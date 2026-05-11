# TODO(phase1): 임베딩 기반 노이즈 제거 구현
# 전략: 각 세그먼트를 임베딩 → 강의 핵심 토픽과 cosine similarity → top-k 이하 세그먼트 제거


def remove_noise(segments: list[dict]) -> list[dict]:
    """인트로/아웃트로/잡담 세그먼트를 필터링하고 강의 본문 세그먼트만 반환한다."""
    # TODO(phase1): 임베딩 모델 로드 후 구현
    return segments
