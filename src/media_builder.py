"""
Payload builders for image generation / editing and speech synthesis.

Mirrors :mod:`src.request_builder` for video: fill a request dataclass, call
``build_*_payload`` and get back ``(http_path, json_body, is_async)``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .catalog import (
    IMAGE_TASK_EDIT, IMAGE_TASK_T2I, ImageModelSpec, SpeechModelSpec,
    get_image_spec, get_speech_spec,
)

MULTIMODAL_PATH = "/api/v1/services/aigc/multimodal-generation/generation"
TEXT2IMAGE_PATH = "/api/v1/services/aigc/text2image/image-synthesis"
COSYVOICE_PATH = "/api/v1/services/audio/tts/SpeechSynthesizer"


class MediaValidationError(ValueError):
    pass


def _clean(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    text = text.strip()
    return text or None


# ---------------------------------------------------------------------- image
@dataclass
class ImageRequest:
    model: str
    task: str = IMAGE_TASK_T2I
    prompt: str = ""
    negative_prompt: Optional[str] = None
    size: Optional[str] = None            # "1328*1328" | "2K" | None (auto)
    n: int = 1
    seed: Optional[int] = None
    prompt_extend: Optional[bool] = None
    watermark: Optional[bool] = None
    image_urls: List[str] = field(default_factory=list)   # source / reference images
    extra_parameters: Dict[str, Any] = field(default_factory=dict)


def _parse_wh(size: str) -> Optional[Tuple[int, int]]:
    if "*" in size:
        try:
            w, h = size.lower().split("*")
            return int(w), int(h)
        except ValueError:
            return None
    return None


def validate_image(req: ImageRequest) -> ImageModelSpec:
    spec = get_image_spec(req.model)
    if not spec.supports(req.task):
        raise MediaValidationError(f"{spec.id} does not support '{req.task}'. Supported: {', '.join(spec.tasks)}")
    prompt = _clean(req.prompt)
    if not prompt:
        raise MediaValidationError("Prompt / instruction cannot be empty.")
    if len(prompt) > spec.max_prompt:
        raise MediaValidationError(f"Prompt too long ({len(prompt)}). {spec.id} accepts up to {spec.max_prompt} chars.")
    if req.task == IMAGE_TASK_EDIT and not req.image_urls:
        raise MediaValidationError("Editing / reference generation needs at least one input image.")
    if req.image_urls and len(req.image_urls) > spec.max_input_images:
        raise MediaValidationError(f"{spec.id} accepts at most {spec.max_input_images} input image(s).")
    if req.image_urls and spec.dialect == "image_async":
        raise MediaValidationError(f"{spec.id} is text-to-image only; it cannot take input images.")
    if not (1 <= int(req.n) <= spec.max_n):
        raise MediaValidationError(f"{spec.id} generates 1–{spec.max_n} image(s) per call.")
    if req.size:
        size = req.size.strip()
        if size not in spec.sizes:
            wh = _parse_wh(size)
            if wh is None:
                raise MediaValidationError(f"Size '{size}' is not valid for {spec.id}. Try one of {', '.join(spec.sizes)}.")
            w, h = wh
            if not (256 <= w <= 4096 and 256 <= h <= 4096):
                raise MediaValidationError("Size must be between 256 and 4096 px per side.")
    return spec


def build_image_payload(req: ImageRequest) -> Tuple[str, Dict[str, Any], bool]:
    """Return ``(path, body, is_async)``."""
    spec = validate_image(req)
    prompt = _clean(req.prompt)
    negative = _clean(req.negative_prompt) if spec.negative_prompt else None
    size = (req.size or spec.default_size or "").strip() or None

    params: Dict[str, Any] = {}
    if size:
        params["size"] = size
    if spec.max_n > 1 or int(req.n) != 1:
        params["n"] = int(req.n)
    if negative:
        params["negative_prompt"] = negative
    if spec.prompt_extend and req.prompt_extend is not None:
        params["prompt_extend"] = bool(req.prompt_extend)
    if spec.watermark and req.watermark is not None:
        params["watermark"] = bool(req.watermark)
    if spec.seed and req.seed is not None:
        params["seed"] = int(req.seed)
    params.update(req.extra_parameters or {})

    if spec.dialect == "image_mm":
        content: List[Dict[str, str]] = [{"image": u} for u in req.image_urls]
        content.append({"text": prompt})
        body = {
            "model": spec.id,
            "input": {"messages": [{"role": "user", "content": content}]},
            "parameters": params,
        }
        return MULTIMODAL_PATH, body, False

    if spec.dialect == "image_async":
        inp: Dict[str, Any] = {"prompt": prompt}
        if negative:
            inp["negative_prompt"] = params.pop("negative_prompt")
        body = {"model": spec.id, "input": inp, "parameters": params}
        return TEXT2IMAGE_PATH, body, True

    raise MediaValidationError(f"Unknown image dialect {spec.dialect}")  # pragma: no cover


def extract_image_urls(response: Dict[str, Any]) -> List[str]:
    """Pull image URLs out of either a multimodal or a text2image response."""
    urls: List[str] = []
    out = response.get("output") or {}
    for choice in out.get("choices") or []:
        msg = choice.get("message") or {}
        for item in msg.get("content") or []:
            if isinstance(item, dict) and item.get("image"):
                urls.append(item["image"])
    for res in out.get("results") or []:
        if isinstance(res, dict) and res.get("url"):
            urls.append(res["url"])
    return urls


# --------------------------------------------------------------------- speech
@dataclass
class SpeechRequest:
    model: str
    text: str = ""
    voice: Optional[str] = None
    language: Optional[str] = None       # qwen: language_type
    instructions: Optional[str] = None   # style hint for instruct-capable models
    format: Optional[str] = None
    sample_rate: Optional[int] = None
    rate: Optional[float] = None         # speaking rate (cosyvoice)
    volume: Optional[int] = None
    extra_input: Dict[str, Any] = field(default_factory=dict)


def validate_speech(req: SpeechRequest) -> SpeechModelSpec:
    spec = get_speech_spec(req.model)
    text = _clean(req.text)
    if not text:
        raise MediaValidationError("Text to speak cannot be empty.")
    if len(text) > spec.max_chars:
        raise MediaValidationError(f"Text too long ({len(text)}). {spec.id} accepts up to {spec.max_chars} chars.")
    if req.format and req.format not in spec.formats:
        raise MediaValidationError(f"{spec.id} outputs {', '.join(spec.formats)}, not {req.format}.")
    if req.sample_rate and req.sample_rate not in spec.sample_rates:
        raise MediaValidationError(f"{spec.id} supports sample rates {spec.sample_rates}.")
    if req.instructions and not spec.instruct:
        raise MediaValidationError(f"{spec.id} does not support style instructions.")
    return spec


def build_speech_payload(req: SpeechRequest) -> Tuple[str, Dict[str, Any], bool]:
    spec = validate_speech(req)
    text = _clean(req.text)
    voice = _clean(req.voice) or spec.default_voice

    if spec.dialect == "tts_mm":
        inp: Dict[str, Any] = {"text": text, "voice": voice}
        lang = _clean(req.language)
        if lang:
            inp["language_type"] = lang
        if spec.instruct and _clean(req.instructions):
            inp["instructions"] = req.instructions.strip()
        inp.update(req.extra_input or {})
        return MULTIMODAL_PATH, {"model": spec.id, "input": inp}, False

    if spec.dialect == "tts_cosy":
        inp = {
            "text": text,
            "voice": voice,
            "format": req.format or spec.formats[0],
            "sample_rate": int(req.sample_rate or spec.sample_rates[0]),
        }
        if req.rate is not None:
            inp["rate"] = float(req.rate)
        if req.volume is not None:
            inp["volume"] = int(req.volume)
        if spec.instruct and _clean(req.instructions):
            inp["instruction"] = req.instructions.strip()
        inp.update(req.extra_input or {})
        return COSYVOICE_PATH, {"model": spec.id, "input": inp}, False

    raise MediaValidationError(f"Unknown speech dialect {spec.dialect}")  # pragma: no cover


def extract_audio_url(response: Dict[str, Any]) -> Optional[str]:
    out = response.get("output") or {}
    audio = out.get("audio") or {}
    if isinstance(audio, dict) and audio.get("url"):
        return audio["url"]
    return out.get("audio_url") or out.get("url")
