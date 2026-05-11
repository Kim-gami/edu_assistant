import json
import logging

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
당신은 강의 내용을 바탕으로 학습 퀴즈를 생성하는 교육 전문가입니다.
주어진 강의 텍스트의 핵심 개념을 파악해 4지선다 퀴즈를 만드세요.

규칙:
- 개념 이해를 측정하는 질문을 만드세요 (단순 암기 지양)
- 오답은 정답과 개념적으로 유사하되 명확히 틀린 선택지로 구성하세요
- explanation에는 정답 이유와 각 오답이 왜 틀렸는지 반드시 포함하세요
- 반드시 아래 JSON 형식만 출력하고 다른 텍스트는 절대 포함하지 마세요

출력 형식:
{
  "quizzes": [
    {
      "question": "질문",
      "type": "multiple_choice",
      "difficulty": "easy|medium|hard",
      "choices": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "answer": "A",
      "explanation": "정답 이유 및 오답 해설"
    }
  ]
}"""


def generate_quizzes(
    transcript_text: str,
    num_questions: int | None = None,
) -> list[dict]:
    """전사 텍스트를 받아 CLAUDE.md 스키마에 맞는 퀴즈 목록을 반환한다."""
    count = num_questions or settings.llm_quiz_count

    client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"다음 강의 내용으로 {count}개의 퀴즈를 생성하세요:\n\n{transcript_text}",
            },
        ],
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("LLM 응답 JSON 파싱 실패: %s\n응답: %.200s", exc, raw)
        raise

    quizzes = data.get("quizzes", [])
    logger.info("퀴즈 생성 완료: %d개", len(quizzes))
    return quizzes
