import json
import logging
import re

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
당신은 강의 내용을 바탕으로 고품질 학습 퀴즈를 생성하는 교육 전문가입니다.
강의 텍스트는 [섹션 X/N] 태그로 균등하게 나뉘어 제공됩니다.

문제 작성 규칙:
- 각 섹션에서 정확히 1개의 문제를 출제하세요 (섹션을 건너뛰거나 중복 금지)
- 해당 섹션의 핵심 개념·원리·인과관계를 묻는 문제를 만드세요 (단순 용어 정의 암기 금지)
- 질문만 읽어도 어떤 개념을 테스트하는지 명확해야 합니다

오답 선택지 규칙:
- 오답은 강의 내용을 잘못 이해했을 때 그럴듯하게 고를 수 있어야 합니다
- 강의를 몰라도 상식적으로 틀렸다고 바로 알 수 있는 선택지는 사용하지 마세요
- 정답과 오답은 형식(길이·문체)이 일관되어야 합니다

해설(explanation) 규칙:
- 정답이 왜 맞는지 근거를 제시하세요
- 각 오답(A·B·C·D)이 왜 틀렸는지 구체적으로 한 문장씩 설명하세요
- "틀렸습니다" "사실이 아닙니다" 처럼 단순 부정은 금지합니다

반드시 아래 JSON 형식만 출력하고 다른 텍스트는 절대 포함하지 마세요:
{
  "quizzes": [
    {
      "question": "질문",
      "type": "multiple_choice",
      "difficulty": "easy|medium|hard",
      "choices": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "answer": "A",
      "explanation": "정답 근거 + 각 오답이 왜 틀렸는지"
    }
  ]
}"""


def _split_into_sections(text: str, n: int) -> str:
    """문장 경계 기준으로 텍스트를 n개 섹션으로 나눠 [섹션 X/N] 태그를 붙여 반환한다."""
    # 마침표/물음표/느낌표 뒤 공백을 기준으로 문장 분리
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]

    if len(sentences) < n:
        # 문장 수가 섹션 수보다 적으면 글자 기준으로 분리
        size = max(1, len(text) // n)
        parts = [text[i * size: len(text) if i == n - 1 else (i + 1) * size].strip() for i in range(n)]
    else:
        # 문장을 n개 그룹으로 균등 배분
        group = max(1, len(sentences) // n)
        parts = []
        for i in range(n):
            start = i * group
            end = len(sentences) if i == n - 1 else (i + 1) * group
            parts.append(" ".join(sentences[start:end]))

    return "\n\n".join(
        f"[섹션 {i + 1}/{n}]\n{part}" for i, part in enumerate(parts) if part
    )


def generate_quizzes(
    transcript_text: str,
    num_questions: int | None = None,
) -> list[dict]:
    """전사 텍스트를 받아 CLAUDE.md 스키마에 맞는 퀴즈 목록을 반환한다."""
    count = num_questions or settings.llm_quiz_count
    sectioned = _split_into_sections(transcript_text, count)

    client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"아래 강의는 {count}개 섹션으로 나뉘어 있습니다. "
                    f"각 섹션에서 1개씩 총 {count}개의 퀴즈를 생성하세요:\n\n{sectioned}"
                ),
            },
        ],
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        response_format={"type": "json_object"},
        extra_body={"options": {"num_ctx": 8192}},
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
