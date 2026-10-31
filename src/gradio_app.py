"""
Wan Gateway Studio — Gradio front-end for Alibaba Cloud Model Studio AIGC.

Three tabs, one philosophy:

* **🎬 Video** — text / image / keyframes / reference / edit → video (Wan 3.0 / 2.7 / 2.6).
* **🖼️ Image** — text → image and instruction / reference editing (Wan 2.7 Image, Qwen-Image 3.0).
* **🔊 Speech** — text → speech (Qwen3-TTS, CosyVoice 3.x).

Design goals (the "harness" view):

* **The model drives the controls.**  Picking a model re-fits resolution, ratio,
  duration range, sizes, voices, audio, multi-shot and prompt limits from the
  registries, so the user can never build an invalid request.
* **Nothing is a black box.**  A *Request preview* shows the exact JSON that will
  be POSTed; a *dry-run* switch sends nothing.
* **Tasks survive refreshes.**  Every submission lands in a local history with
  its task id; any row can be resumed, and a task id can be pasted in by hand.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr

from .catalog import (
    IMAGE_TASK_EDIT, IMAGE_TASK_LABELS, IMAGE_TASK_T2I, DEFAULT_IMAGE_MODEL,
    DEFAULT_SPEECH_MODEL, ImageModelSpec, SpeechModelSpec, get_image_spec, get_speech_spec,
    id_from_display, image_display_name, image_models_for_task, speech_display_name,
    speech_models,
)
from .config import Config
from .history import HistoryEntry, history
from .media_builder import (
    ImageRequest, MediaValidationError, SpeechRequest, build_image_payload,
    build_speech_payload, extract_audio_url, extract_image_urls,
)
from .models import (
    I2V, KF2V, R2V, T2V, VEDIT, TASK_DESCRIPTIONS, TASK_LABELS, ModelSpec,
    default_model_for_task, display_name, get_spec, model_id_from_display, models_for_task,
)
from .prompt_optimizer import optimize_prompt_with_qwen
from .request_builder import GenerationRequest, RequestValidationError, build_payload
from .wan_client import WanAPIError, WanClient

logger = logging.getLogger(__name__)

LABEL_TO_TASK = {v: k for k, v in TASK_LABELS.items()}
IMAGE_LABEL_TO_TASK = {v: k for k, v in IMAGE_TASK_LABELS.items()}
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
IMAGE_EXAMPLES = [
    ["Product shot of a matte black ceramic coffee mug on a walnut table, soft window light, "
     "shallow depth of field, 85mm, photorealistic."],
    ["海报：'秋日音乐节 10.24' 大字标题，复古胶片质感，枫叶与吉他剪影，暖橙配色。"],
    ["Isometric illustration of a tiny solar-punk city on a floating island, pastel palette, clean vector style."],
]
SPEECH_EXAMPLES = [
    ["欢迎使用 Wan Gateway Studio，这是一段由千问语音合成的示例。"],
    ["Welcome to Wan Gateway Studio. This sample was synthesized by Qwen3-TTS."],
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


def _lines(text: Optional[str]) -> List[str]:
    return [l.strip() for l in (text or "").splitlines() if l.strip()]


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

    def _filter_hidden(self, specs):
        if self.show_hidden and not Config.SHOW_DEPRECATED_MODELS:
            return [s for s in specs if s.status != "deprecated"]
        return specs

    def _model_choices(self, task: str) -> List[str]:
        return [display_name(s) for s in self._filter_hidden(models_for_task(task, include_hidden=self.show_hidden))]

    def _image_choices(self, task: str) -> List[str]:
        return [image_display_name(s) for s in self._filter_hidden(image_models_for_task(task, include_hidden=self.show_hidden))]

    def _speech_choices(self) -> List[str]:
        return [speech_display_name(s) for s in self._filter_hidden(speech_models(include_hidden=self.show_hidden))]

    @staticmethod
    def _pick(choices: List[str], wanted_id: str, to_id) -> Optional[str]:
        return next((c for c in choices if to_id(c) == wanted_id), choices[0] if choices else None)

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

    def _upload_many(self, files, upload: bool, warnings: List[str]) -> List[str]:
        urls: List[str] = []
        for f in files or []:
            p = f if isinstance(f, str) else getattr(f, "name", None)
            if not p:
                continue
            if _classify_url(p) != "image":
                warnings.append(f"⚠️ {os.path.basename(p)}: only images can be uploaded — paste a public URL for "
                                "video / audio.")
                continue
            if upload:
                u, w = self._upload(p, os.path.basename(p))
                if w:
                    warnings.append(w)
                if u:
                    urls.append(u)
            else:
                urls.append(f"<upload:{os.path.basename(p)}>")
        return urls

    @staticmethod
    def _seed(seed) -> Tuple[Optional[int], Optional[str]]:
        if seed in (None, ""):
            return None, None
        try:
            return int(float(seed)), None
        except (TypeError, ValueError):
            return None, "⚠️ Seed ignored: not a number."

    def _dry_run_msg(self, payload_desc: str = "request") -> str:
        why = "WAN_DRY_RUN=1" if Config.DRY_RUN else "DASHSCOPE_API_KEY is not set"
        return f"🧪 Dry run ({why}) — the {payload_desc} shown below was **not** sent."

    # =================================================================== VIDEO
    def _assemble(self, task_label, model_label, prompt, negative_prompt,
                  first_frame, last_frame, ref_files, ref_urls, video_url,
                  resolution, ratio, duration, smart_duration, audio, audio_url,
                  shot_type, prompt_extend, seed, watermark, upload: bool
                  ) -> Tuple[Optional[GenerationRequest], List[str]]:
        warnings: List[str] = []
        task = LABEL_TO_TASK.get(task_label, task_label)
        model = model_id_from_display(model_label)
        spec = get_spec(model)

        first_url = last_url = None
        ref_imgs: List[str] = []
        ref_vids: List[str] = []
        ref_auds: List[str] = []
        input_video = (video_url or "").strip() or None

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
        if task in (R2V, VEDIT):
            ref_imgs.extend(self._upload_many(ref_files, upload, warnings))
            for u in _lines(ref_urls):
                kind = _classify_url(u)
                if kind == "video" and task == VEDIT and not input_video:
                    input_video = u
                else:
                    {"image": ref_imgs, "video": ref_vids, "audio": ref_auds}[kind].append(u)

        seed_val, w = self._seed(seed)
        if w:
            warnings.append(w)

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
            reference_audio_urls=ref_auds, input_video_url=input_video,
        )
        return req, warnings

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
            return "", self._dry_run_msg(), gr.Timer(active=False), payload, self.history.as_rows()

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
            extra = ("\n" + " · ".join(f"{k}: {v}" for k, v in usage.items())) if usage else ""
            msg = (f"✅ Done in {_fmt_elapsed(elapsed)} · task `{task_id}`\n"
                   f"{'💾 saved to ' + local if local else '🔗 streaming from URL (expires in 24 h)'}{extra}")
            return (local or st.video_url), msg, gr.Timer(active=False), self.history.as_rows()

        if st.status in ("FAILED", "CANCELED") or (st.status == "SUCCEEDED" and not st.video_url):
            err = st.error_message or "no video URL returned"
            self.history.update(task_id, status=st.status, finished_at=time.time(), error=err)
            return None, f"❌ {st.status}: {err}", gr.Timer(active=False), self.history.as_rows()

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
        if self.client.cancel(task_id):
            self.history.update(task_id, status="CANCELED", finished_at=time.time())
            return f"⛔ Task `{task_id}` cancelled.", gr.Timer(active=False)
        return "⚠️ Could not cancel (only queued tasks can be cancelled).", gr.Timer(active=True)

    def on_history_select(self, evt: gr.SelectData, rows):
        try:
            row = rows.iloc[evt.index[0]] if hasattr(rows, "iloc") else rows[evt.index[0]]
            return str(row.iloc[5] if hasattr(row, "iloc") else row[5])
        except Exception:
            return ""

    def on_task_change(self, task_label: str):
        task = LABEL_TO_TASK.get(task_label, T2V)
        choices = self._model_choices(task)
        value = self._pick(choices, default_model_for_task(task), model_id_from_display)
        return (
            gr.update(choices=choices, value=value),
            gr.update(visible=task in (I2V, KF2V)),
            gr.update(visible=task == KF2V),
            gr.update(visible=task in (R2V, VEDIT), label="Reference images" if task == R2V else "Reference images (optional)"),
            gr.update(visible=task in (R2V, VEDIT)),
            gr.update(visible=task == VEDIT),
            TASK_DESCRIPTIONS[task],
            *self._fit_controls(value, task),
        )

    def on_model_change(self, model_label: str, task_label: str):
        return self._fit_controls(model_label, LABEL_TO_TASK.get(task_label, T2V))

    def _fit_controls(self, model_label: Optional[str], task: str):
        if not model_label:
            return (gr.update(),) * 8
        spec = get_spec(model_id_from_display(model_label))
        ratios = list(spec.ratios)
        ratio_default = "16:9" if "16:9" in ratios else ratios[0]
        if task in (I2V, KF2V, VEDIT) and "adaptive" in ratios:
            ratio_default = "adaptive"
        fixed = spec.duration_min == spec.duration_max
        return (
            gr.update(choices=list(spec.resolutions), value=spec.default_resolution),
            gr.update(choices=ratios, value=ratio_default, visible=spec.dialect in ("media", "size", "r2v")),
            gr.update(minimum=spec.duration_min, maximum=spec.duration_max, step=spec.duration_step,
                      value=spec.default_duration, interactive=not fixed,
                      label=f"⏱️ Duration (s) — {spec.duration_label}"),
            gr.update(visible=spec.smart_duration, value=False),
            gr.update(visible=spec.audio, value=True),
            gr.update(visible=spec.audio_url),
            gr.update(visible=spec.shot_type, value="single"),
            self._model_card(spec),
        )

    @staticmethod
    def _model_card(spec: ModelSpec) -> str:
        lines = [f"**{spec.badge} {spec.id}** · Wan {spec.family} · {spec.status}", spec.description,
                 f"Resolutions: {' / '.join(spec.resolutions)} · {spec.fps} fps · {spec.duration_label} · "
                 f"prompt ≤ {spec.max_prompt} chars · ETA {spec.eta}"]
        lines += [f"ℹ️ {n}" for n in spec.notes]
        return "\n\n".join(lines)

    # =================================================================== IMAGE
    def _assemble_image(self, task_label, model_label, prompt, negative, files, urls, size, n,
                        seed, prompt_extend, watermark, upload: bool) -> Tuple[ImageRequest, List[str]]:
        warnings: List[str] = []
        task = IMAGE_LABEL_TO_TASK.get(task_label, task_label)
        model = id_from_display(model_label)
        images = self._upload_many(files, upload, warnings) + [u for u in _lines(urls) if _classify_url(u) == "image"]
        seed_val, w = self._seed(seed)
        if w:
            warnings.append(w)
        size = (size or "").strip()
        if size.lower() in ("", "(auto)", "auto"):
            size = None
        req = ImageRequest(model=model, task=task, prompt=prompt or "", negative_prompt=negative or None,
                           size=size, n=int(n or 1), seed=seed_val,
                           prompt_extend=bool(prompt_extend), watermark=bool(watermark), image_urls=images)
        return req, warnings

    def image_preview(self, *args):
        try:
            req, warnings = self._assemble_image(*args, upload=False)
            path, body, is_async = build_image_payload(req)
            msg = f"🔍 Preview only — nothing sent. `POST {path}` ({'async' if is_async else 'sync'})"
            if warnings:
                msg += "\n" + "\n".join(warnings)
            return body, msg
        except (MediaValidationError, ValueError) as exc:
            return {}, f"❌ {exc}"

    def image_generate(self, *args, progress=gr.Progress()):
        try:
            req, warnings = self._assemble_image(*args, upload=True)
            path, body, is_async = build_image_payload(req)
        except (MediaValidationError, ValueError) as exc:
            return [], f"❌ {exc}", {}
        if self.dry_run:
            return [], self._dry_run_msg(), body
        started = time.time()
        try:
            if is_async:
                task_id = self.client.submit_async(path, body)
                progress(0.1, desc=f"task {task_id} queued")
                st = self.client.wait(task_id, interval=3, max_wait=600,
                                      on_tick=lambda s, t: progress(min(0.9, 0.1 + t / 120), desc=f"{s.status} · {_fmt_elapsed(t)}"))
                if st.status != "SUCCEEDED":
                    return [], f"❌ {st.status}: {st.error_message or 'no result'}", body
                urls = extract_image_urls(st.raw)
                tid = task_id
            else:
                progress(0.3, desc="generating…")
                resp = self.client.call_sync(path, body)
                urls = extract_image_urls(resp)
                tid = (resp.get("request_id") or f"img-{int(started)}")
        except WanAPIError as exc:
            return [], f"❌ {exc}", body
        except Exception as exc:
            return [], f"❌ {exc}", body
        if not urls:
            return [], "❌ No image URL in the response.", body
        files: List[str] = []
        for i, u in enumerate(urls):
            local = self.client.download_file(u, f"{tid}_{i}", Config.IMAGE_DIR, ".png")
            files.append(local or u)
        self.history.add(HistoryEntry(task_id=str(tid), model=req.model, task=f"image/{req.task}",
                                      prompt=req.prompt, status="SUCCEEDED", finished_at=time.time(),
                                      video_url=urls[0], local_path=files[0], payload=body))
        msg = (f"✅ {len(urls)} image(s) in {_fmt_elapsed(time.time() - started)} · `{req.model}`\n"
               f"💾 saved under `{Config.IMAGE_DIR}` (URLs expire in 24 h)")
        if warnings:
            msg += "\n" + "\n".join(warnings)
        return files, msg, body

    def on_image_task_change(self, task_label: str):
        task = IMAGE_LABEL_TO_TASK.get(task_label, IMAGE_TASK_T2I)
        choices = self._image_choices(task)
        value = self._pick(choices, DEFAULT_IMAGE_MODEL[task], id_from_display)
        return (gr.update(choices=choices, value=value),
                gr.update(visible=task == IMAGE_TASK_EDIT or True),
                *self._fit_image_controls(value))

    def on_image_model_change(self, model_label: str):
        return self._fit_image_controls(model_label)

    def _fit_image_controls(self, model_label: Optional[str]):
        if not model_label:
            return (gr.update(),) * 4
        spec = get_image_spec(id_from_display(model_label))
        sizes = ["(auto)"] + list(spec.sizes) if spec.default_size is None else list(spec.sizes)
        return (
            gr.update(choices=sizes, value=spec.default_size or "(auto)"),
            gr.update(maximum=spec.max_n, value=1, interactive=spec.max_n > 1,
                      label=f"Images per call (≤{spec.max_n})"),
            gr.update(visible=spec.max_input_images > 0,
                      label=f"Input images (≤{spec.max_input_images}) — required for editing"),
            self._image_card(spec),
        )

    @staticmethod
    def _image_card(spec: ImageModelSpec) -> str:
        lines = [f"**{spec.badge} {spec.id}** · {spec.vendor} {spec.family} · {spec.status}", spec.description,
                 f"Sizes: {', '.join(spec.sizes)} · n ≤ {spec.max_n} · input images ≤ {spec.max_input_images} · "
                 f"prompt ≤ {spec.max_prompt} · ETA {spec.eta}"]
        lines += [f"ℹ️ {n}" for n in spec.notes]
        return "\n\n".join(lines)

    # ================================================================== SPEECH
    def _assemble_speech(self, model_label, text, voice, language, instructions, fmt, sample_rate, rate) -> SpeechRequest:
        spec = get_speech_spec(id_from_display(model_label))
        return SpeechRequest(
            model=spec.id, text=text or "", voice=(voice or "").strip() or None,
            language=(language or None) if spec.dialect == "tts_mm" else None,
            instructions=(instructions or "").strip() or None,
            format=(fmt or None), sample_rate=int(sample_rate) if sample_rate else None,
            rate=float(rate) if (rate is not None and spec.dialect == "tts_cosy" and float(rate) != 1.0) else None,
        )

    def speech_preview(self, *args):
        try:
            path, body, _ = build_speech_payload(self._assemble_speech(*args))
            return body, f"🔍 Preview only — nothing sent. `POST {path}`"
        except (MediaValidationError, ValueError) as exc:
            return {}, f"❌ {exc}"

    def speech_generate(self, *args):
        try:
            req = self._assemble_speech(*args)
            path, body, _ = build_speech_payload(req)
        except (MediaValidationError, ValueError) as exc:
            return None, f"❌ {exc}", {}
        if self.dry_run:
            return None, self._dry_run_msg(), body
        started = time.time()
        try:
            resp = self.client.call_sync(path, body)
        except WanAPIError as exc:
            return None, f"❌ {exc}", body
        except Exception as exc:
            return None, f"❌ {exc}", body
        url = extract_audio_url(resp)
        if not url:
            return None, f"❌ No audio URL in the response: {str(resp)[:300]}", body
        tid = resp.get("request_id") or f"tts-{int(started)}"
        local = self.client.download_file(url, str(tid), Config.AUDIO_DIR, "." + (req.format or "wav"))
        self.history.add(HistoryEntry(task_id=str(tid), model=req.model, task="tts", prompt=req.text,
                                      status="SUCCEEDED", finished_at=time.time(), video_url=url,
                                      local_path=local, payload=body))
        return (local or url), (f"✅ Synthesized in {_fmt_elapsed(time.time() - started)} · `{req.model}`\n"
                                f"{'💾 ' + local if local else '🔗 ' + url}"), body

    def on_speech_model_change(self, model_label: str):
        spec = get_speech_spec(id_from_display(model_label))
        return (
            gr.update(choices=list(spec.voices), value=spec.default_voice),
            gr.update(choices=list(spec.languages), value=spec.languages[0], visible=spec.dialect == "tts_mm"),
            gr.update(visible=spec.instruct),
            gr.update(choices=list(spec.formats), value=spec.formats[0]),
            gr.update(choices=[str(r) for r in spec.sample_rates], value=str(spec.sample_rates[0]),
                      visible=spec.dialect == "tts_cosy"),
            gr.update(visible=spec.dialect == "tts_cosy", value=1.0),
            self._speech_card(spec),
        )

    @staticmethod
    def _speech_card(spec: SpeechModelSpec) -> str:
        caps = [c for c, on in (("instruction control", spec.instruct), ("voice cloning", spec.clone)) if on]
        return (f"**{spec.badge} {spec.id}** · {spec.family} · {spec.status}\n\n{spec.description}\n\n"
                f"Voices: {len(spec.voices)}+ · formats {', '.join(spec.formats)} · ≤ {spec.max_chars} chars"
                + (f" · {', '.join(caps)}" if caps else ""))

    # ====================================================================== UI
    def create_interface(self) -> gr.Blocks:
        banner = []
        if self.dry_run:
            banner.append("🧪 **Dry-run mode** — requests are previewed, not sent "
                          f"({'WAN_DRY_RUN=1' if Config.DRY_RUN else 'no DASHSCOPE_API_KEY'}).")
        if not Config.OSS_ENABLE:
            banner.append("⚠️ OSS not configured: uploaded images fall back to a demo picture. "
                          "Set OSS_ACCESS_KEY_ID / OSS_ACCESS_KEY_SECRET / OSS_BUCKET_NAME.")
        banner.append(f"🌐 Region `{Config.DASHSCOPE_REGION}` → `{Config.DASHSCOPE_BASE_URL}`")

        with gr.Blocks(title="Wan Gateway Studio", analytics_enabled=False, **self._blocks_kwargs()) as ui:
            gr.Markdown("# 🎬 Wan Gateway Studio\n"
                        "Video · Image · Speech on Alibaba Cloud Model Studio — **Wan 3.0 / 2.7 / 2.6**, "
                        "**Wan 2.7 Image**, **Qwen-Image 3.0**, **Qwen3-TTS**, **CosyVoice 3.x**.")
            gr.Markdown("\n\n".join(banner), elem_classes=["small-note"])
            with gr.Tabs():
                with gr.Tab("🎬 Video"):
                    self._video_tab()
                with gr.Tab("🖼️ Image"):
                    self._image_tab()
                with gr.Tab("🔊 Speech"):
                    self._speech_tab()
            with gr.Accordion("ℹ️ Help", open=False):
                gr.Markdown(
                    "**Video:** `wan3.0-video` does everything (2–30 s, smart duration, adaptive ratio, "
                    "editing). `wan2.7-*` for 2–15 s clips with strong audio sync, `wan2.6-*-flash` when speed "
                    "matters, `wan2.6-t2v` for explicit multi-shot storyboards, `wan2.7-videoedit` to restyle a clip.\n\n"
                    "**Image:** `wan2.7-image-pro` (up to 4K, image sets, references) or `qwen-image-3.0-pro` "
                    "(best text rendering, identity-preserving edits). Drop images in to switch to editing.\n\n"
                    "**Speech:** `qwen3-tts-flash` for 49 voices / 10 languages; CosyVoice 3.x for cloned voices "
                    "and natural-language style instructions.\n\n"
                    "**Images in:** JPEG/PNG/BMP/WEBP, ≤10 MB, 360–2000 px per side, uploaded to your OSS bucket "
                    "as signed URLs. Videos / audio are passed as public URLs.\n\n"
                    f"**Files out:** `{Config.DATA_DIR}` (videos / images / audio). Result URLs expire in 24 h.\n\n"
                    "**CLI:** `python cli.py models | catalog | generate | image | tts | status | history`."
                )
        return ui

    # ----------------------------------------------------------- video tab
    def _video_tab(self) -> None:
        init_choices = self._model_choices(T2V)
        init_model = self._pick(init_choices, default_model_for_task(T2V), model_id_from_display)
        init_spec = get_spec(model_id_from_display(init_model))

        with gr.Row(equal_height=False):
            with gr.Column(scale=5):
                task_radio = gr.Radio(list(TASK_LABELS.values()), value=TASK_LABELS[T2V], label="Task")
                task_desc = gr.Markdown(TASK_DESCRIPTIONS[T2V], elem_classes=["small-note"])
                model_dd = gr.Dropdown(init_choices, value=init_model, label="Model",
                                       info="🆕 latest · ✅ stable · 🕰️ legacy")
                model_card = gr.Markdown(self._model_card(init_spec), elem_classes=["small-note"])
                with gr.Row():
                    prompt_tb = gr.Textbox(label="Prompt", lines=4, scale=5,
                                           placeholder="Describe subject, action, camera, light, mood, sound. "
                                                       "Multi-shot: 'Shot 1 [0-5s]: …'")
                    optimize_btn = gr.Button("✨ Enhance", scale=1, variant="secondary")
                gr.Examples(EXAMPLE_PROMPTS, inputs=[prompt_tb], label="Prompt ideas")

                with gr.Row(visible=False) as frames_row:
                    first_frame = gr.Image(label="First frame", type="filepath", height=220)
                    last_frame = gr.Image(label="Last frame", type="filepath", height=220, visible=False)
                video_url_tb = gr.Textbox(label="Source video URL (public)", visible=False,
                                          placeholder="https://…/clip.mp4")
                ref_files = gr.File(label="Reference images", file_count="multiple", file_types=["image"], visible=False)
                ref_urls = gr.Textbox(label="Reference URLs (one per line: image / video / audio)", lines=3,
                                      visible=False, placeholder="https://…/character.png\nhttps://…/clip.mp4\nhttps://…/voice.mp3")

                with gr.Group():
                    with gr.Row():
                        resolution_dd = gr.Dropdown(list(init_spec.resolutions), value=init_spec.default_resolution, label="Resolution")
                        ratio_dd = gr.Dropdown(list(init_spec.ratios), value="16:9", label="Aspect ratio")
                    with gr.Row():
                        duration_sl = gr.Slider(init_spec.duration_min, init_spec.duration_max, value=init_spec.default_duration,
                                                step=init_spec.duration_step,
                                                label=f"⏱️ Duration (s) — {init_spec.duration_label}", scale=3)
                        smart_cb = gr.Checkbox(label="Smart duration (-1)", value=False, visible=init_spec.smart_duration, scale=1)
                    with gr.Row():
                        audio_cb = gr.Checkbox(label="🎵 Generate audio", value=True, visible=init_spec.audio)
                        shot_radio = gr.Radio(["single", "multi"], value="single", label="Shots", visible=init_spec.shot_type)
                    audio_url_tb = gr.Textbox(label="🎧 Custom audio / voice URL (optional)", visible=init_spec.audio_url,
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
        form_inputs = [task_radio, model_dd, prompt_tb, negative_tb, first_frame, last_frame, ref_files, ref_urls,
                       video_url_tb, resolution_dd, ratio_dd, duration_sl, smart_cb, audio_cb, audio_url_tb,
                       shot_radio, prompt_extend_cb, seed_tb, watermark_cb]
        fit_outputs = [resolution_dd, ratio_dd, duration_sl, smart_cb, audio_cb, audio_url_tb, shot_radio, model_card]

        task_radio.change(self.on_task_change, [task_radio],
                          [model_dd, frames_row, last_frame, ref_files, ref_urls, video_url_tb, task_desc, *fit_outputs])
        model_dd.change(self.on_model_change, [model_dd, task_radio], fit_outputs)
        preview_btn.click(self.preview, form_inputs, [payload_json, status_md])
        generate_btn.click(self.submit, form_inputs, [task_state, status_md, timer, payload_json, history_df])
        timer.tick(self.poll, [task_state], [video_out, status_md, timer, history_df])
        resume_btn.click(self.resume, [resume_tb], [task_state, status_md, timer])
        cancel_btn.click(self.cancel, [task_state], [status_md, timer])
        history_df.select(self.on_history_select, [history_df], [resume_tb])
        optimize_btn.click(optimize_prompt_with_qwen, [prompt_tb], [prompt_tb])

    # ----------------------------------------------------------- image tab
    def _image_tab(self) -> None:
        init_choices = self._image_choices(IMAGE_TASK_T2I)
        init_model = self._pick(init_choices, DEFAULT_IMAGE_MODEL[IMAGE_TASK_T2I], id_from_display)
        init_spec = get_image_spec(id_from_display(init_model))

        with gr.Row(equal_height=False):
            with gr.Column(scale=5):
                task_radio = gr.Radio(list(IMAGE_TASK_LABELS.values()), value=IMAGE_TASK_LABELS[IMAGE_TASK_T2I], label="Task")
                model_dd = gr.Dropdown(init_choices, value=init_model, label="Model",
                                       info="🆕 latest · ✅ stable · 🕰️ legacy")
                model_card = gr.Markdown(self._image_card(init_spec), elem_classes=["small-note"])
                prompt_tb = gr.Textbox(label="Prompt / edit instruction", lines=4,
                                       placeholder="What to draw — or, with input images, what to change.")
                gr.Examples(IMAGE_EXAMPLES, inputs=[prompt_tb], label="Prompt ideas")
                files = gr.File(label=f"Input images (≤{init_spec.max_input_images}) — required for editing",
                                file_count="multiple", file_types=["image"], visible=init_spec.max_input_images > 0)
                urls_tb = gr.Textbox(label="Input image URLs (one per line, optional)", lines=2,
                                     placeholder="https://…/photo.png")
                with gr.Group():
                    with gr.Row():
                        size_dd = gr.Dropdown(list(init_spec.sizes), value=init_spec.default_size, label="Size",
                                              allow_custom_value=True, info="pick one or type W*H")
                        n_sl = gr.Slider(1, init_spec.max_n, value=1, step=1, label=f"Images per call (≤{init_spec.max_n})",
                                         interactive=init_spec.max_n > 1)
                with gr.Accordion("⚙️ Advanced", open=False):
                    negative_tb = gr.Textbox(label="Negative prompt", lines=2)
                    with gr.Row():
                        seed_tb = gr.Textbox(label="Seed", placeholder="random")
                        prompt_extend_cb = gr.Checkbox(label="Prompt rewrite (prompt_extend)", value=True)
                        watermark_cb = gr.Checkbox(label="Watermark", value=False)
                with gr.Row():
                    gen_btn = gr.Button("🖌️ Generate", variant="primary", scale=3)
                    prev_btn = gr.Button("🔍 Preview request", scale=1)
            with gr.Column(scale=5):
                status_md = gr.Markdown("Ready.")
                gallery = gr.Gallery(label="Results", columns=2, height=420, object_fit="contain")
                with gr.Accordion("📦 Request payload (exactly what is sent)", open=False):
                    payload_json = gr.JSON()

        inputs = [task_radio, model_dd, prompt_tb, negative_tb, files, urls_tb, size_dd, n_sl, seed_tb,
                  prompt_extend_cb, watermark_cb]
        fit = [size_dd, n_sl, files, model_card]
        task_radio.change(self.on_image_task_change, [task_radio], [model_dd, urls_tb, *fit])
        model_dd.change(self.on_image_model_change, [model_dd], fit)
        prev_btn.click(self.image_preview, inputs, [payload_json, status_md])
        gen_btn.click(self.image_generate, inputs, [gallery, status_md, payload_json])

    # ---------------------------------------------------------- speech tab
    def _speech_tab(self) -> None:
        init_choices = self._speech_choices()
        init_model = self._pick(init_choices, DEFAULT_SPEECH_MODEL, id_from_display)
        init_spec = get_speech_spec(id_from_display(init_model))

        with gr.Row(equal_height=False):
            with gr.Column(scale=5):
                model_dd = gr.Dropdown(init_choices, value=init_model, label="Model",
                                       info="🆕 latest · ✅ stable · 🕰️ legacy")
                model_card = gr.Markdown(self._speech_card(init_spec), elem_classes=["small-note"])
                text_tb = gr.Textbox(label="Text", lines=5, placeholder="Text to speak…")
                gr.Examples(SPEECH_EXAMPLES, inputs=[text_tb], label="Samples")
                with gr.Row():
                    voice_dd = gr.Dropdown(list(init_spec.voices), value=init_spec.default_voice, label="Voice",
                                           allow_custom_value=True, info="pick one or paste a cloned voice id")
                    lang_dd = gr.Dropdown(list(init_spec.languages), value=init_spec.languages[0], label="Language",
                                          visible=init_spec.dialect == "tts_mm")
                instr_tb = gr.Textbox(label="Style instruction (optional)", visible=init_spec.instruct,
                                      placeholder="e.g. 用兴奋的语气，语速稍快 / warm late-night radio host")
                with gr.Row():
                    fmt_dd = gr.Dropdown(list(init_spec.formats), value=init_spec.formats[0], label="Format")
                    sr_dd = gr.Dropdown([str(r) for r in init_spec.sample_rates], value=str(init_spec.sample_rates[0]),
                                        label="Sample rate", visible=init_spec.dialect == "tts_cosy")
                    rate_sl = gr.Slider(0.5, 2.0, value=1.0, step=0.1, label="Speed", visible=init_spec.dialect == "tts_cosy")
                with gr.Row():
                    gen_btn = gr.Button("🔊 Synthesize", variant="primary", scale=3)
                    prev_btn = gr.Button("🔍 Preview request", scale=1)
            with gr.Column(scale=5):
                status_md = gr.Markdown("Ready.")
                audio_out = gr.Audio(label="Result", type="filepath")
                with gr.Accordion("📦 Request payload (exactly what is sent)", open=False):
                    payload_json = gr.JSON()

        inputs = [model_dd, text_tb, voice_dd, lang_dd, instr_tb, fmt_dd, sr_dd, rate_sl]
        model_dd.change(self.on_speech_model_change, [model_dd],
                        [voice_dd, lang_dd, instr_tb, fmt_dd, sr_dd, rate_sl, model_card])
        prev_btn.click(self.speech_preview, inputs, [payload_json, status_md])
        gen_btn.click(self.speech_generate, inputs, [audio_out, status_md, payload_json])

    # ------------------------------------------------------------- launch
    _THEME_KW = dict(css=".small-note{font-size:0.85em;opacity:.8}")

    @staticmethod
    def _gradio_major() -> int:
        try:
            return int(gr.__version__.split(".")[0])
        except Exception:  # pragma: no cover
            return 5

    def _blocks_kwargs(self) -> Dict[str, Any]:
        return {} if self._gradio_major() >= 6 else {"theme": gr.themes.Soft(), **self._THEME_KW}

    def _launch_kwargs(self) -> Dict[str, Any]:
        return {"theme": gr.themes.Soft(), **self._THEME_KW} if self._gradio_major() >= 6 else {}

    def launch(self, server_name="127.0.0.1", server_port=7860, share=False, debug=False) -> None:
        ui = self.create_interface()
        logger.info("Launching Wan Gateway Studio on %s:%s", server_name, server_port)
        common = dict(server_name=server_name, server_port=server_port, debug=debug,
                      show_error=True, quiet=True, auth=Config.UI_AUTH, **self._launch_kwargs())
        if Config.UI_AUTH:
            logger.info("UI login enabled for %d user(s)", len(Config.UI_AUTH))
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
