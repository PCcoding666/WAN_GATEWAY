"""
Declarative registry of Wan (通义万相) video models exposed on Alibaba Cloud
Model Studio / DashScope.

Every model is described by a ``ModelSpec``.  The UI, the request builder and
the CLI all read from this single table, so adding a new model (or fixing a
limit when Alibaba changes it) is a one-line edit here and nothing else.

Status legend
-------------
latest      newest generation, recommended default
stable      fully supported, still a good choice
legacy      works, but superseded; hidden behind "show legacy" unless needed
deprecated  may be removed by Alibaba at any time; hidden by default

Request "dialects"
------------------
The DashScope payload shape changed across generations:

media       Wan 2.7 / 3.0  -> ``input.media=[{type,url}]`` + ``parameters.resolution/ratio``
label       Wan 2.2 i2v, 2.5, 2.6 i2v -> ``input.img_url`` + ``parameters.resolution="1080P"``
size        Wan 2.1/2.2/2.6 t2v -> ``parameters.size="1920*1080"``
kf2v        wanx2.1-kf2v-plus / wan2.2-kf2v-flash -> ``input.first_frame_url/last_frame_url``
r2v         Wan 2.6 r2v -> ``input.reference_urls=[...]`` + ``parameters.size``

Sources (Oct 2026): Alibaba Cloud Model Studio "Wan3.0 Video Generation API
Reference", "Wan2.7 Text-to-Video / Image-to-Video API Reference",
"Wan text-to-video / image-to-video API reference (2.1-2.6)",
"Wan2.6 reference-to-video API reference", "Wan first-and-last-frame (2.2)".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Task identifiers used throughout the app
T2V = "t2v"      # text -> video
I2V = "i2v"      # first frame image -> video
KF2V = "kf2v"    # first + last frame -> video
R2V = "r2v"      # reference images / videos / audio -> video

TASKS: Tuple[str, ...] = (T2V, I2V, KF2V, R2V)

TASK_LABELS: Dict[str, str] = {
    T2V: "📝 Text → Video",
    I2V: "🖼️ Image → Video",
    KF2V: "🎞️ Keyframes → Video",
    R2V: "🎭 Reference → Video",
}

TASK_DESCRIPTIONS: Dict[str, str] = {
    T2V: "Describe a scene and let the model shoot it.",
    I2V: "Animate a single image (used as the first frame).",
    KF2V: "Interpolate between a start frame and an end frame.",
    R2V: "Keep characters / style consistent from reference images, clips or audio.",
}

ALL_RATIOS: Tuple[str, ...] = ("16:9", "9:16", "1:1", "4:3", "3:4")

# width*height for the ``size`` dialect
SIZE_TABLE: Dict[str, Dict[str, str]] = {
    "480P": {"16:9": "832*480", "9:16": "480*832", "1:1": "624*624",
             "4:3": "640*480", "3:4": "480*640"},
    "720P": {"16:9": "1280*720", "9:16": "720*1280", "1:1": "960*960",
             "4:3": "1088*832", "3:4": "832*1088"},
    "1080P": {"16:9": "1920*1080", "9:16": "1080*1920", "1:1": "1440*1440",
              "4:3": "1632*1248", "3:4": "1248*1632"},
}


@dataclass(frozen=True)
class ModelSpec:
    id: str
    family: str
    tasks: Tuple[str, ...]
    dialect: str
    resolutions: Tuple[str, ...]
    ratios: Tuple[str, ...] = ALL_RATIOS[:3]
    duration_min: int = 5
    duration_max: int = 5
    duration_step: int = 1
    default_duration: int = 5
    smart_duration: bool = False      # supports duration=-1 (model picks length)
    fps: int = 30
    audio: bool = False               # ``parameters.audio`` toggle
    audio_url: bool = False           # custom audio track
    shot_type: bool = False           # ``parameters.shot_type`` single|multi
    prompt_extend: bool = True        # ``parameters.prompt_extend``
    negative_prompt: bool = True
    seed: bool = True
    watermark: bool = True
    max_prompt: int = 2000
    status: str = "stable"
    description: str = ""
    eta: str = "1-3 min"
    notes: Tuple[str, ...] = field(default_factory=tuple)

    # ---- convenience -----------------------------------------------------
    @property
    def default_resolution(self) -> str:
        return self.resolutions[-1]

    @property
    def is_hidden(self) -> bool:
        return self.status in ("legacy", "deprecated")

    @property
    def badge(self) -> str:
        return {
            "latest": "🆕",
            "stable": "✅",
            "legacy": "🕰️",
            "deprecated": "⚠️",
        }.get(self.status, "")

    @property
    def duration_label(self) -> str:
        if self.duration_min == self.duration_max:
            base = f"{self.duration_min}s"
        else:
            base = f"{self.duration_min}-{self.duration_max}s"
        return base + (" (or smart)" if self.smart_duration else "")

    def supports(self, task: str) -> bool:
        return task in self.tasks

    def clamp_duration(self, value: Optional[int]) -> int:
        if value is None:
            return self.default_duration
        if value == -1 and self.smart_duration:
            return -1
        value = int(value)
        value = max(self.duration_min, min(self.duration_max, value))
        # snap to step
        if self.duration_step > 1:
            offset = value - self.duration_min
            value = self.duration_min + round(offset / self.duration_step) * self.duration_step
            value = min(value, self.duration_max)
        return value


# ---------------------------------------------------------------------------
# The registry.  Order matters: it is the order shown in the UI.
# ---------------------------------------------------------------------------
_SPECS: List[ModelSpec] = [
    # ------------------------------------------------------------------ 3.0
    ModelSpec(
        id="wan3.0-video",
        family="3.0",
        tasks=(T2V, I2V, KF2V, R2V),
        dialect="media",
        resolutions=("480P", "720P", "1080P"),
        ratios=ALL_RATIOS + ("adaptive",),
        duration_min=2, duration_max=30, default_duration=5, smart_duration=True,
        fps=30, audio=True, audio_url=True,
        status="latest",
        description="Wan 3.0 All-in-One: text / first frame / first+last frame / "
                    "reference-to-video in one model. Up to 30 s, 1080P, native audio, "
                    "smart duration, adaptive ratio.",
        eta="2-6 min",
        notes=("First/last-frame mode cannot be combined with reference audio.",
               "With reference video: input + output duration ≤ 30 s."),
    ),
    # ------------------------------------------------------------------ 2.7
    ModelSpec(
        id="wan2.7-t2v",
        family="2.7",
        tasks=(T2V,),
        dialect="media",
        resolutions=("720P", "1080P"),
        ratios=ALL_RATIOS,
        duration_min=2, duration_max=15, default_duration=5,
        fps=30, audio=True, audio_url=True,
        status="stable",
        description="Wan 2.7 text-to-video. 2-15 s, 720P/1080P, 30 fps, synchronized audio.",
    ),
    ModelSpec(
        id="wan2.7-i2v",
        family="2.7",
        tasks=(I2V, KF2V),
        dialect="media",
        resolutions=("720P", "1080P"),
        ratios=ALL_RATIOS,
        duration_min=2, duration_max=15, default_duration=5,
        fps=30, audio=True, audio_url=True,
        status="stable",
        description="Wan 2.7 image-to-video. First frame or first+last frame, 2-15 s, audio.",
        eta="2-5 min",
    ),
    ModelSpec(
        id="wan2.7-r2v",
        family="2.7",
        tasks=(R2V,),
        dialect="media",
        resolutions=("720P", "1080P"),
        ratios=ALL_RATIOS,
        duration_min=2, duration_max=10, default_duration=5,
        fps=30, audio=True, audio_url=True, shot_type=True,
        status="stable",
        description="Wan 2.7 reference-to-video. Character / style consistency from up to "
                    "several reference images or clips, single or multi-shot.",
        eta="3-6 min",
    ),
    # ------------------------------------------------------------------ 2.6
    ModelSpec(
        id="wan2.6-t2v",
        family="2.6",
        tasks=(T2V,),
        dialect="size",
        resolutions=("720P", "1080P"),
        ratios=ALL_RATIOS,
        duration_min=2, duration_max=15, default_duration=5,
        fps=30, audio=True, audio_url=True, shot_type=True,
        status="stable",
        description="Wan 2.6 text-to-video. 2-15 s, multi-shot storyboard control, audio.",
    ),
    ModelSpec(
        id="wan2.6-i2v",
        family="2.6",
        tasks=(I2V,),
        dialect="label",
        resolutions=("720P", "1080P"),
        duration_min=2, duration_max=15, default_duration=5,
        fps=30, audio=True, audio_url=True, shot_type=True,
        status="stable",
        description="Wan 2.6 image-to-video (first frame). 2-15 s, multi-shot, audio.",
        eta="2-5 min",
    ),
    ModelSpec(
        id="wan2.6-i2v-flash",
        family="2.6",
        tasks=(I2V,),
        dialect="label",
        resolutions=("720P", "1080P"),
        duration_min=2, duration_max=15, default_duration=5,
        fps=30, audio=True, audio_url=True, shot_type=True,
        status="stable",
        description="Wan 2.6 image-to-video Flash: same features, faster and cheaper.",
        eta="1-3 min",
    ),
    ModelSpec(
        id="wan2.6-r2v",
        family="2.6",
        tasks=(R2V,),
        dialect="r2v",
        resolutions=("720P", "1080P"),
        ratios=ALL_RATIOS,
        duration_min=2, duration_max=10, default_duration=5,
        fps=30, audio=True, shot_type=True,
        status="stable",
        description="Wan 2.6 reference-to-video (reference_urls). 2-10 s.",
        eta="3-6 min",
    ),
    ModelSpec(
        id="wan2.6-r2v-flash",
        family="2.6",
        tasks=(R2V,),
        dialect="r2v",
        resolutions=("720P", "1080P"),
        ratios=ALL_RATIOS,
        duration_min=2, duration_max=10, default_duration=5,
        fps=30, audio=True, shot_type=True,
        status="stable",
        description="Wan 2.6 reference-to-video Flash.",
        eta="2-4 min",
    ),
    # ------------------------------------------------------------------ 2.5
    ModelSpec(
        id="wan2.5-t2v-preview",
        family="2.5",
        tasks=(T2V,),
        dialect="label",
        resolutions=("480P", "720P", "1080P"),
        duration_min=5, duration_max=10, duration_step=5, default_duration=5,
        fps=24, audio=True, audio_url=True,
        status="legacy",
        description="Wan 2.5 preview text-to-video. 5 or 10 s, 24 fps, audio.",
    ),
    ModelSpec(
        id="wan2.5-i2v-preview",
        family="2.5",
        tasks=(I2V,),
        dialect="label",
        resolutions=("480P", "720P", "1080P"),
        duration_min=5, duration_max=10, duration_step=5, default_duration=5,
        fps=24, audio=True, audio_url=True,
        status="legacy",
        description="Wan 2.5 preview image-to-video. 5 or 10 s, 24 fps, audio.",
        eta="2-5 min",
    ),
    # ------------------------------------------------------------------ 2.2
    ModelSpec(
        id="wan2.2-t2v-plus",
        family="2.2",
        tasks=(T2V,),
        dialect="size",
        resolutions=("480P", "1080P"),
        duration_min=5, duration_max=5,
        fps=30, max_prompt=800,
        status="legacy",
        description="Wan 2.2 text-to-video Plus. Silent 5 s clips.",
    ),
    ModelSpec(
        id="wan2.2-i2v-flash",
        family="2.2",
        tasks=(I2V,),
        dialect="label",
        resolutions=("480P", "720P"),
        duration_min=5, duration_max=5,
        fps=30, max_prompt=800,
        status="legacy",
        description="Wan 2.2 image-to-video Flash. Silent 5 s clips, fast.",
        eta="1-2 min",
    ),
    ModelSpec(
        id="wan2.2-i2v-plus",
        family="2.2",
        tasks=(I2V,),
        dialect="label",
        resolutions=("480P", "1080P"),
        duration_min=5, duration_max=5,
        fps=30, max_prompt=800,
        status="legacy",
        description="Wan 2.2 image-to-video Plus. Silent 5 s clips.",
        eta="2-5 min",
    ),
    ModelSpec(
        id="wan2.2-kf2v-flash",
        family="2.2",
        tasks=(KF2V,),
        dialect="kf2v",
        resolutions=("480P", "720P", "1080P"),
        duration_min=5, duration_max=5,
        fps=30, max_prompt=800,
        status="legacy",
        description="Wan 2.2 first-and-last-frame Flash. Silent 5 s transitions.",
        eta="2-5 min",
    ),
    # ------------------------------------------------------------------ 2.1 (deprecated)
    ModelSpec(
        id="wanx2.1-t2v-turbo", family="2.1", tasks=(T2V,), dialect="size",
        resolutions=("480P", "720P"), max_prompt=800, status="deprecated",
        description="Wan 2.1 Turbo text-to-video (deprecated).",
    ),
    ModelSpec(
        id="wanx2.1-t2v-plus", family="2.1", tasks=(T2V,), dialect="size",
        resolutions=("720P",), max_prompt=800, status="deprecated",
        description="Wan 2.1 Plus text-to-video (deprecated).",
    ),
    ModelSpec(
        id="wanx2.1-i2v-plus", family="2.1", tasks=(I2V,), dialect="label",
        resolutions=("720P",), max_prompt=800, status="deprecated",
        description="Wan 2.1 Plus image-to-video (deprecated).", eta="5-10 min",
    ),
    ModelSpec(
        id="wanx2.1-i2v-turbo", family="2.1", tasks=(I2V,), dialect="label",
        resolutions=("480P", "720P"), duration_min=3, duration_max=5, max_prompt=800,
        status="deprecated", description="Wan 2.1 Turbo image-to-video (deprecated).",
        eta="2-5 min",
    ),
    ModelSpec(
        id="wanx2.1-kf2v-plus", family="2.1", tasks=(KF2V,), dialect="kf2v",
        resolutions=("720P",), max_prompt=800, status="deprecated",
        description="Wan 2.1 keyframe-to-video (deprecated).", eta="5-10 min",
    ),
]

REGISTRY: Dict[str, ModelSpec] = {s.id: s for s in _SPECS}

DEFAULT_MODEL_FOR_TASK: Dict[str, str] = {
    T2V: "wan3.0-video",
    I2V: "wan3.0-video",
    KF2V: "wan3.0-video",
    R2V: "wan3.0-video",
}


def get_spec(model_id: str) -> ModelSpec:
    try:
        return REGISTRY[model_id]
    except KeyError:
        raise ValueError(
            f"Unknown model '{model_id}'. Known models: {', '.join(REGISTRY)}"
        ) from None


def models_for_task(task: str, include_hidden: bool = False) -> List[ModelSpec]:
    """Models that support ``task`` in UI order (latest first)."""
    return [
        s for s in _SPECS
        if s.supports(task) and (include_hidden or not s.is_hidden)
    ]


def model_ids_for_task(task: str, include_hidden: bool = False) -> List[str]:
    return [s.id for s in models_for_task(task, include_hidden)]


def default_model_for_task(task: str) -> str:
    return DEFAULT_MODEL_FOR_TASK.get(task, "wan3.0-video")


def display_name(spec: ModelSpec) -> str:
    """Dropdown label: ``🆕 wan3.0-video · 2-30s · 1080P · audio``."""
    bits = [f"{spec.badge} {spec.id}", spec.duration_label, spec.resolutions[-1]]
    if spec.audio:
        bits.append("audio")
    if spec.shot_type:
        bits.append("multi-shot")
    return " · ".join(bits)


def model_id_from_display(label: str) -> str:
    """Inverse of :func:`display_name`; tolerant of plain ids."""
    if label in REGISTRY:
        return label
    token = label.split(" · ")[0].strip()
    token = token.split(" ", 1)[-1] if " " in token else token
    return token if token in REGISTRY else label


def size_for(resolution: str, ratio: str) -> str:
    """``(1080P, 16:9) -> 1920*1080`` for the legacy ``size`` dialect."""
    table = SIZE_TABLE.get(resolution) or SIZE_TABLE["1080P"]
    return table.get(ratio) or table["16:9"]
