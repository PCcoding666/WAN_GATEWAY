# Model matrix (Wan Gateway 2.1, Oct 2026)

## Video

Single source of truth: [`src/models.py`](../src/models.py). The UI, the CLI and
the request builder all read from it. `python cli.py models --all` prints the
live table.

| Model | Gen | Tasks | Resolution | Duration | fps | Audio | Multi-shot | Status |
|---|---|---|---|---|---|---|---|---|
| `wan3.0-video` | 3.0 | t2v · i2v · kf2v · r2v | 480P / 720P / 1080P | 2–30 s, or **smart (-1)** | 30 | ✅ | prompt-driven | 🆕 latest (default) |
| `wan2.7-t2v` | 2.7 | t2v | 720P / 1080P | 2–15 s | 30 | ✅ | – | ✅ stable |
| `wan2.7-i2v` | 2.7 | i2v · kf2v | 720P / 1080P | 2–15 s | 30 | ✅ | – | ✅ stable |
| `wan2.7-r2v` | 2.7 | r2v | 720P / 1080P | 2–10 s | 30 | ✅ | `shot_type` | ✅ stable |
| `wan2.7-videoedit` | 2.7 | vedit | 720P / 1080P | 2–10 s | 30 | ✅ | – | ✅ stable |
| `wan2.6-t2v` | 2.6 | t2v | 720P / 1080P | 2–15 s | 30 | ✅ | `shot_type` | ✅ stable |
| `wan2.6-i2v` | 2.6 | i2v | 720P / 1080P | 2–15 s | 30 | ✅ | `shot_type` | ✅ stable |
| `wan2.6-i2v-flash` | 2.6 | i2v | 720P / 1080P | 2–15 s | 30 | ✅ | `shot_type` | ✅ stable (fast) |
| `wan2.6-r2v` / `-flash` | 2.6 | r2v | 720P / 1080P | 2–10 s | 30 | ✅ | `shot_type` | ✅ stable |
| `wan2.5-t2v-preview` / `wan2.5-i2v-preview` | 2.5 | t2v / i2v | 480P / 720P / 1080P | 5 or 10 s | 24 | ✅ | – | 🕰️ legacy |
| `wan2.2-t2v-plus` | 2.2 | t2v | 480P / 1080P | 5 s | 30 | – | – | 🕰️ legacy |
| `wan2.2-i2v-flash` / `-plus` | 2.2 | i2v | 480P/720P · 480P/1080P | 5 s | 30 | – | – | 🕰️ legacy |
| `wan2.2-kf2v-flash` | 2.2 | kf2v | 480P / 720P / 1080P | 5 s | 30 | – | – | 🕰️ legacy |
| `wanx2.1-*` | 2.1 | t2v / i2v / kf2v | 480P–720P | 3–5 s | 30 | – | – | ⚠️ deprecated |

Legacy and deprecated models are hidden in the UI unless `WAN_SHOW_LEGACY=1` /
`WAN_SHOW_DEPRECATED=1` (or `python main.py --show-legacy`).

## Task names

| id | UI label | Inputs |
|---|---|---|
| `t2v` | 📝 Text → Video | prompt |
| `i2v` | 🖼️ Image → Video | prompt (optional) + first frame |
| `kf2v` | 🎞️ Keyframes → Video | prompt (optional) + first frame + last frame |
| `r2v` | 🎭 Reference → Video | prompt + reference images / clips / audio |
| `vedit` | ✂️ Edit Video | instruction + source video URL (+ reference images) |

## Request dialects

DashScope changed the payload shape between generations. The builder
([`src/request_builder.py`](../src/request_builder.py)) picks the right one:

| Dialect | Models | Media input | Size / resolution | Extras |
|---|---|---|---|---|
| `media` | wan3.0-video, wan2.7-* | `input.media=[{"type":"first_frame"\|"last_frame"\|"reference_image"\|"reference_video"\|"reference_audio","url":…}]` | `parameters.resolution="1080P"`, `parameters.ratio="16:9"\|…\|"adaptive"` | `duration` (-1 = smart on 3.0), `audio`, `shot_type` (r2v) |
| `label` | wan2.6-i2v*, wan2.5-*, wan2.2-i2v-* | `input.img_url` | `parameters.resolution="1080P"` | `duration`, `audio`, `input.audio_url`, `shot_type` (2.6) |
| `size` | wan2.6-t2v, wan2.2-t2v-plus, wanx2.1-t2v-* | – | `parameters.size="1920*1080"` | `duration`, `audio`, `shot_type` (2.6) |
| `kf2v` | wan2.2-kf2v-flash, wanx2.1-kf2v-plus | `input.first_frame_url`, `input.last_frame_url` | `parameters.resolution` | endpoint `…/image2video/video-synthesis` |
| `r2v` | wan2.6-r2v* | `input.reference_urls=[…]` | `parameters.size` | `duration`, `audio`, `shot_type` |

Common to all: `input.prompt`, `input.negative_prompt`, `parameters.prompt_extend`,
`parameters.seed`, `parameters.watermark`. Everything is submitted with
`X-DashScope-Async: enable` and polled at `GET /api/v1/tasks/{task_id}`.

