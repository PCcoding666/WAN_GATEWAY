"""
Wan Gateway Studio — Gradio front-end.

Design goals (the "harness" view):

* **One form, four tasks.**  Text / Image / Keyframes / Reference share the same
  controls; switching task only shows/hides the media inputs.
* **The model drives the controls.**  Picking a model re-fits resolution, ratio,
  duration range, audio, multi-shot and prompt limits from the registry, so the
  user can never build an invalid request.
* **Nothing is a black box.**  A live *Request preview* shows the exact JSON
  that will be POSTed; a *dry-run* switch sends nothing.
* **Tasks survive refreshes.**  Every submission lands in a local history with
  its task id; any row can be resumed, and a task id can be pasted in by hand.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr

from .config import Config
from .history import HistoryEntry, history
from .models import (
    I2V, KF2V, R2V, T2V, TASK_DESCRIPTIONS, TASK_LABELS, ModelSpec,
    display_name, get_spec, model_id_from_display, models_for_task,
    default_model_for_task,
)
from .prompt_optimizer import optimize_prompt_with_qwen
from .request_builder import GenerationRequest, RequestValidationError, build_payload
from .wan_client import WanAPIError, WanClient

logger = logging.getLogger(__name__)

LABEL_TO_TASK = {v: k for k, v in TASK_LABELS.items()}
HISTORY_HEADERS = ["time", "status", "task", "model", "prompt", "task_id"]

EXAMPLE_PROMPTS = [
    ["A golden retriever puppy runs through autumn leaves in a park, low-angle tracking shot, "
     "warm late-afternoon light, shallow depth of field, joyful barking and rustling leaves."],
    ["Cyberpunk night market in the rain, neon signs reflecting on wet pavement, slow dolly "
     "forward through the crowd, synth soundtrack, cinematic 35mm look."],
    ["一位穿汉服的少女在竹林中缓步前行，微风吹动衣袂，镜头缓慢环绕，晨雾弥漫，古琴配乐。"],
    ["Shot 1 [0-5s]: wide establishing shot of a lighthouse at dawn. Shot 2 [5-10s]: close-up of "
     "waves hitting the rocks. Shot 3 [10-15s]: a seagull takes off into the sunrise."],
]

VIDEO_EXT = (".mp4", ".mov", ".webm", ".mkv", ".avi")
AUDIO_EXT = (".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg")


def _classify_url(url: str) -> str:
    low = url.lower().split("?")[0]
    if low.endswith(VIDEO_EXT):
        return "video"
    if low.endswith(AUDIO_EXT):
        return "audio"
    return "image"


def _fmt_elapsed(seconds: float) -> str:
    seconds = int(seconds)
    return f"{seconds // 60}m {seconds % 60:02d}s" if seconds >= 60 else f"{seconds}s"


class WanStudio:
    """State + handlers behind the Gradio Blocks."""

    def __init__(self) -> None:
        self.history = history()
        self._client: Optional[WanClient] = None
        self.dry_run = Config.DRY_RUN or not Config.DASHSCOPE_API_KEY
        self.show_hidden = Config.SHOW_LEGACY_MODELS or Config.SHOW_DEPRECATED_MODELS

    # ------------------------------------------------------------- helpers
    @property
    def client(self) -> WanClient:
        if self._client is None:
            self._client = WanClient()
        return self._client

    def _model_choices(self, task: str) -> List[str]:
        specs = models_for_task(task, include_hidden=self.show_hidden)
        if self.show_hidden and not Config.SHOW_DEPRECATED_MODELS:
            specs = [s for s in specs if s.status != "deprecated"]
        return [display_name(s) for s in specs]

    def _upload(self, path: Optional[str], what: str) -> Tuple[Optional[str], Optional[str]]:
        """Upload a local image to OSS → (public_url, warning)."""
        if not path:
            return None, None
        from .oss_service import oss_service  # lazy: oss2 import is slow
        url, info = oss_service.upload_image(path)
        if not url:
            return None, f"Failed to upload {what}."
        warn = None
        if (info or {}).get("source") == "demo":
            warn = (f"⚠️ OSS is not configured, so the {what} was replaced by a demo image. "
                    "Set OSS_* in .env to use your own images.")
        return url, warn

    # ---------------------------------------------------- request assembly
    def _assemble(self, task_label, model_label, prompt, negative_prompt,
                  first_frame, last_frame, ref_files, ref_urls,
                  resolution, ratio, duration, smart_duration, audio, audio_url,
                  shot_type, prompt_extend, seed, watermark, upload: bool
                  ) -> Tuple[Optional[GenerationRequest], List[str]]:
        """Turn raw widget values into a GenerationRequest (+ warnings)."""
        warnings: List[str] = []
        task = LABEL_TO_TASK.get(task_label, task_label)
        model = model_id_from_display(model_label)
        spec = get_spec(model)

        first_url = last_url = None
        ref_imgs: List[str] = []
        ref_vids: List[str] = []
        ref_auds: List[str] = []

        if task in (I2V, KF2V):
            if upload:
                first_url, w = self._upload(first_frame, "first frame")
                if w:
                    warnings.append(w)
            else:
                first_url = "<first_frame_upload>" if first_frame else None
        if task == KF2V:
            if upload:
                last_url, w = self._upload(last_frame, "last frame")
                if w:
                    warnings.append(w)
            else:
                last_url = "<last_frame_upload>" if last_frame else None
        if task == R2V:
            for f in ref_files or []:
                p = f if isinstance(f, str) else getattr(f, "name", None)
                if not p:
                    continue
                kind = _classify_url(p)
                if kind != "image":
                    warnings.append(f"⚠️ {os.path.basename(p)}: upload of {kind} files is not "
                                    "supported yet — paste a public URL instead.")
                    continue
                if upload:
                    u, w = self._upload(p, os.path.basename(p))
                    if w:
                        warnings.append(w)
                    if u:
                        ref_imgs.append(u)
                else:
                    ref_imgs.append(f"<upload:{os.path.basename(p)}>")
            for line in (ref_urls or "").splitlines():
                u = line.strip()
                if not u:
                    continue
                {"image": ref_imgs, "video": ref_vids, "audio": ref_auds}[_classify_url(u)].append(u)

        seed_val: Optional[int] = None
        if seed not in (None, ""):
            try:
                seed_val = int(float(seed))
            except (TypeError, ValueError):
                warnings.append("⚠️ Seed ignored: not a number.")

        req = GenerationRequest(
            model=model, task=task, prompt=prompt or "",
            negative_prompt=negative_prompt or None,
            resolution=resolution or None,
            ratio=ratio if ratio in spec.ratios else None,
            duration=-1 if (smart_duration and spec.smart_duration) else (int(duration) if duration is not None else None),
            audio=bool(audio) if spec.audio else None,
            audio_url=(audio_url or None) if spec.audio_url else None,
            shot_type=shot_type if (spec.shot_type and shot_type) else None,
            prompt_extend=bool(prompt_extend),
            seed=seed_val,
            watermark=bool(watermark) if spec.watermark else None,
            first_frame_url=first_url, last_frame_url=last_url,
            reference_image_urls=ref_imgs, reference_video_urls=ref_vids,
            reference_audio_urls=ref_auds,
        )
        return req, warnings

    # ------------------------------------------------------------ handlers
    def preview(self, *args) -> Tuple[Dict[str, Any], str]:
        try:
            req, warnings = self._assemble(*args, upload=False)
            payload = build_payload(req)
            msg = "🔍 Preview only — nothing sent." + ("\n" + "\n".join(warnings) if warnings else "")
            return payload, msg
        except (RequestValidationError, ValueError) as exc:
            return {}, f"❌ {exc}"

    def submit(self, *args):
        """Upload media, POST the task, start the poller."""
        try:
            req, warnings = self._assemble(*args, upload=True)
            payload = build_payload(req)
        except (RequestValidationError, ValueError) as exc:
            return "", f"❌ {exc}", gr.Timer(active=False), {}, self.history.as_rows()

        if self.dry_run:
            why = "WAN_DRY_RUN=1" if Config.DRY_RUN else "DASHSCOPE_API_KEY is not set"
            return ("", f"🧪 Dry run ({why}) — request shown below was **not** sent.",
                    gr.Timer(active=False), payload, self.history.as_rows())

        try:
            task_id = self.client.submit(payload, task=req.task)
        except WanAPIError as exc:
            hint = ""
            if "InvalidApiKey" in str(exc) or "401" in str(exc):
                hint = "\nCheck DASHSCOPE_API_KEY and DASHSCOPE_REGION (cn vs intl)."
            return "", f"❌ Submit failed: {exc}{hint}", gr.Timer(active=False), payload, self.history.as_rows()
        except Exception as exc:  # network etc.
            return "", f"❌ Submit failed: {exc}", gr.Timer(active=False), payload, self.history.as_rows()

        self.history.add(HistoryEntry(task_id=task_id, model=req.model, task=req.task,
                                      prompt=req.prompt or "", payload=payload))
        spec = get_spec(req.model)
        msg = (f"🚀 Task **{task_id}** submitted to `{spec.id}`.\n"
               f"⏳ Typical wait: {spec.eta}. Polling every 5 s…")
        if warnings:
            msg += "\n" + "\n".join(warnings)
        return task_id, msg, gr.Timer(active=True), payload, self.history.as_rows()

    def poll(self, task_id: str):
        """Timer tick → (video, status, timer, history rows)."""
        if not task_id:
            return None, "No active task.", gr.Timer(active=False), self.history.as_rows()
        entry = self.history.get(task_id)
        started = entry.created_at if entry else time.time()
        st = self.client.status(task_id)
        elapsed = time.time() - started

        if st.status in ("PENDING", "RUNNING"):
            self.history.update(task_id, status=st.status)
            bar = "▰" * min(20, int(elapsed // 15)) + "▱" * max(0, 20 - int(elapsed // 15))
            msg = (f"⏳ **{st.status}** · {_fmt_elapsed(elapsed)}\n`{bar}`\n"
                   f"Task `{task_id}` — you can close this tab; resume later from History.")
            return None, msg, gr.Timer(active=True), self.history.as_rows()

        if st.status == "SUCCEEDED" and st.video_url:
            local = self.client.download(st.video_url, task_id)
            self.history.update(task_id, status="SUCCEEDED", finished_at=time.time(),
                                video_url=st.video_url, local_path=local)
            usage = st.usage
            extra = ""
            if usage:
                extra = "\n" + " · ".join(f"{k}: {v}" for k, v in usage.items())
            msg = (f"✅ Done in {_fmt_elapsed(elapsed)} · task `{task_id}`\n"
                   f"{'💾 saved to ' + local if local else '🔗 streaming from URL (expires in 24 h)'}"
                   f"{extra}")
            return (local or st.video_url), msg, gr.Timer(active=False), self.history.as_rows()

        if st.status in ("FAILED", "CANCELED") or (st.status == "SUCCEEDED" and not st.video_url):
            err = st.error_message or "no video URL returned"
            self.history.update(task_id, status=st.status, finished_at=time.time(), error=err)
            return None, f"❌ {st.status}: {err}", gr.Timer(active=False), self.history.as_rows()

        # ERROR / UNKNOWN → keep polling, transient
        return None, f"⚠️ {st.error_message or st.status} — retrying…", gr.Timer(active=True), self.history.as_rows()

    def resume(self, task_id: str):
        task_id = (task_id or "").strip()
        if not task_id:
            return "", "Paste a task id first.", gr.Timer(active=False)
        if not self.history.get(task_id):
            self.history.add(HistoryEntry(task_id=task_id, model="?", task="?", prompt="(resumed)"))
        return task_id, f"🔁 Resuming task `{task_id}`…", gr.Timer(active=True)

    def cancel(self, task_id: str):
        if not task_id:
            return "Nothing to cancel.", gr.Timer(active=False)
        ok = self.client.cancel(task_id)
        if ok:
            self.history.update(task_id, status="CANCELED", finished_at=time.time())
            return f"⛔ Task `{task_id}` cancelled.", gr.Timer(active=False)
        return "⚠️ Could not cancel (only queued tasks can be cancelled).", gr.Timer(active=True)

    def on_history_select(self, evt: gr.SelectData, rows):
        try:
            row = rows.iloc[evt.index[0]] if hasattr(rows, "iloc") else rows[evt.index[0]]
            return str(row[5] if not hasattr(row, "iloc") else row.iloc[5])
        except Exception:
            return ""

    # ----------------------------------------------------- dynamic layout
    def on_task_change(self, task_label: str):
        task = LABEL_TO_TASK.get(task_label, T2V)
        choices = self._model_choices(task)
        default = default_model_for_task(task)
        value = next((c for c in choices if model_id_from_display(c) == default), choices[0] if choices else None)
        return (
            gr.update(choices=choices, value=value),
            gr.update(visible=task in (I2V, KF2V)),
            gr.update(visible=task == KF2V),
            gr.update(visible=task == R2V),
            gr.update(visible=task == R2V),
            TASK_DESCRIPTIONS[task],
            *self._fit_controls(value, task),
        )

    def on_model_change(self, model_label: str, task_label: str):
        task = LABEL_TO_TASK.get(task_label, T2V)
        return self._fit_controls(model_label, task)

    def _fit_controls(self, model_label: Optional[str], task: str):
        """Re-fit every control to the selected model's spec."""
        if not model_label:
            return (gr.update(),) * 8
        spec = get_spec(model_id_from_display(model_label))
        ratios = list(spec.ratios)
        ratio_default = "16:9" if "16:9" in ratios else ratios[0]
        if task in (I2V, KF2V) and "adaptive" in ratios:
            ratio_default = "adaptive"
        fixed = spec.duration_min == spec.duration_max
        return (
            gr.update(choices=list(spec.resolutions), value=spec.default_resolution),
            gr.update(choices=ratios, value=ratio_default,
                      visible=spec.dialect in ("media", "size", "r2v")),
            gr.update(minimum=spec.duration_min, maximum=spec.duration_max,
                      step=spec.duration_step, value=spec.default_duration,
                      interactive=not fixed,
                      label=f"⏱️ Duration (s) — {spec.duration_label}"),
            gr.update(visible=spec.smart_duration, value=False),
            gr.update(visible=spec.audio, value=True),
            gr.update(visible=spec.audio_url),
            gr.update(visible=spec.shot_type, value="single"),
            self._model_card(spec),
        )

    @staticmethod
    def _model_card(spec: ModelSpec) -> str:
        lines = [f"**{spec.badge} {spec.id}** · Wan {spec.family} · {spec.status}",
                 spec.description,
                 f"Resolutions: {' / '.join(spec.resolutions)} · {spec.fps} fps · "
                 f"{spec.duration_label} · prompt ≤ {spec.max_prompt} chars · ETA {spec.eta}"]
        lines += [f"ℹ️ {n}" for n in spec.notes]
        return "\n\n".join(lines)

    # --------------------------------------------------------------- UI
    def create_interface(self) -> gr.Blocks:
        banner = []
        if self.dry_run:
            banner.append("🧪 **Dry-run mode** — requests are previewed, not sent "
                          f"({'WAN_DRY_RUN=1' if Config.DRY_RUN else 'no DASHSCOPE_API_KEY'}).")
        if not Config.OSS_ENABLE:
            banner.append("⚠️ OSS not configured: uploaded images fall back to a demo picture. "
                          "Set OSS_ACCESS_KEY_ID / OSS_ACCESS_KEY_SECRET / OSS_BUCKET_NAME.")
        banner.append(f"🌐 Region `{Config.DASHSCOPE_REGION}` → `{Config.DASHSCOPE_BASE_URL}`")

        default_task_label = TASK_LABELS[T2V]
        init_choices = self._model_choices(T2V)
        init_model = next((c for c in init_choices if model_id_from_display(c) == default_model_for_task(T2V)),
                          init_choices[0])
        init_spec = get_spec(model_id_from_display(init_model))

        with gr.Blocks(title="Wan Gateway Studio", analytics_enabled=False, **self._blocks_kwargs()) as ui:
            gr.Markdown("# 🎬 Wan Gateway Studio\n"
                        "Text · Image · Keyframes · Reference → video on **Wan 3.0 / 2.7 / 2.6** "
                        "(Alibaba Cloud Model Studio).")
            gr.Markdown("\n\n".join(banner), elem_classes=["small-note"])

            with gr.Row(equal_height=False):
                # ============================ LEFT: inputs
                with gr.Column(scale=5):
                    task_radio = gr.Radio(list(TASK_LABELS.values()), value=default_task_label,
                                          label="Task")
                    task_desc = gr.Markdown(TASK_DESCRIPTIONS[T2V], elem_classes=["small-note"])

                    model_dd = gr.Dropdown(init_choices, value=init_model, label="Model",
                                           info="🆕 latest · ✅ stable · 🕰️ legacy")
                    model_card = gr.Markdown(self._model_card(init_spec), elem_classes=["small-note"])

                    with gr.Row():
                        prompt_tb = gr.Textbox(label="Prompt", lines=4, scale=5,
                                               placeholder="Describe subject, action, camera, light, "
                                                           "mood, sound. Multi-shot: 'Shot 1 [0-5s]: …'")
                        optimize_btn = gr.Button("✨ Enhance", scale=1, variant="secondary")
                    gr.Examples(EXAMPLE_PROMPTS, inputs=[prompt_tb], label="Prompt ideas")

                    with gr.Row(visible=False) as frames_row:
                        first_frame = gr.Image(label="First frame", type="filepath", height=220)
                        last_frame = gr.Image(label="Last frame", type="filepath", height=220, visible=False)
                    ref_files = gr.File(label="Reference images", file_count="multiple",
                                        file_types=["image"], visible=False)
                    ref_urls = gr.Textbox(label="Reference URLs (one per line: image / video / audio)",
                                          lines=3, visible=False,
                                          placeholder="https://…/character.png\nhttps://…/clip.mp4\nhttps://…/voice.mp3")

                    with gr.Group():
                        with gr.Row():
                            resolution_dd = gr.Dropdown(list(init_spec.resolutions),
                                                        value=init_spec.default_resolution, label="Resolution")
                            ratio_dd = gr.Dropdown(list(init_spec.ratios), value="16:9", label="Aspect ratio")
                        with gr.Row():
                            duration_sl = gr.Slider(init_spec.duration_min, init_spec.duration_max,
                                                    value=init_spec.default_duration, step=init_spec.duration_step,
                                                    label=f"⏱️ Duration (s) — {init_spec.duration_label}", scale=3)
                            smart_cb = gr.Checkbox(label="Smart duration (-1)", value=False,
                                                   visible=init_spec.smart_duration, scale=1)
                        with gr.Row():
                            audio_cb = gr.Checkbox(label="🎵 Generate audio", value=True, visible=init_spec.audio)
                            shot_radio = gr.Radio(["single", "multi"], value="single", label="Shots",
                                                  visible=init_spec.shot_type)
                        audio_url_tb = gr.Textbox(label="🎧 Custom audio / voice URL (optional)",
                                                  visible=init_spec.audio_url,
                                                  placeholder="https://…/track.mp3")

                    with gr.Accordion("⚙️ Advanced", open=False):
                        negative_tb = gr.Textbox(label="Negative prompt", lines=2)
                        with gr.Row():
                            seed_tb = gr.Textbox(label="Seed", placeholder="random")
                            prompt_extend_cb = gr.Checkbox(label="Prompt rewrite (prompt_extend)", value=True)
                            watermark_cb = gr.Checkbox(label="Watermark", value=False)

                    with gr.Row():
                        generate_btn = gr.Button("🎬 Generate", variant="primary", scale=3)
                        preview_btn = gr.Button("🔍 Preview request", scale=1)
                        cancel_btn = gr.Button("⛔ Cancel", variant="stop", scale=1)

                # ============================ RIGHT: outputs
                with gr.Column(scale=5):
                    status_md = gr.Markdown("Ready.")
                    video_out = gr.Video(label="Result", height=360)
                    with gr.Accordion("📦 Request payload (exactly what is sent)", open=False):
                        payload_json = gr.JSON()
                    with gr.Accordion("🕘 History & resume", open=True):
                        with gr.Row():
                            resume_tb = gr.Textbox(label="Task id", scale=4,
                                                   placeholder="click a row below or paste a DashScope task id")
                            resume_btn = gr.Button("🔁 Resume", scale=1)
                        history_df = gr.Dataframe(value=self.history.as_rows(), headers=HISTORY_HEADERS,
                                                  interactive=False, wrap=True, row_count=(5, "dynamic"))

            task_state = gr.State("")
            timer = gr.Timer(5, active=False)

            form_inputs = [task_radio, model_dd, prompt_tb, negative_tb, first_frame, last_frame,
                           ref_files, ref_urls, resolution_dd, ratio_dd, duration_sl, smart_cb,
                           audio_cb, audio_url_tb, shot_radio, prompt_extend_cb, seed_tb, watermark_cb]
            fit_outputs = [resolution_dd, ratio_dd, duration_sl, smart_cb, audio_cb, audio_url_tb,
                           shot_radio, model_card]

            task_radio.change(self.on_task_change, [task_radio],
                              [model_dd, frames_row, last_frame, ref_files, ref_urls, task_desc, *fit_outputs])
            model_dd.change(self.on_model_change, [model_dd, task_radio], fit_outputs)

            preview_btn.click(self.preview, form_inputs, [payload_json, status_md])
            generate_btn.click(self.submit, form_inputs,
                               [task_state, status_md, timer, payload_json, history_df])
            timer.tick(self.poll, [task_state], [video_out, status_md, timer, history_df])
            resume_btn.click(self.resume, [resume_tb], [task_state, status_md, timer])
            cancel_btn.click(self.cancel, [task_state], [status_md, timer])
            history_df.select(self.on_history_select, [history_df], [resume_tb])
            optimize_btn.click(optimize_prompt_with_qwen, [prompt_tb], [prompt_tb])

            with gr.Accordion("ℹ️ Help", open=False):
                gr.Markdown(
                    "**Which model?** `wan3.0-video` does everything (2–30 s, smart duration, adaptive "
                    "ratio). Use `wan2.7-*` for 2–15 s clips with strong audio sync, `wan2.6-*-flash` "
                    "when speed matters, `wan2.6-t2v` for explicit multi-shot storyboards.\n\n"
                    "**Images:** JPEG/PNG/BMP/WEBP, ≤10 MB, 360–2000 px per side. Images are uploaded to "
                    "your OSS bucket and passed as signed URLs.\n\n"
                    "**Billing:** price = per-second rate (by resolution) × duration. Smart duration "
                    "lets the model pick the length, so the cost is only known after the run.\n\n"
                    "**Resume:** task ids and result URLs stay valid for 24 h. Downloaded files live in "
                    f"`{Config.VIDEO_DIR}`.\n\n"
                    "**CLI:** `python cli.py models`, `python cli.py generate --model wan3.0-video "
                    "--prompt '…' --dry-run`, `python cli.py status <task_id>`."
                )
        return ui

    # Gradio 6 moved theme/css from Blocks() to launch(); support both majors.
    _THEME_KW = dict(css=".small-note{font-size:0.85em;opacity:.8}")

    @staticmethod
    def _gradio_major() -> int:
        try:
            return int(gr.__version__.split(".")[0])
        except Exception:  # pragma: no cover
            return 5

    def _blocks_kwargs(self) -> Dict[str, Any]:
        if self._gradio_major() >= 6:
            return {}
        return {"theme": gr.themes.Soft(), **self._THEME_KW}

    def _launch_kwargs(self) -> Dict[str, Any]:
        if self._gradio_major() >= 6:
            return {"theme": gr.themes.Soft(), **self._THEME_KW}
        return {}

    def launch(self, server_name="127.0.0.1", server_port=7860, share=False, debug=False) -> None:
        ui = self.create_interface()
        logger.info("Launching Wan Gateway Studio on %s:%s", server_name, server_port)
        common = dict(server_name=server_name, server_port=server_port, debug=debug,
                      show_error=True, quiet=True, **self._launch_kwargs())
        try:
            ui.launch(share=share, **common)
        except Exception as exc:
            if "localhost is not accessible" in str(exc) or "shareable link" in str(exc):
                ui.launch(share=True, **common)
            else:
                raise


# ----------------------------------------------------------- compat shims
EnhancedGradioVideoApp = WanStudio


def create_app() -> WanStudio:
    return WanStudio()


def create_interface() -> gr.Blocks:
    return create_app().create_interface()


class GradioTextToVideoApp:
    """Legacy class kept for old imports."""

    def __init__(self):
        self.app = WanStudio()
        logger.warning("GradioTextToVideoApp is deprecated. Use WanStudio instead.")

    def create_interface(self):
        return self.app.create_interface()

    def launch(self, **kwargs):
        return self.app.launch(**kwargs)
