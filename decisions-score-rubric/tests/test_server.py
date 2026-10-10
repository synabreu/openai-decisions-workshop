# 테스트 조건에 따라 기능의 정상 동작과 오류 처리를 검증한다.
import unittest
from unittest.mock import patch, MagicMock
from server import app

# 관련 기능의 정상 처리와 오류 처리 조건을 묶어 검증한다.
class ServerTests(unittest.TestCase):
    def setUp(self):
        # 각 테스트가 독립적으로 실행되도록 클라이언트 또는 예제 상태를 준비한다.
        self.client = app.test_client()

    def test_only_demo_is_served(self):
        # 현재 데모를 제공하고 이전 주소를 데모로 연결하는지 확인한다.
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'id="playback"', response.data)
        self.assertNotIn(b'<iframe', response.data)
        for url in ['/playground', '/playground/', '/api/docs/guides/decisions', '/api/docs/guides/decisions/', '/static/official/index.html', '/static/original.html', '/static/reference/original.html', '/static/reference/live.html']:
            with self.subTest(url=url):
                redirect = self.client.get(url)
                self.assertEqual(redirect.status_code, 302)
                self.assertEqual(redirect.headers['Location'], '/')
                page = self.client.get(url, follow_redirects=True)
                self.assertEqual(page.status_code, 200)
                self.assertIn(b'id="playback"', page.data)
                page.close()
        self.assertEqual(self.client.get('/static/missing.js').status_code, 404)

    def test_rejects_invalid_inputs(self):
        # 잘못된 모드와 예제 번호 및 입력 형식을 거부하는지 확인한다.
        for data in [None, [], {}, {'mode': [], 'index': 0}, {'mode': 'package', 'index': True}, {'mode': 'urgency', 'index': 3}]:
            response = self.client.post('/api/score', json=data)
            self.assertEqual(response.status_code, 400)

    @patch('server.OpenAI')
    def test_live_request_and_result(self, constructor):
        # 실제 SDK 요청 구성을 확인하고 거부 또는 잘못된 확률 응답을 처리하는지 확인한다.
        answer = {'type': 'score', 'name': 'urgency', 'score': 1.1, 'confidence': .8,
                  'probabilities': [{'label': label, 'value': i, 'probability': p} for i, (label, p) in enumerate(zip(['Low','Medium','High'], [.1,.7,.2]))]}
        result = MagicMock()
        result.model_dump.return_value = {'answers': [answer]}
        create = constructor.return_value.__enter__.return_value.decisions.create
        create.return_value = result
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-only'}):
            response = self.client.post('/api/score', json={'mode': 'urgency', 'index': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['answer']['score'], 1.1)
        self.assertIn('CSV exports', create.call_args.kwargs['input'])
        result.model_dump.return_value = {'answers': [{'type': 'refusal'}]}
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-only'}):
            self.assertEqual(self.client.post('/api/score', json={'mode':'package','index':0}).status_code, 422)
        answer['probabilities'][0]['probability'] = 4
        result.model_dump.return_value = {'answers': [answer]}
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-only'}):
            self.assertEqual(self.client.post('/api/score', json={'mode':'urgency','index':0}).status_code, 502)

# 파일을 직접 실행한 경우에만 서버나 콘솔 작업을 시작한다.
if __name__ == '__main__':
    unittest.main()