Use **🔍 Preview request** in the UI (or `cli.py generate --dry-run`) to see the
exact JSON before it is sent. If Alibaba tweaks a field, fix it in
`src/models.py` / `src/request_builder.py` — nothing else needs to change.

## Image (`src/catalog.py`)

| Model | Vendor | Tasks | Sizes | n | Input images | Status |
|---|---|---|---|---|---|---|
| `wan2.7-image-pro` | Wan 2.7 | t2i · edit | 1K / 2K / **4K** (4K t2i only) | ≤4 | ≤4 | 🆕 latest (t2i default) |
| `wan2.7-image` | Wan 2.7 | t2i · edit | 1K / 2K | ≤4 | ≤4 | ✅ |
| `qwen-image-3.0-pro` | Qwen | t2i · edit | auto or 512²–2048² W*H | 1 | ≤3 | 🆕 latest (edit default) |
| `qwen-image-2.1-pro` / `-turbo` | Qwen | t2i · edit | W*H presets | 1 | ≤3 | ✅ |
| `wan2.6-image` | Wan 2.6 | edit | 1280²–1440² flex | ≤4 | ≤4 | ✅ |
| `wan2.6-t2i` | Wan 2.6 | t2i (async) | 1280²–1440² flex, 1:4–4:1 | ≤4 | – | ✅ |
| `qwen-image-2.0`, `qwen-image-2.0-pro`, `qwen-image-edit-plus` | Qwen | t2i · edit | W*H presets | 1 | ≤3 | 🕰️ legacy |
| `wan2.5-t2i-preview`, `wan2.2-t2i-flash/plus` | Wan | t2i (async) | 512–1440 px/side | ≤4 | – | 🕰️ legacy |
| `wanx2.1-t2i-turbo/plus` | Wan | t2i (async) | 512–1440 px/side | ≤4 | – | ⚠️ deprecated |

Dialects: `image_mm` = synchronous `POST /api/v1/services/aigc/multimodal-generation/generation` with
`input.messages[0].content=[{image},…,{text}]`, result in `output.choices[0].message.content[*].image`;
`image_async` = `POST /api/v1/services/aigc/text2image/image-synthesis` (`X-DashScope-Async: enable`),
poll `/api/v1/tasks/{id}`, result in `output.results[*].url`. Common `parameters`: `size`, `n`,
`negative_prompt`, `prompt_extend`, `watermark`, `seed`.

## Speech (`src/catalog.py`)

| Model | Dialect | Voices | Formats | Instruct | Clone | Status |
|---|---|---|---|---|---|---|
| `qwen3-tts-flash` | `tts_mm` | 49 (Cherry, Ethan, Serena…) · 10 languages | wav | – | – | 🆕 latest (default) |
| `qwen-audio-3.1-tts-plus` / `-flash` | `tts_mm` | Qwen voices | wav | ✅ | – | ✅ |
| `cosyvoice-v3.5-plus` / `-flash` | `tts_cosy` | longanyang, longanhuan, … + cloned ids | mp3 / wav / pcm | ✅ | ✅ | 🆕 / ✅ |
| `cosyvoice-v3-plus` / `-flash` | `tts_cosy` | same | mp3 / wav / pcm | flash only | ✅ | ✅ |
| `cosyvoice-v2` | `tts_cosy` | `*_v2` voices | mp3 / wav / pcm | – | ✅ | 🕰️ legacy |

Dialects: `tts_mm` = `POST /api/v1/services/aigc/multimodal-generation/generation` with
`input.text / voice / language_type`; `tts_cosy` = `POST /api/v1/services/audio/tts/SpeechSynthesizer`
with `input.text / voice / format / sample_rate (/ rate / volume / instruction)`. Both return
`output.audio.url` (valid 24 h). Realtime / streaming WebSocket endpoints are out of scope.

## Not integrated (yet)

Music generation and `wan2.2-animate-*` were not found as public Model Studio APIs at the time
of writing; virtual try-on / video-effect templates are model-specific extras not covered here.

## Sources

* Alibaba Cloud Model Studio — *Wan3.0 Video Generation API Reference*, *wan3.0-video model info*
* Alibaba Cloud Model Studio — *Wan2.7 Text-to-Video / Image-to-Video API Reference*
* Alibaba Cloud Model Studio — *Wan text-to-video / image-to-video API reference (2.1–2.6)*,
  *Wan2.6 reference-to-video API reference*, *Wan first-and-last-frame API reference (2.2)*
* Tongyi — *Wan2.6 系列模型正式发布*; Alibaba Cloud blog — *Wan3.0: 30-Second AI Video Generation from Any Input*
* Alibaba Cloud Model Studio — *万相-图像生成与编辑2.7 API参考*, *千问 Qwen-Image 图像生成与编辑 API*, *千问 Qwen-Image-Edit API*, *万相文本生成图像 V2 API参考*
* Alibaba Cloud Model Studio — *语音合成 模型列表*, *非实时语音合成 Qwen-Audio-TTS/CosyVoice HTTP API参考*, *Qwen-TTS API*
* Third-party references for `wan2.7-videoedit` (Novita, Comfy Router, Apifox) — official page not reachable from the build sandbox

Limits (duration ranges, resolutions) were cross-checked against several API
resellers because the official pages could not be fetched from the build
environment; treat the Model Studio console as authoritative for billing.
