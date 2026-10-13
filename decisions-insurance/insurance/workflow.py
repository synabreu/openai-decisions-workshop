# 파일명: insurance/workflow.py
# 설명: 사고 접수 내용과 Decisions API의 분석 결과를 기반으로 담당자가 검토할 경로를 제안한다.
# 작성자: 서진호
# 버전: v1.0

import math
from .questions import ROUTES


def probability(value):
    # BOOL을 제외한 유한한 정수 또는 실수가 0 이상 1 이하인지 확인한다.
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1


def select_workflow(result, threshold=0.80):
    # 질문 응답과 신뢰도 임계값을 검증한 뒤 담당자가 검토할 경로를 반환한다.
    # 긴급 경로를 우선하며 응답 오류나 자동 승인 후보는 담당자 검토로 전환한다.
    if not probability(threshold):
        raise ValueError("threshold는 0~1이어야 한다.")
    def manual(reason):
        # 담당자 검토가 필요한 사유를 받아 실제 업무를 실행하지 않은 결과를 구성한다.
        return {"route": "HUMAN_REVIEW", "action": "담당자 검토 필요", "reason": reason, "executed": False}

    # Decisions API 응답이 사전인지 확인한다.
    items = result.get("answers")
    if not isinstance(items, list):
        return manual("answers 누락 또는 잘못된 형식")

    # 질문 이름과 형식, 확률 또는 신뢰도를 검증하고 중복을 제거한다.
    answers = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            return manual("응답 이름 또는 형식 오류")
        if item["name"] in answers:
            return manual("질문 이름 중복")
        answers[item["name"]] = item

    # 질문 이름과 형식, 확률 또는 신뢰도를 검증하고 중복을 제거한다.
    expected = {"valid_insurance_claim": "predicate", "claim_route": "choice",
                "urgency": "score", "medical_attention_required": "predicate"}
    for name, kind in expected.items():
        answer = answers.get(name, {})
        if answer.get("type") != kind:
            return manual(f"{name}: 응답 거부, 누락 또는 형식 오류")
        field = "probability" if kind == "predicate" else "confidence"
        if not probability(answer.get(field)):
            return manual(f"{name}: 유효하지 않은 확률")

    # 검토 경로 선택과 신뢰도 임계값을 기반으로 담당자 검토 경로를 결정한다.
    route = answers["claim_route"]
    chosen = route.get("choice")
    if not isinstance(chosen, str) or chosen not in ROUTES:
        return manual("알 수 없는 처리 경로")
    if chosen == "EMERGENCY":
        return {"route": chosen, "action": ROUTES[chosen], "reason": "긴급 검토 제안", "executed": False}
    if route["confidence"] < threshold:
        return manual("경로 선택 신뢰도가 데모 임계값 미만")
    if chosen == "AUTO_APPROVE":
        return manual("자동 처리 후보도 이 데모에서는 지급 승인 없이 담당자가 검토")
    if chosen == "NORMAL_ADJUSTER" and answers["medical_attention_required"]["probability"] >= threshold:
        chosen = "MEDICAL_REVIEW"
    return {"route": chosen, "action": ROUTES[chosen], "reason": "검토 경로 제안", "executed": False}
