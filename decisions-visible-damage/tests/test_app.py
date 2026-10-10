# 테스트 조건에 따라 기능의 정상 동작과 오류 처리를 검증한다.
import unittest
from unittest.mock import patch, MagicMock
import app as server
from app import app


# 관련 기능의 정상 처리와 오류 처리 조건을 묶어 검증한다.
class DemoTests(unittest.TestCase):
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-only'})
    @patch('app.OpenAI')
    def test_real_request_and_cache(self, sdk):
        # 이미지를 실제 요청 형식으로 전달하고 동일 예제 응답을 재사용하는지 확인한다.
        server.cache.clear()
        sdk.return_value.__enter__.return_value.decisions.create.return_value.answers = [MagicMock(type='predicate', probability=0.831)]
        first = self.web.post('/api/predicate', json={'mode':'dent','index':0})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json['probability'], 0.831)
        second = self.web.post('/api/predicate', json={'mode':'dent','index':0})
        self.assertTrue(second.json['cached'])
        create = sdk.return_value.__enter__.return_value.decisions.create
        self.assertEqual(create.call_count, 1)
        self.assertTrue(create.call_args.kwargs['input'][0]['content'][0]['image_url'].startswith('data:image/webp;base64,'))
        server.cache.clear()

    @patch('app.evaluate_sample')
    def test_invalid_samples_never_call_api(self, evaluate):
        # 지원하지 않는 예제는 외부 API 호출 없이 거부하는지 확인한다.
        for payload in [{'mode':'dent','index':True}, {'mode':'unknown','index':0}, {'mode':'dent','index':5}, []]:
            self.assertEqual(self.web.post('/api/predicate',json=payload).status_code,400)
        evaluate.assert_not_called()

    @patch.dict('os.environ', {'OPENAI_API_KEY':'test-only'})
    @patch('app.OpenAI')
    def test_refusal_has_no_fallback_probability(self, sdk):
        # 판단 거부 시 샘플 확률로 대체하지 않는지 확인한다.
        server.cache.clear()
        sdk.return_value.__enter__.return_value.decisions.create.return_value.answers = [MagicMock(type='refusal')]
        result=self.web.post('/api/predicate',json={'mode':'cancellation','index':0})
        self.assertEqual(result.status_code,502)
        self.assertNotIn('probability',result.json)

    def test_shipped_numbers_are_empty(self):
        # HTML에 기록된 예제 확률이 남아 있지 않은지 확인한다.
        with self.web.get('/static/reference/predicate.html') as result:
            self.assertNotIn(b'>1.00<',result.data)
            self.assertNotIn(b'>0.90<',result.data)

    def setUp(self):
        # 각 테스트가 독립적으로 실행되도록 클라이언트 또는 예제 상태를 준비한다.
        self.web = app.test_client()

    def test_demo_without_analysis_controls(self):
        # 데모 화면에서 삭제한 직접 분석 컨트롤이 나타나지 않는지 확인한다.
        response = self.web.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'id="reference-demo"', response.data)
        self.assertNotIn(b'<form', response.data)
        self.assertNotIn(b'type="file"', response.data)
        self.assertNotIn(b'id="threshold"', response.data)
        self.assertNotIn(b'id="raw"', response.data)

    def test_analysis_endpoints_removed(self):
        # 삭제한 분석 엔드포인트가 제공되지 않는지 확인한다.
        for method, url in [('post', '/api/inspect'), ('post', '/api/evaluate-text'), ('get', '/api/example')]:
            with self.subTest(url=url):
                self.assertEqual(getattr(self.web, method)(url).status_code, 404)

    def test_demo_assets(self):
        # 데모에 필요한 이미지와 스크립트 및 스타일을 제공하는지 확인한다.
        for name in ['predicate.html', 'demo.js', 'demo.css', 'can.webp', 'bottle.webp', 'travel-cup.webp', 'dented-mug.webp', 'dimpled-tin.webp']:
            with self.web.get('/static/reference/' + name) as response:
                self.assertEqual(response.status_code, 200)


# 파일을 직접 실행한 경우에만 서버나 콘솔 작업을 시작한다.
if __name__ == '__main__':
    unittest.main()
