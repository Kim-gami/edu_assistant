from app.services.preprocessor import remove_noise


def test_remove_noise_passthrough():
    # TODO(phase1): 임베딩 구현 후 실제 필터링 테스트 추가
    segments = [{"start": 0.0, "end": 1.0, "text": "강의 본문"}]
    assert remove_noise(segments) == segments
