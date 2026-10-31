import pytest

from src.catalog import (
    IMAGE_REGISTRY, IMAGE_TASK_EDIT, IMAGE_TASK_T2I, SPEECH_REGISTRY, get_image_spec,
    id_from_display, image_display_name, image_models_for_task, speech_display_name,
    speech_models,
)
from src.media_builder import (
    COSYVOICE_PATH, MULTIMODAL_PATH, TEXT2IMAGE_PATH, ImageRequest, MediaValidationError,
    SpeechRequest, build_image_payload, build_speech_payload, extract_audio_url,
    extract_image_urls,
)
from src.models import VEDIT
from src.request_builder import GenerationRequest, RequestValidationError, build_payload


class TestCatalog:
    def test_latest_present(self):
        for mid in ("wan2.7-image-pro", "wan2.7-image", "qwen-image-3.0-pro", "wan2.6-t2i"):
            assert mid in IMAGE_REGISTRY
        for mid in ("qwen3-tts-flash", "cosyvoice-v3.5-plus", "cosyvoice-v3-flash"):
            assert mid in SPEECH_REGISTRY

    def test_hidden_filter(self):
        ids = [s.id for s in image_models_for_task(IMAGE_TASK_T2I)]
        assert ids[0] == "wan2.7-image-pro"
        assert "wan2.2-t2i-flash" not in ids
        assert "wan2.2-t2i-flash" in [s.id for s in image_models_for_task(IMAGE_TASK_T2I, include_hidden=True)]
        assert "cosyvoice-v2" not in [s.id for s in speech_models()]

    def test_display_roundtrip(self):
        for s in IMAGE_REGISTRY.values():
            assert id_from_display(image_display_name(s)) == s.id
        for s in SPEECH_REGISTRY.values():
            assert id_from_display(speech_display_name(s)) == s.id


class TestImagePayload:
    def test_wan27_t2i(self):
        path, body, is_async = build_image_payload(ImageRequest(model="wan2.7-image-pro", prompt="a fox", n=2,
                                                                size="4K", watermark=False))
        assert path == MULTIMODAL_PATH and is_async is False
        assert body["input"]["messages"][0]["content"] == [{"text": "a fox"}]
        assert body["parameters"] == {"size": "4K", "n": 2, "watermark": False}

    def test_qwen_edit_with_images(self):
        path, body, _ = build_image_payload(ImageRequest(
            model="qwen-image-3.0-pro", task=IMAGE_TASK_EDIT, prompt="make it night",
            image_urls=["https://x/a.png", "https://x/b.png"], prompt_extend=True))
        content = body["input"]["messages"][0]["content"]
        assert content[:2] == [{"image": "https://x/a.png"}, {"image": "https://x/b.png"}]
        assert content[-1] == {"text": "make it night"}
        assert "size" not in body["parameters"]           # qwen 3.0 auto-size
        assert body["parameters"]["prompt_extend"] is True

    def test_wan26_t2i_async(self):
        path, body, is_async = build_image_payload(ImageRequest(
            model="wan2.6-t2i", prompt="a fox", negative_prompt="blur", size="1440*1440", seed=7))
        assert path == TEXT2IMAGE_PATH and is_async is True
        assert body["input"] == {"prompt": "a fox", "negative_prompt": "blur"}
        assert body["parameters"] == {"size": "1440*1440", "n": 1, "seed": 7}

    def test_edit_requires_image(self):
        with pytest.raises(MediaValidationError):
            build_image_payload(ImageRequest(model="qwen-image-3.0-pro", task=IMAGE_TASK_EDIT, prompt="x"))

    def test_async_model_rejects_images(self):
        with pytest.raises(MediaValidationError):
            build_image_payload(ImageRequest(model="wan2.6-t2i", prompt="x", image_urls=["u"]))

    def test_n_cap(self):
        with pytest.raises(MediaValidationError):
            build_image_payload(ImageRequest(model="qwen-image-3.0-pro", prompt="x", n=2))

    def test_free_size_accepted(self):
        _, body, _ = build_image_payload(ImageRequest(model="qwen-image-2.1-pro", prompt="x", size="1200*800"))
        assert body["parameters"]["size"] == "1200*800"
        with pytest.raises(MediaValidationError):
            build_image_payload(ImageRequest(model="qwen-image-2.1-pro", prompt="x", size="huge"))

    def test_extract_urls(self):
        assert extract_image_urls({"output": {"choices": [{"message": {"content": [{"image": "u1"}, {"text": "hi"}]}}]}}) == ["u1"]
        assert extract_image_urls({"output": {"results": [{"url": "u2"}, {"url": "u3"}]}}) == ["u2", "u3"]
        assert extract_image_urls({}) == []


class TestSpeechPayload:
    def test_qwen3_tts(self):
        path, body, _ = build_speech_payload(SpeechRequest(model="qwen3-tts-flash", text="你好", voice="Ethan",
                                                           language="Chinese"))
        assert path == MULTIMODAL_PATH
        assert body == {"model": "qwen3-tts-flash", "input": {"text": "你好", "voice": "Ethan", "language_type": "Chinese"}}

    def test_cosyvoice(self):
        path, body, _ = build_speech_payload(SpeechRequest(model="cosyvoice-v3-flash", text="hi", format="mp3",
                                                           sample_rate=22050, rate=1.2, instructions="whisper"))
        assert path == COSYVOICE_PATH
        assert body["input"] == {"text": "hi", "voice": "longanyang", "format": "mp3", "sample_rate": 22050,
                                 "rate": 1.2, "instruction": "whisper"}

    def test_instruct_rejected_on_basic_model(self):
        with pytest.raises(MediaValidationError):
            build_speech_payload(SpeechRequest(model="qwen3-tts-flash", text="hi", instructions="sad"))

    def test_bad_format(self):
        with pytest.raises(MediaValidationError):
            build_speech_payload(SpeechRequest(model="qwen3-tts-flash", text="hi", format="ogg"))

    def test_extract_audio(self):
        assert extract_audio_url({"output": {"audio": {"url": "a"}}}) == "a"
        assert extract_audio_url({"output": {}}) is None


class TestVideoEdit:
    def test_wan27_videoedit(self):
        p = build_payload(GenerationRequest(model="wan2.7-videoedit", task=VEDIT, prompt="anime style",
                                            input_video_url="https://x/v.mp4",
                                            reference_image_urls=["https://x/r.png"], duration=6))
        assert p["input"]["media"] == [{"type": "video", "url": "https://x/v.mp4"},
                                       {"type": "reference_image", "url": "https://x/r.png"}]
        assert p["parameters"]["duration"] == 6

    def test_wan30_edit_uses_reference_video(self):
        p = build_payload(GenerationRequest(model="wan3.0-video", task=VEDIT, prompt="winter",
                                            input_video_url="https://x/v.mp4"))
        assert p["input"]["media"] == [{"type": "reference_video", "url": "https://x/v.mp4"}]

    def test_requires_video_and_prompt(self):
        with pytest.raises(RequestValidationError):
            build_payload(GenerationRequest(model="wan2.7-videoedit", task=VEDIT, prompt="x"))
        with pytest.raises(RequestValidationError):
            build_payload(GenerationRequest(model="wan2.7-videoedit", task=VEDIT, input_video_url="u"))
        with pytest.raises(RequestValidationError):
            build_payload(GenerationRequest(model="wan2.7-videoedit", task=VEDIT, prompt="x",
                                            input_video_url="u", duration=15))
