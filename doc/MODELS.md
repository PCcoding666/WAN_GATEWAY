# Wan model matrix (as shipped in Wan Gateway 2.0, Oct 2026)

Single source of truth: [`src/models.py`](../src/models.py). The UI, the CLI and
the request builder all read from it. `python cli.py models --all` prints the
live table.

| Model | Gen | Tasks | Resolution | Duration | fps | Audio | Multi-shot | Status |
|---|---|---|---|---|---|---|---|---|
| `wan3.0-video` | 3.0 | t2v · i2v · kf2v · r2v | 480P / 720P / 1080P | 2–30 s, or **smart (-1)** | 30 | ✅ | prompt-driven | 🆕 latest (default) |
| `wan2.7-t2v` | 2.7 | t2v | 720P / 1080P | 2–15 s | 30 | ✅ | – | ✅ stable |
| `wan2.7-i2v` | 2.7 | i2v · kf2v | 720P / 1080P | 2–15 s | 30 | ✅ | – | ✅ stable |
| `wan2.7-r2v` | 2.7 | r2v | 720P / 1080P | 2–10 s | 30 | ✅ | `shot_type` | ✅ stable |
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

## Sources

* Alibaba Cloud Model Studio — *Wan3.0 Video Generation API Reference*, *wan3.0-video model info*
* Alibaba Cloud Model Studio — *Wan2.7 Text-to-Video / Image-to-Video API Reference*
* Alibaba Cloud Model Studio — *Wan text-to-video / image-to-video API reference (2.1–2.6)*,
  *Wan2.6 reference-to-video API reference*, *Wan first-and-last-frame API reference (2.2)*
* Tongyi — *Wan2.6 系列模型正式发布*; Alibaba Cloud blog — *Wan3.0: 30-Second AI Video Generation from Any Input*

Limits (duration ranges, resolutions) were cross-checked against several API
resellers because the official pages could not be fetched from the build
environment; treat the Model Studio console as authoritative for billing.
