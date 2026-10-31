"""
Registry of the *non-video* Alibaba Cloud Model Studio AIGC models exposed by
Wan Gateway: image generation / editing and speech synthesis.

Video models live in :mod:`src.models`; this module follows the same idea —
one declarative spec per model, consumed by the builder, the UI and the CLI.

Image dialects
--------------
image_mm     Wan 2.6/2.7-image, Qwen-Image 2.x/3.x, Qwen-Image-Edit
             -> synchronous ``POST /api/v1/services/aigc/multimodal-generation/generation``
                with ``input.messages[0].content=[{text},{image}...]``;
                result in ``output.choices[0].message.content[*].image``.
image_async  Wan t2i V2 (wan2.6-t2i, wan2.5-t2i-preview, wan2.2-t2i-*, wanx2.1-t2i-*)
             -> asynchronous ``POST /api/v1/services/aigc/text2image/image-synthesis``
                (``X-DashScope-Async: enable``), poll ``GET /api/v1/tasks/{id}``;
                result in ``output.results[*].url``.

Speech dialects
---------------
tts_mm       Qwen3-TTS / Qwen-Audio-TTS
             -> ``POST /api/v1/services/aigc/multimodal-generation/generation``
                with ``input.text / input.voice / input.language_type``;
                result in ``output.audio.url``.
tts_cosy     CosyVoice v2 / v3 / v3.5 (non-realtime HTTP)
             -> ``POST /api/v1/services/audio/tts/SpeechSynthesizer`` with
                ``input.text / input.voice / input.format / input.sample_rate``;
                result in ``output.audio.url``.

Sources (Oct 2026): Model Studio "万相-图像生成与编辑2.7 API参考", "千问
Qwen-Image 图像生成与编辑 API", "千问 Qwen-Image-Edit API", "万相文本生成图像 V2
API参考", "非实时语音合成 Qwen-Audio-TTS/CosyVoice HTTP API参考", "语音合成 模型列表".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# --------------------------------------------------------------------- image
IMAGE_TASK_T2I = "t2i"      # text -> image
IMAGE_TASK_EDIT = "edit"    # image(s) + instruction -> image
IMAGE_TASKS = (IMAGE_TASK_T2I, IMAGE_TASK_EDIT)

IMAGE_TASK_LABELS = {
    IMAGE_TASK_T2I: "🖌️ Text → Image",
    IMAGE_TASK_EDIT: "✂️ Edit / Reference → Image",
}

# Discrete size menus shown in the UI.  Models that accept free W*H also accept
# anything typed by hand; the builder only checks the pixel budget.
SIZES_QWEN = ("1328*1328", "1664*928", "928*1664", "1472*1140", "1140*1472",
              "1584*1056", "1056*1584", "2048*2048")
SIZES_WAN_TIER = ("1K", "2K", "4K")
SIZES_WAN_FLEX = ("1280*1280", "1440*1440", "1664*1152", "1152*1664", "1920*1080", "1080*1920")
SIZES_WAN_22 = ("1024*1024", "1280*720", "720*1280", "1440*1440", "1440*810", "810*1440")


@dataclass(frozen=True)
class ImageModelSpec:
    id: str
    family: str
    vendor: str                       # "wan" | "qwen"
    tasks: Tuple[str, ...]
    dialect: str                      # image_mm | image_async
    sizes: Tuple[str, ...]
    default_size: Optional[str] = None  # None -> let the model choose
    max_n: int = 1
    max_prompt: int = 800
    max_input_images: int = 0
    negative_prompt: bool = True
    prompt_extend: bool = True
    seed: bool = True
    watermark: bool = True
    status: str = "stable"
    description: str = ""
    eta: str = "10-60 s"
    notes: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_hidden(self) -> bool:
        return self.status in ("legacy", "deprecated")

    @property
    def badge(self) -> str:
        return {"latest": "🆕", "stable": "✅", "legacy": "🕰️", "deprecated": "⚠️"}.get(self.status, "")

    def supports(self, task: str) -> bool:
        return task in self.tasks


_IMAGE_SPECS: List[ImageModelSpec] = [
    ImageModelSpec(
        id="wan2.7-image-pro", family="2.7", vendor="wan", tasks=IMAGE_TASKS, dialect="image_mm",
        sizes=SIZES_WAN_TIER, default_size="2K", max_n=4, max_prompt=5000, max_input_images=4,
        status="latest",
        description="Wan 2.7 Image Pro: text-to-image up to 4K, image sets, editing and multi-image "
                    "reference generation.",
        notes=("4K is text-to-image only; editing and image sets are capped at 2K.",),
    ),
    ImageModelSpec(
        id="wan2.7-image", family="2.7", vendor="wan", tasks=IMAGE_TASKS, dialect="image_mm",
        sizes=("1K", "2K"), default_size="2K", max_n=4, max_prompt=5000, max_input_images=4,
        status="stable",
        description="Wan 2.7 Image: same capabilities as Pro at 1K/2K, faster and cheaper.",
    ),
    ImageModelSpec(
        id="qwen-image-3.0-pro", family="3.0", vendor="qwen", tasks=IMAGE_TASKS, dialect="image_mm",
        sizes=SIZES_QWEN, default_size=None, max_n=1, max_prompt=5000, max_input_images=3,
        status="latest",
        description="Qwen-Image 3.0 Pro: flagship, best-in-class text rendering, identity-preserving "
                    "edits. Omit size to let it pick a resolution from the prompt.",
    ),
    ImageModelSpec(
        id="qwen-image-2.1-pro", family="2.1", vendor="qwen", tasks=IMAGE_TASKS, dialect="image_mm",
        sizes=SIZES_QWEN, default_size="1328*1328", max_n=1, max_prompt=5000, max_input_images=3,
        status="stable", description="Qwen-Image 2.1 Pro: high quality generation + editing.",
    ),
    ImageModelSpec(
        id="qwen-image-2.1-turbo", family="2.1", vendor="qwen", tasks=IMAGE_TASKS, dialect="image_mm",
        sizes=SIZES_QWEN, default_size="1328*1328", max_n=1, max_prompt=5000, max_input_images=3,
        status="stable", description="Qwen-Image 2.1 Turbo: fast generation + editing.", eta="5-20 s",
    ),
    ImageModelSpec(
        id="wan2.6-image", family="2.6", vendor="wan", tasks=(IMAGE_TASK_EDIT,), dialect="image_mm",
        sizes=SIZES_WAN_FLEX, default_size="1280*1280", max_n=4, max_prompt=5000, max_input_images=4,
        status="stable",
        description="Wan 2.6 Image: editing and mixed text+image output. For pure text-to-image "
                    "use wan2.6-t2i.",
    ),
    ImageModelSpec(
        id="wan2.6-t2i", family="2.6", vendor="wan", tasks=(IMAGE_TASK_T2I,), dialect="image_async",
        sizes=SIZES_WAN_FLEX, default_size="1280*1280", max_n=4, max_prompt=800,
        status="stable",
        description="Wan 2.6 text-to-image (async). Flexible W*H, 1280² – 1440² pixels, 1:4 – 4:1.",
    ),
    ImageModelSpec(
        id="qwen-image-2.0-pro", family="2.0", vendor="qwen", tasks=IMAGE_TASKS, dialect="image_mm",
        sizes=SIZES_QWEN, default_size="1328*1328", max_n=1, max_prompt=5000, max_input_images=3,
        status="legacy", description="Qwen-Image 2.0 Pro (superseded by 2.1 / 3.0).",
    ),
    ImageModelSpec(
        id="qwen-image-2.0", family="2.0", vendor="qwen", tasks=IMAGE_TASKS, dialect="image_mm",
        sizes=SIZES_QWEN, default_size="1328*1328", max_n=1, max_prompt=5000, max_input_images=3,
        status="legacy", description="Qwen-Image 2.0 (accelerated).",
    ),
    ImageModelSpec(
        id="qwen-image-edit-plus", family="1.0", vendor="qwen", tasks=(IMAGE_TASK_EDIT,), dialect="image_mm",
        sizes=SIZES_QWEN, default_size=None, max_n=1, max_prompt=800, max_input_images=3,
        status="legacy", description="Qwen-Image-Edit Plus: instruction-based editing (legacy).",
    ),
    ImageModelSpec(
        id="wan2.5-t2i-preview", family="2.5", vendor="wan", tasks=(IMAGE_TASK_T2I,), dialect="image_async",
        sizes=SIZES_WAN_FLEX, default_size="1280*1280", max_n=4, status="legacy",
        description="Wan 2.5 text-to-image preview (async).",
    ),
    ImageModelSpec(
        id="wan2.2-t2i-flash", family="2.2", vendor="wan", tasks=(IMAGE_TASK_T2I,), dialect="image_async",
        sizes=SIZES_WAN_22, default_size="1024*1024", max_n=4, status="legacy",
        description="Wan 2.2 text-to-image Flash (async, 512–1440 px per side).",
    ),
    ImageModelSpec(
        id="wan2.2-t2i-plus", family="2.2", vendor="wan", tasks=(IMAGE_TASK_T2I,), dialect="image_async",
        sizes=SIZES_WAN_22, default_size="1024*1024", max_n=4, status="legacy",
        description="Wan 2.2 text-to-image Plus (async).",
    ),
    ImageModelSpec(
        id="wanx2.1-t2i-turbo", family="2.1", vendor="wan", tasks=(IMAGE_TASK_T2I,), dialect="image_async",
        sizes=SIZES_WAN_22, default_size="1024*1024", max_n=4, status="deprecated",
        description="Wan 2.1 text-to-image Turbo (deprecated).",
    ),
    ImageModelSpec(
        id="wanx2.1-t2i-plus", family="2.1", vendor="wan", tasks=(IMAGE_TASK_T2I,), dialect="image_async",
        sizes=SIZES_WAN_22, default_size="1024*1024", max_n=4, status="deprecated",
        description="Wan 2.1 text-to-image Plus (deprecated).",
    ),
]

IMAGE_REGISTRY: Dict[str, ImageModelSpec] = {s.id: s for s in _IMAGE_SPECS}
DEFAULT_IMAGE_MODEL: Dict[str, str] = {IMAGE_TASK_T2I: "wan2.7-image-pro", IMAGE_TASK_EDIT: "qwen-image-3.0-pro"}


def get_image_spec(model_id: str) -> ImageModelSpec:
    try:
        return IMAGE_REGISTRY[model_id]
    except KeyError:
        raise ValueError(f"Unknown image model '{model_id}'. Known: {', '.join(IMAGE_REGISTRY)}") from None


def image_models_for_task(task: str, include_hidden: bool = False) -> List[ImageModelSpec]:
    return [s for s in _IMAGE_SPECS if s.supports(task) and (include_hidden or not s.is_hidden)]


def image_display_name(spec: ImageModelSpec) -> str:
    bits = [f"{spec.badge} {spec.id}", f"≤{spec.sizes[-1]}"]
    if spec.max_n > 1:
        bits.append(f"n≤{spec.max_n}")
    if IMAGE_TASK_EDIT in spec.tasks:
        bits.append("edit")
    return " · ".join(bits)


# -------------------------------------------------------------------- speech
@dataclass(frozen=True)
class SpeechModelSpec:
    id: str
    family: str
    dialect: str                       # tts_mm | tts_cosy
    voices: Tuple[str, ...]
    default_voice: str
    languages: Tuple[str, ...] = ("Auto",)
    formats: Tuple[str, ...] = ("mp3", "wav")
    sample_rates: Tuple[int, ...] = (24000,)
    max_chars: int = 600
    instruct: bool = False            # supports natural-language style instructions
    clone: bool = False               # accepts cloned voice ids
    status: str = "stable"
    description: str = ""

    @property
    def is_hidden(self) -> bool:
        return self.status in ("legacy", "deprecated")

    @property
    def badge(self) -> str:
        return {"latest": "🆕", "stable": "✅", "legacy": "🕰️", "deprecated": "⚠️"}.get(self.status, "")


QWEN_TTS_VOICES = ("Cherry", "Serena", "Ethan", "Chelsie", "Dylan", "Jada", "Sunny", "Momo",
                   "Vivian", "Ryan", "Katerina", "Elias", "Marcus", "Roy", "Peter", "Rocky", "Kiki", "Eric")
QWEN_TTS_LANGS = ("Auto", "Chinese", "English", "Japanese", "Korean", "German", "French",
                  "Russian", "Italian", "Spanish", "Portuguese")
COSY_VOICES = ("longanyang", "longanhuan", "longyingcui", "longxiaochun_v2", "longxiaoxia_v2",
               "longwan_v2", "longcheng_v2", "longhua_v2", "longshu_v2", "loongbella_v2",
               "longjielidou_v2", "longxiang_v2", "loongstella_v2")

_SPEECH_SPECS: List[SpeechModelSpec] = [
    SpeechModelSpec(
        id="qwen3-tts-flash", family="qwen3", dialect="tts_mm", voices=QWEN_TTS_VOICES,
        default_voice="Cherry", languages=QWEN_TTS_LANGS, formats=("wav",), max_chars=600,
        status="latest",
        description="Qwen3-TTS Flash: 49 voices, 10 languages + Chinese dialects, low latency.",
    ),
    SpeechModelSpec(
        id="qwen-audio-3.1-tts-plus", family="qwen-audio-3.1", dialect="tts_mm", voices=QWEN_TTS_VOICES,
        default_voice="Cherry", languages=QWEN_TTS_LANGS, formats=("wav",), max_chars=600, instruct=True,
        status="stable", description="Qwen-Audio 3.1 TTS Plus: expressive, instruction controllable.",
    ),
    SpeechModelSpec(
        id="qwen-audio-3.1-tts-flash", family="qwen-audio-3.1", dialect="tts_mm", voices=QWEN_TTS_VOICES,
        default_voice="Cherry", languages=QWEN_TTS_LANGS, formats=("wav",), max_chars=600, instruct=True,
        status="stable", description="Qwen-Audio 3.1 TTS Flash: fast expressive speech.",
    ),
    SpeechModelSpec(
        id="cosyvoice-v3.5-plus", family="cosyvoice-3.5", dialect="tts_cosy", voices=COSY_VOICES,
        default_voice="longanyang", formats=("mp3", "wav", "pcm"), sample_rates=(24000, 22050, 16000, 8000),
        max_chars=2000, instruct=True, clone=True, status="latest",
        description="CosyVoice 3.5 Plus: highest quality, instruction control, voice design, cloning.",
    ),
    SpeechModelSpec(
        id="cosyvoice-v3.5-flash", family="cosyvoice-3.5", dialect="tts_cosy", voices=COSY_VOICES,
        default_voice="longanyang", formats=("mp3", "wav", "pcm"), sample_rates=(24000, 22050, 16000, 8000),
        max_chars=2000, instruct=True, clone=True, status="stable",
        description="CosyVoice 3.5 Flash: fast, instruction control, cloning.",
    ),
    SpeechModelSpec(
        id="cosyvoice-v3-plus", family="cosyvoice-3", dialect="tts_cosy", voices=COSY_VOICES,
        default_voice="longanyang", formats=("mp3", "wav", "pcm"), sample_rates=(24000, 22050, 16000, 8000),
        max_chars=2000, clone=True, status="stable", description="CosyVoice 3 Plus: SSML, cloning.",
    ),
    SpeechModelSpec(
        id="cosyvoice-v3-flash", family="cosyvoice-3", dialect="tts_cosy", voices=COSY_VOICES,
        default_voice="longanyang", formats=("mp3", "wav", "pcm"), sample_rates=(24000, 22050, 16000, 8000),
        max_chars=2000, instruct=True, clone=True, status="stable",
        description="CosyVoice 3 Flash: fast, instruction control, cloning.",
    ),
    SpeechModelSpec(
        id="cosyvoice-v2", family="cosyvoice-2", dialect="tts_cosy", voices=COSY_VOICES,
        default_voice="longxiaochun_v2", formats=("mp3", "wav", "pcm"), sample_rates=(22050, 16000, 8000),
        max_chars=2000, clone=True, status="legacy", description="CosyVoice 2 (basic synthesis).",
    ),
]

SPEECH_REGISTRY: Dict[str, SpeechModelSpec] = {s.id: s for s in _SPEECH_SPECS}
DEFAULT_SPEECH_MODEL = "qwen3-tts-flash"


def get_speech_spec(model_id: str) -> SpeechModelSpec:
    try:
        return SPEECH_REGISTRY[model_id]
    except KeyError:
        raise ValueError(f"Unknown speech model '{model_id}'. Known: {', '.join(SPEECH_REGISTRY)}") from None


def speech_models(include_hidden: bool = False) -> List[SpeechModelSpec]:
    return [s for s in _SPEECH_SPECS if include_hidden or not s.is_hidden]


def speech_display_name(spec: SpeechModelSpec) -> str:
    bits = [f"{spec.badge} {spec.id}", f"{len(spec.voices)}+ voices"]
    if spec.instruct:
        bits.append("instruct")
    if spec.clone:
        bits.append("clone")
    return " · ".join(bits)


def id_from_display(label: str) -> str:
    """Strip the badge / suffix from a dropdown label (works for image + speech)."""
    if label in IMAGE_REGISTRY or label in SPEECH_REGISTRY:
        return label
    token = label.split(" · ")[0].strip()
    token = token.split(" ", 1)[-1] if " " in token else token
    return token
