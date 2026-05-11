import pytest
from app.services.quiz_generator import generate_quizzes


def test_generate_quizzes_not_implemented():
    # TODO(phase1): LLM 구현 후 실제 퀴즈 생성 테스트 추가
    with pytest.raises(NotImplementedError):
        generate_quizzes("테스트 강의 텍스트")
