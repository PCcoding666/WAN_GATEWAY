import pytest

from src.models import (
    I2V, KF2V, R2V, T2V, REGISTRY, display_name, get_spec, model_id_from_display,
    model_ids_for_task, size_for,
)
from src.request_builder import (
    GenerationRequest, RequestValidationError, build_payload, billable_seconds,
)


class TestRegistry:
    def test_latest_models_present(self):
        for mid in ("wan3.0-video", "wan2.7-t2v", "wan2.7-i2v", "wan2.7-r2v",
                    "wan2.6-t2v", "wan2.6-i2v", "wan2.6-i2v-flash"):
            assert mid in REGISTRY

    def test_default_models_hidden_legacy(self):
        visible = model_ids_for_task(T2V)
        assert visible[0] == "wan3.0-video"
        assert "wan2.2-t2v-plus" not in visible
        assert "wan2.2-t2v-plus" in model_ids_for_task(T2V, include_hidden=True)

    def test_display_roundtrip(self):
        for spec in REGISTRY.values():
            assert model_id_from_display(display_name(spec)) == spec.id
        assert model_id_from_display("wan2.7-t2v") == "wan2.7-t2v"

    def test_size_table(self):
        assert size_for("1080P", "16:9") == "1920*1080"
        assert size_for("720P", "9:16") == "720*1280"
        assert size_for("480P", "1:1") == "624*624"

    def test_clamp_duration(self):
        s = get_spec("wan2.5-t2v-preview")
        assert s.clamp_duration(7) == 5
        assert s.clamp_duration(9) == 10
        assert get_spec("wan3.0-video").clamp_duration(-1) == -1
        assert get_spec("wan2.7-t2v").clamp_duration(99) == 15


class TestBuildPayload:
    def test_wan30_text(self):
        p = build_payload(GenerationRequest(model="wan3.0-video", prompt="a cat",
                                            duration=-1, ratio="adaptive"))
        assert p["model"] == "wan3.0-video"
        assert p["input"] == {"prompt": "a cat"}
        assert p["parameters"]["duration"] == -1
        assert p["parameters"]["ratio"] == "adaptive"
        assert p["parameters"]["resolution"] == "1080P"
        assert p["parameters"]["audio"] is True

    def test_wan30_keyframes_media(self):
        p = build_payload(GenerationRequest(
            model="wan3.0-video", task=KF2V, prompt="x",
            first_frame_url="https://a/1.png", last_frame_url="https://a/2.png", duration=12))
        assert p["input"]["media"] == [
            {"type": "first_frame", "url": "https://a/1.png"},
            {"type": "last_frame", "url": "https://a/2.png"},
        ]
        assert p["parameters"]["duration"] == 12

    def test_wan30_keyframes_rejects_reference_audio(self):
        with pytest.raises(RequestValidationError):
            build_payload(GenerationRequest(
                model="wan3.0-video", task=KF2V, first_frame_url="u1", last_frame_url="u2",
                reference_audio_urls=["https://a/v.mp3"]))

    def test_wan27_r2v(self):
        p = build_payload(GenerationRequest(
            model="wan2.7-r2v", task=R2V, prompt="dance",
            reference_image_urls=["https://a/c.png"], reference_video_urls=["https://a/v.mp4"],
            shot_type="multi", duration=8))
        types = [m["type"] for m in p["input"]["media"]]
        assert types == ["reference_image", "reference_video"]
        assert p["parameters"]["shot_type"] == "multi"
        assert p["parameters"]["duration"] == 8

    def test_wan27_r2v_duration_cap(self):
        with pytest.raises(RequestValidationError):
            build_payload(GenerationRequest(model="wan2.7-r2v", task=R2V,
                                            reference_image_urls=["u"], duration=15))

    def test_wan26_t2v_size_dialect(self):
        p = build_payload(GenerationRequest(model="wan2.6-t2v", prompt="x", resolution="1080P",
                                            ratio="9:16", duration=15, shot_type="multi",
                                            audio_url="https://a/bgm.mp3"))
        assert p["parameters"]["size"] == "1080*1920"
        assert "resolution" not in p["parameters"]
        assert p["parameters"]["shot_type"] == "multi"
        assert p["input"]["audio_url"] == "https://a/bgm.mp3"

    def test_wan26_i2v_label_dialect(self):
        p = build_payload(GenerationRequest(model="wan2.6-i2v-flash", task=I2V, prompt="",
                                            first_frame_url="https://a/1.png", duration=3))
        assert p["input"]["img_url"] == "https://a/1.png"
        assert "prompt" not in p["input"]
        assert p["parameters"]["resolution"] == "1080P"
        assert p["parameters"]["duration"] == 3

    def test_wan26_r2v_reference_urls(self):
        p = build_payload(GenerationRequest(model="wan2.6-r2v", task=R2V, prompt="x",
                                            reference_image_urls=["u1"], reference_video_urls=["u2"]))
        assert p["input"]["reference_urls"] == ["u1", "u2"]
        assert p["parameters"]["size"] == "1920*1080"

    def test_wan25_legacy(self):
        p = build_payload(GenerationRequest(model="wan2.5-t2v-preview", prompt="x", duration=10,
                                            audio=False))
        assert p["parameters"] == {"resolution": "1080P", "duration": 10, "audio": False}

    def test_wan22_silent_no_audio_key(self):
        p = build_payload(GenerationRequest(model="wan2.2-t2v-plus", prompt="x", seed=42,
                                            negative_prompt="blurry", prompt_extend=False))
        assert p["parameters"] == {"size": "1920*1080", "prompt_extend": False, "seed": 42}
        assert p["input"]["negative_prompt"] == "blurry"

    def test_kf2v_legacy_dialect(self):
        p = build_payload(GenerationRequest(model="wan2.2-kf2v-flash", task=KF2V,
                                            first_frame_url="u1", last_frame_url="u2"))
        assert p["input"] == {"first_frame_url": "u1", "last_frame_url": "u2"}
        assert p["parameters"] == {"resolution": "1080P"}

    def test_task_not_supported(self):
        with pytest.raises(RequestValidationError):
            build_payload(GenerationRequest(model="wan2.7-t2v", task=I2V, first_frame_url="u"))

    def test_prompt_required_for_t2v(self):
        with pytest.raises(RequestValidationError):
            build_payload(GenerationRequest(model="wan3.0-video", prompt="   "))

    def test_prompt_too_long(self):
        with pytest.raises(RequestValidationError):
            build_payload(GenerationRequest(model="wan2.2-t2v-plus", prompt="x" * 801))

    def test_bad_resolution(self):
        with pytest.raises(RequestValidationError):
            build_payload(GenerationRequest(model="wan2.7-t2v", prompt="x", resolution="480P"))

    def test_extra_parameters_passthrough(self):
        p = build_payload(GenerationRequest(model="wan3.0-video", prompt="x",
                                            extra_parameters={"foo": "bar"}))
        assert p["parameters"]["foo"] == "bar"

    def test_billable_seconds(self):
        assert billable_seconds(GenerationRequest(model="wan2.7-t2v", duration=7)) == 7
        assert billable_seconds(GenerationRequest(model="wan3.0-video", duration=-1)) is None
