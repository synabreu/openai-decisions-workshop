# 프로젝트 이름: OpenAI Descisions API (3) - Score API
# 설명: 예제3 - 평가 기준에 따라 점수 매기는 Score API 사용

import config  # 사용이 승인된 기존 키를 복사하지 않고 읽는다.
from openai import OpenAI

def main():
    # 고정된 문제 설명을 실제 API로 채점하고 점수 또는 판단 거부를 출력한다.
    # 요청 시간이 무한정 늘어나지 않도록 제한하고 사용이 끝나면 API 클라이언트를 닫는다.
    with OpenAI(timeout=45, max_retries=0) as client:
        # 화면의 증거와 평가 기준을 실제 Decisions API로 전달한다.
        decision = client.decisions.create(
            model="gpt-6-luna",
            input="Export fails in Safari but works in Chrome.",
            questions=[{
                "type": "score",
                "name": "severity",
                "instructions": "How severe is this issue?",
                "levels": [
                    {"label": "Cosmetic", "description": "Appearance only; no lost functionality."},
                    {"label": "Workaround available", "description": "A task fails, but another way works."},
                    {"label": "Fully blocked", "description": "A task fails with no workaround."},
                ],
            }],
        )
    # 반환된 첫 판단의 형식과 점수를 확인할 준비를 한다.
    answer = decision.answers[0]
    # API 응답의 선택지와 확률이 정의된 범위 내에 있는지 확인
    if answer.type == "refusal":
        print(f"Refused: {answer.name}")
    elif answer.type == "score":
        print(f"Severity: {answer.score} (confidence: {answer.confidence})")

# 파일을 직접 실행한 경우에만 서버나 콘솔 작업을 시작한다.
if __name__ == '__main__':
    main()
