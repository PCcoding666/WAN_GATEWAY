#!/usr/bin/env python3
"""
Wan Gateway command line.

    python cli.py models [--task t2v|i2v|kf2v|r2v] [--all]
    python cli.py generate --model wan3.0-video --prompt "..." [options] [--dry-run] [--wait]
    python cli.py status <task_id> [--download]
    python cli.py history
    python cli.py image --model wan2.7-image-pro --prompt "..." [--image URL ...] [--size 2K] [--n 2] [--dry-run]
    python cli.py tts --model qwen3-tts-flash --text "..." [--voice Cherry] [--dry-run]
    python cli.py catalog            # every image / speech model

Everything goes through the same registry / request builder / client as the
web UI, so a payload that works here works there.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config  # noqa: E402
from src.history import HistoryEntry, history  # noqa: E402
from src.models import REGISTRY, TASKS, get_spec, models_for_task  # noqa: E402
from src.request_builder import GenerationRequest, RequestValidationError, build_payload  # noqa: E402
from src.catalog import (  # noqa: E402
    IMAGE_REGISTRY, IMAGE_TASK_EDIT, IMAGE_TASK_T2I, SPEECH_REGISTRY,
)
from src.media_builder import (  # noqa: E402
    ImageRequest, MediaValidationError, SpeechRequest, build_image_payload,
    build_speech_payload, extract_audio_url, extract_image_urls,
)


def cmd_models(args) -> int:
    specs = models_for_task(args.task, include_hidden=args.all) if args.task else [
        s for s in REGISTRY.values() if args.all or not s.is_hidden]
    print(f"{'model':<22}{'fam':<5}{'tasks':<18}{'res':<16}{'duration':<16}{'audio':<6}{'status'}")
    for s in specs:
        print(f"{s.id:<22}{s.family:<5}{','.join(s.tasks):<18}{'/'.join(s.resolutions):<16}"
              f"{s.duration_label:<16}{'yes' if s.audio else 'no':<6}{s.badge} {s.status}")
    return 0


def cmd_generate(args) -> int:
    req = GenerationRequest(
        model=args.model, task=args.task, prompt=args.prompt or "",
        negative_prompt=args.negative, resolution=args.resolution, ratio=args.ratio,
        duration=args.duration, audio=None if args.audio is None else args.audio,
        audio_url=args.audio_url, shot_type=args.shot_type,
        prompt_extend=None if args.prompt_extend is None else args.prompt_extend,
        seed=args.seed, watermark=args.watermark,
        first_frame_url=args.first_frame, last_frame_url=args.last_frame,
        reference_image_urls=args.ref_image or [], reference_video_urls=args.ref_video or [],
        reference_audio_urls=args.ref_audio or [],
    )
    try:
        payload = build_payload(req)
    except (RequestValidationError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.dry_run or Config.DRY_RUN:
        print("(dry run — not sent)", file=sys.stderr)
        return 0

    from src.wan_client import WanAPIError, WanClient
    client = WanClient()
    try:
        task_id = client.submit(payload, task=req.task)
    except WanAPIError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    history().add(HistoryEntry(task_id=task_id, model=req.model, task=req.task,
                               prompt=req.prompt or "", payload=payload))
    print(f"task_id: {task_id}", file=sys.stderr)
    if not args.wait:
        return 0
    st = client.wait(task_id, interval=args.interval,
                     on_tick=lambda s, t: print(f"  {s.status:<10}{int(t):>5}s", file=sys.stderr))
    return _finish(client, st, download=True)


def cmd_status(args) -> int:
    from src.wan_client import WanClient
    client = WanClient()
    st = client.status(args.task_id)
    return _finish(client, st, download=args.download)


def _finish(client, st, download: bool) -> int:
    out = {"task_id": st.task_id, "status": st.status, "video_url": st.video_url,
           "error": st.error_message, "usage": st.usage}
    if st.status == "SUCCEEDED" and st.video_url and download:
        out["local_path"] = client.download(st.video_url, st.task_id)
        history().update(st.task_id, status="SUCCEEDED", video_url=st.video_url,
                         local_path=out["local_path"])
    elif st.status in ("FAILED", "CANCELED"):
        history().update(st.task_id, status=st.status, error=st.error_message)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if st.status == "SUCCEEDED" else 1


def cmd_catalog(args) -> int:
    print("IMAGE")
    print(f"  {'model':<24}{'tasks':<10}{'sizes':<22}{'n':<4}{'status'}")
    for s in IMAGE_REGISTRY.values():
        if s.is_hidden and not args.all:
            continue
        print(f"  {s.id:<24}{','.join(s.tasks):<10}{s.sizes[0] + '…' + s.sizes[-1]:<22}{s.max_n:<4}{s.badge} {s.status}")
    print("SPEECH")
    print(f"  {'model':<24}{'voices':<8}{'formats':<14}{'instruct':<10}{'status'}")
    for s in SPEECH_REGISTRY.values():
        if s.is_hidden and not args.all:
            continue
        print(f"  {s.id:<24}{len(s.voices):<8}{'/'.join(s.formats):<14}{'yes' if s.instruct else 'no':<10}{s.badge} {s.status}")
    return 0


def cmd_image(args) -> int:
    req = ImageRequest(
        model=args.model, task=IMAGE_TASK_EDIT if args.image else IMAGE_TASK_T2I,
        prompt=args.prompt or "", negative_prompt=args.negative, size=args.size, n=args.n,
        seed=args.seed, prompt_extend=args.prompt_extend, watermark=args.watermark,
        image_urls=args.image or [],
    )
    try:
        path, body, is_async = build_image_payload(req)
    except (MediaValidationError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"path": path, "async": is_async, "body": body}, ensure_ascii=False, indent=2))
    if args.dry_run or Config.DRY_RUN:
        print("(dry run — not sent)", file=sys.stderr)
        return 0
    from src.wan_client import WanAPIError, WanClient
    client = WanClient()
    try:
        if is_async:
            task_id = client.submit_async(path, body)
            print(f"task_id: {task_id}", file=sys.stderr)
            st = client.wait(task_id, interval=3)
            if st.status != "SUCCEEDED":
                print(f"error: {st.status}: {st.error_message}", file=sys.stderr)
                return 1
            urls = extract_image_urls(st.raw)
        else:
            urls = extract_image_urls(client.call_sync(path, body))
    except WanAPIError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    out = []
    for i, u in enumerate(urls):
        local = client.download_file(u, f"img_{int(__import__('time').time())}_{i}", Config.IMAGE_DIR, ".png") if args.download else None
        out.append({"url": u, "local_path": local})
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if urls else 1


def cmd_tts(args) -> int:
    req = SpeechRequest(model=args.model, text=args.text or "", voice=args.voice, language=args.language,
                        instructions=args.instructions, format=args.format, sample_rate=args.sample_rate,
                        rate=args.rate)
    try:
        path, body, _ = build_speech_payload(req)
    except (MediaValidationError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"path": path, "body": body}, ensure_ascii=False, indent=2))
    if args.dry_run or Config.DRY_RUN:
        print("(dry run — not sent)", file=sys.stderr)
        return 0
    from src.wan_client import WanAPIError, WanClient
    client = WanClient()
    try:
        url = extract_audio_url(client.call_sync(path, body))
    except WanAPIError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    local = client.download_file(url, f"tts_{int(__import__('time').time())}", Config.AUDIO_DIR, ".wav") if (url and args.download) else None
    print(json.dumps({"url": url, "local_path": local}, ensure_ascii=False, indent=2))
    return 0 if url else 1


def cmd_history(args) -> int:
    for row in history().as_rows(args.n):
        print("  ".join(str(c) for c in row))
    return 0


def _bool(v: str) -> bool:
    return v.lower() in ("1", "true", "yes", "on")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="wan", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("models", help="list models")
    m.add_argument("--task", choices=TASKS)
    m.add_argument("--all", action="store_true", help="include legacy / deprecated")
    m.set_defaults(fn=cmd_models)

    g = sub.add_parser("generate", help="submit a generation task")
    g.add_argument("--model", default=Config.DEFAULT_MODEL)
    g.add_argument("--task", choices=TASKS, default="t2v")
    g.add_argument("--prompt", "-p")
    g.add_argument("--negative")
    g.add_argument("--resolution", choices=["480P", "720P", "1080P"])
    g.add_argument("--ratio")
    g.add_argument("--duration", type=int, help="seconds; -1 = smart (Wan 3.0)")
    g.add_argument("--audio", type=_bool)
    g.add_argument("--audio-url")
    g.add_argument("--shot-type", choices=["single", "multi"])
    g.add_argument("--prompt-extend", type=_bool)
    g.add_argument("--seed", type=int)
    g.add_argument("--watermark", type=_bool)
    g.add_argument("--first-frame", help="public image URL")
    g.add_argument("--last-frame", help="public image URL")
    g.add_argument("--ref-image", action="append")
    g.add_argument("--ref-video", action="append")
    g.add_argument("--ref-audio", action="append")
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--wait", action="store_true", help="poll until finished and download")
    g.add_argument("--interval", type=float, default=5.0)
    g.set_defaults(fn=cmd_generate)

    s = sub.add_parser("status", help="query a task")
    s.add_argument("task_id")
    s.add_argument("--download", action="store_true")
    s.set_defaults(fn=cmd_status)

    c = sub.add_parser("catalog", help="list image / speech models")
    c.add_argument("--all", action="store_true")
    c.set_defaults(fn=cmd_catalog)

    im = sub.add_parser("image", help="generate or edit an image")
    im.add_argument("--model", default=Config.DEFAULT_IMAGE_MODEL)
    im.add_argument("--prompt", "-p")
    im.add_argument("--negative")
    im.add_argument("--size", help='e.g. 1328*1328 or 2K; omit for model default')
    im.add_argument("--n", type=int, default=1)
    im.add_argument("--seed", type=int)
    im.add_argument("--prompt-extend", type=_bool)
    im.add_argument("--watermark", type=_bool)
    im.add_argument("--image", action="append", help="input image URL (repeatable) -> edit / reference mode")
    im.add_argument("--download", action="store_true")
    im.add_argument("--dry-run", action="store_true")
    im.set_defaults(fn=cmd_image)

    t = sub.add_parser("tts", help="text to speech")
    t.add_argument("--model", default=Config.DEFAULT_SPEECH_MODEL)
    t.add_argument("--text")
    t.add_argument("--voice")
    t.add_argument("--language", help="qwen3-tts: Auto / Chinese / English / ...")
    t.add_argument("--instructions", help="style hint for instruct-capable models")
    t.add_argument("--format")
    t.add_argument("--sample-rate", type=int)
    t.add_argument("--rate", type=float)
    t.add_argument("--download", action="store_true")
    t.add_argument("--dry-run", action="store_true")
    t.set_defaults(fn=cmd_tts)

    h = sub.add_parser("history", help="recent tasks")
    h.add_argument("-n", type=int, default=20)
    h.set_defaults(fn=cmd_history)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
