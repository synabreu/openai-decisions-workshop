# 테스트 조건에 따라 기능의 정상 동작과 오류 처리를 검증한다.
import unittest
from unittest.mock import patch
from server import analyze


# 관련 기능의 정상 처리와 오류 처리 조건을 묶어 검증한다.
class WebTests(unittest.TestCase):
    def test_mock_never_calls_api(self):
        # 고정 예제 모드에서 실제 API를 호출하지 않는지 확인한다.
        with patch('server.create_decision') as call:
            result = analyze({'mode': 'mock', 'text': 'ignored'})
            call.assert_not_called()
        self.assertEqual(result['workflow']['route'], 'MEDICAL_REVIEW')
        self.assertFalse(result['workflow']['executed'])

    def test_live_uses_input(self):
        # 실제 분석 모드가 전달받은 사고 내용을 사용하는지 확인한다.
        with patch('server.load_environment'), patch('server.create_decision', return_value={}) as call:
            result = analyze({'text': '가상 사고 접수'})
        self.assertEqual(call.call_args.args[0], '가상 사고 접수')
        self.assertEqual(result['workflow']['route'], 'HUMAN_REVIEW')

    def test_invalid_inputs(self):
        # 유효하지 않은 입력 형식과 범위를 거부하는지 확인한다.
        for payload in ({'text': ''}, {'text': 1}, {'text': 'x'*20001}, {'mode': 'bad'}, {'threshold': float('nan')}, {'threshold': True}):
            with self.subTest(payload=str(payload)[:60]), self.assertRaises(ValueError):
                analyze(payload)
