"""
Build DashScope ``video-synthesis`` payloads from a single, model-agnostic
:class:`GenerationRequest`.

The caller fills in what the user asked for; :func:`build_payload` looks up the
model's :class:`~src.models.ModelSpec` and emits the exact JSON the model's
API dialect expects, dropping anything the model does not support.  The result
is deterministic and side-effect free, which makes it easy to unit-test and to
show the user in a "request preview" panel before anything is sent.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .models import (
    I2V, KF2V, R2V, T2V, ModelSpec, get_spec, size_for,
)


@dataclass
class GenerationRequest:
    model: str
    task: str = T2V
    prompt: str = ""
    negative_prompt: Optional[str] = None
    resolution: Optional[str] = None          # "480P" | "720P" | "1080P"
    ratio: Optional[str] = None               # "16:9" ... | "adaptive"
    duration: Optional[int] = None            # seconds, -1 = smart (Wan 3.0)
    audio: Optional[bool] = None
    audio_url: Optional[str] = None
    shot_type: Optional[str] = None           # "single" | "multi"
    prompt_extend: Optional[bool] = None
    seed: Optional[int] = None
    watermark: Optional[bool] = None
    # media inputs (public URLs)
    first_frame_url: Optional[str] = None
    last_frame_url: Optional[str] = None
    reference_image_urls: List[str] = field(default_factory=list)
    reference_video_urls: List[str] = field(default_factory=list)
    reference_audio_urls: List[str] = field(default_factory=list)
    # escape hatch: merged last into ``parameters`` verbatim
    extra_parameters: Dict[str, Any] = field(default_factory=dict)


class RequestValidationError(ValueError):
    """Raised when a request cannot be satisfied by the chosen model."""


def _clean(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    text = text.strip()
    return text or None


def validate(req: GenerationRequest) -> ModelSpec:
    """Check *req* against its model spec. Returns the spec on success."""
    spec = get_spec(req.model)

    if not spec.supports(req.task):
        raise RequestValidationError(
            f"{spec.id} does not support task '{req.task}'. "
            f"Supported: {', '.join(spec.tasks)}"
        )

    prompt = _clean(req.prompt)
    if req.task == T2V and not prompt:
        raise RequestValidationError("Prompt cannot be empty for text-to-video.")
    if prompt and len(prompt) > spec.max_prompt:
        raise RequestValidationError(
            f"Prompt too long ({len(prompt)} chars). {spec.id} accepts up to {spec.max_prompt}."
        )

    if req.task in (I2V, KF2V) and not req.first_frame_url:
        raise RequestValidationError("A first-frame image is required.")
    if req.task == KF2V and not req.last_frame_url:
        raise RequestValidationError("A last-frame image is required for keyframe mode.")
    if req.task == R2V and not (
        req.reference_image_urls or req.reference_video_urls or req.reference_audio_urls
    ):
        raise RequestValidationError("At least one reference image / video / audio is required.")

    if req.resolution and req.resolution not in spec.resolutions:
        raise RequestValidationError(
            f"{spec.id} supports resolutions {', '.join(spec.resolutions)}, not {req.resolution}."
        )
    if req.ratio and req.ratio not in spec.ratios:
        raise RequestValidationError(
            f"{spec.id} supports ratios {', '.join(spec.ratios)}, not {req.ratio}."
        )
    if req.duration is not None:
        if req.duration == -1:
            if not spec.smart_duration:
                raise RequestValidationError(f"{spec.id} does not support smart duration (-1).")
        elif not (spec.duration_min <= int(req.duration) <= spec.duration_max):
            raise RequestValidationError(
                f"{spec.id} accepts {spec.duration_label}; got {req.duration}s."
            )
    if req.shot_type and req.shot_type not in ("single", "multi"):
        raise RequestValidationError("shot_type must be 'single' or 'multi'.")
    if req.task == KF2V and spec.dialect == "media" and req.reference_audio_urls:
        raise RequestValidationError(
            "First/last-frame mode cannot be combined with reference audio on this model."
        )
    return spec


def build_payload(req: GenerationRequest) -> Dict[str, Any]:
    """Return the JSON body for ``POST .../video-generation/video-synthesis``."""
    spec = validate(req)

    prompt = _clean(req.prompt)
    negative = _clean(req.negative_prompt) if spec.negative_prompt else None
    resolution = req.resolution or spec.default_resolution
    ratio = req.ratio or ("16:9" if "16:9" in spec.ratios else spec.ratios[0])
    duration = spec.clamp_duration(req.duration)

    inp: Dict[str, Any] = {}
    params: Dict[str, Any] = {}

    if prompt:
        inp["prompt"] = prompt
    if negative:
        inp["negative_prompt"] = negative

    # ---------------------------------------------------------------- media
    if spec.dialect == "media":
        media: List[Dict[str, str]] = []
        if req.first_frame_url:
            media.append({"type": "first_frame", "url": req.first_frame_url})
        if req.last_frame_url:
            media.append({"type": "last_frame", "url": req.last_frame_url})
        for url in req.reference_image_urls:
            media.append({"type": "reference_image", "url": url})
        for url in req.reference_video_urls:
            media.append({"type": "reference_video", "url": url})
        for url in req.reference_audio_urls:
            media.append({"type": "reference_audio", "url": url})
        if spec.audio_url and req.audio_url and _clean(req.audio_url):
            media.append({"type": "reference_audio", "url": req.audio_url.strip()})
        if media:
            inp["media"] = media
        params["resolution"] = resolution
        params["ratio"] = ratio
        params["duration"] = duration

    # ---------------------------------------------------------------- label
    elif spec.dialect == "label":
        if req.first_frame_url:
            inp["img_url"] = req.first_frame_url
        if spec.audio_url and _clean(req.audio_url):
            inp["audio_url"] = req.audio_url.strip()
        params["resolution"] = resolution
        if spec.duration_min != spec.duration_max or spec.family >= "2.5":
            params["duration"] = duration

    # ----------------------------------------------------------------- size
    elif spec.dialect == "size":
        if spec.audio_url and _clean(req.audio_url):
            inp["audio_url"] = req.audio_url.strip()
        params["size"] = size_for(resolution, ratio)
        if spec.duration_min != spec.duration_max:
            params["duration"] = duration

    # ----------------------------------------------------------------- kf2v
    elif spec.dialect == "kf2v":
        inp["first_frame_url"] = req.first_frame_url
        inp["last_frame_url"] = req.last_frame_url
        params["resolution"] = resolution

    # ------------------------------------------------------------------ r2v
    elif spec.dialect == "r2v":
        refs = list(req.reference_image_urls) + list(req.reference_video_urls)
        inp["reference_urls"] = refs
        if req.reference_audio_urls:
            inp["reference_audio_urls"] = list(req.reference_audio_urls)
        params["size"] = size_for(resolution, ratio)
        params["duration"] = duration

    else:  # pragma: no cover - defensive
        raise RequestValidationError(f"Unknown dialect '{spec.dialect}' for {spec.id}")

    # ------------------------------------------------------- shared options
    if spec.audio:
        params["audio"] = True if req.audio is None else bool(req.audio)
    if spec.shot_type and req.shot_type:
        params["shot_type"] = req.shot_type
    if spec.prompt_extend and req.prompt_extend is not None:
        params["prompt_extend"] = bool(req.prompt_extend)
    if spec.seed and req.seed is not None:
        params["seed"] = int(req.seed)
    if spec.watermark and req.watermark is not None:
        params["watermark"] = bool(req.watermark)

    params.update(req.extra_parameters or {})

    return {"model": spec.id, "input": inp, "parameters": params}


def billable_seconds(req: GenerationRequest) -> Optional[int]:
    """Seconds the user will be charged for, or None for smart duration."""
    spec = get_spec(req.model)
    d = spec.clamp_duration(req.duration)
    return None if d == -1 else d
