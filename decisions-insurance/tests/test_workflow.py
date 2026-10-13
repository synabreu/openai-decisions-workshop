# 프로그램 소스명은 tests/test_workflow.py이다.
# 원본 작성자는 기존 소스에 명시되어 있지 않으며, 주석 작성자는 Codex이다.
# 원본 프로그램 버전은 명시되어 있지 않으며, 주석 문서 버전은 1.0이다.
# 고정 모의 응답으로 검토 경로 규칙과 잘못된 응답에 대한 처리 결과를 검증한다.
import copy
import json
from pathlib import Path
import unittest
from insurance.workflow import select_workflow


# 관련 기능의 정상 처리와 오류 처리 조건을 묶어 검증한다.
class WorkflowTests(unittest.TestCase):
    # 사고 접수 검토 경로의 정상 처리와 담당자 검토 전환 규칙을 검증한다.
    def setUp(self):
        # 각 테스트가 독립적으로 수정할 수 있도록 고정 모의 응답을 새로 읽는다.
        self.data = json.loads((Path(__file__).resolve().parents[1] / "examples/mock_response.json").read_text(encoding="utf-8"))

    def test_normal_medical(self):
        # 부상 검토가 필요한 예시가 의료 검토로 분류되고 실제 업무는 실행되지 않는지 확인한다.
        self.assertEqual(select_workflow(self.data)["route"], "MEDICAL_REVIEW")
        self.assertFalse(select_workflow(self.data)["executed"])

    def test_refusal_in_each_question(self):
        # 네 질문 중 어느 하나라도 응답을 거부하면 담당자 검토로 전환되는지 확인한다.
        for i in range(4):
            data = copy.deepcopy(self.data)
            data["answers"][i] = {"name": data["answers"][i]["name"], "type": "refusal"}
            self.assertEqual(select_workflow(data)["route"], "HUMAN_REVIEW")

    def test_missing_low_confidence_and_unknown(self):
        # 응답 누락, 낮거나 잘못된 신뢰도, 알 수 없는 경로가 담당자 검토로 전환되는지 확인한다.
        self.assertEqual(select_workflow({})["route"], "HUMAN_REVIEW")
        for value in (0.2, float("nan"), True, "0.9"):
            self.data["answers"][1]["confidence"] = value
            self.assertEqual(select_workflow(self.data)["route"], "HUMAN_REVIEW")
        self.data["answers"][1].update(confidence=0.9, choice="UNKNOWN")
        self.assertEqual(select_workflow(self.data)["route"], "HUMAN_REVIEW")

    def test_no_automatic_payment(self):
        # 자동 처리 후보의 신뢰도가 높아도 지급 승인 대신 담당자 검토를 제안하는지 확인한다.
        self.data["answers"][1].update(choice="AUTO_APPROVE", confidence=0.99)
        self.assertEqual(select_workflow(self.data)["route"], "HUMAN_REVIEW")

    def test_emergency_even_with_low_confidence(self):
        # 긴급 경로는 신뢰도가 임계값보다 낮아도 긴급 검토 제안을 유지하는지 확인한다.
        self.data["answers"][1].update(choice="EMERGENCY", confidence=0.5)
        self.assertEqual(select_workflow(self.data)["route"], "EMERGENCY")

    def test_duplicate(self):
        # 같은 이름의 질문 응답이 중복되면 담당자 검토로 전환되는지 확인한다.
        self.data["answers"].append(self.data["answers"][0])
        self.assertEqual(select_workflow(self.data)["route"], "HUMAN_REVIEW")
