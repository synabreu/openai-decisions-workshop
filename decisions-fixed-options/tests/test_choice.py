# 테스트 조건에 따라 기능의 정상 동작과 오류 처리를 검증한다.
import unittest
from unittest.mock import patch, MagicMock
import server

# 관련 기능의 정상 처리와 오류 처리 조건을 묶어 검증한다.
class ChoiceTests(unittest.TestCase):
 def setUp(self):
  # 각 테스트가 독립적으로 실행되도록 클라이언트 또는 예제 상태를 준비한다.
  self.client=server.app.test_client()
  server.CACHE.clear()
 def test_invalid_input(self):
  # 잘못된 예제 입력은 API를 호출하지 않고 거부하는지 확인한다.
  with patch('server.evaluate') as evaluate:
   for data in [[],{}, {'mode':'driving','index':True},{'mode':'driving','index':6},{'mode':'other','index':0}]:
    self.assertEqual(self.client.post('/api/choice',json=data).status_code,400)
   evaluate.assert_not_called()
 @patch.dict('os.environ',{'OPENAI_API_KEY':'test-only'})
 @patch('server.OpenAI')
 def test_choice_request_and_cache(self,sdk):
  # 선택 질문의 입력과 실제 응답 재사용을 확인한다.
  answer=MagicMock(type='choice',choice='Billing',probabilities=[MagicMock(value='Billing',probability=.83),MagicMock(value='Technical support',probability=.12),MagicMock(value='Account access',probability=.05)])
  create=sdk.return_value.__enter__.return_value.decisions.create
  create.return_value.answers=[answer]
  result=self.client.post('/api/choice',json={'mode':'routing','index':0})
  self.assertEqual(result.status_code,200)
  self.assertEqual(result.json['probabilities']['Billing'],.83)
  self.assertEqual(create.call_args.kwargs['input'],server.SAMPLES['routing'][0])
  self.assertEqual(create.call_args.kwargs['questions'][0]['type'],'choice')
  result=self.client.post('/api/choice',json={'mode':'routing','index':0})
  self.assertTrue(result.json['cached'])
  self.assertEqual(create.call_count,1)
 @patch.dict('os.environ',{'OPENAI_API_KEY':'test-only'})
 @patch('server.OpenAI')
 def test_refusal(self,sdk):
  # 판단 거부 응답을 확률로 대체하지 않는지 확인한다.
  sdk.return_value.__enter__.return_value.decisions.create.return_value.answers=[MagicMock(type='refusal')]
  result=self.client.post('/api/choice',json={'mode':'document','index':0})
  self.assertEqual(result.status_code,502)
  self.assertNotIn('probabilities',result.json)
  self.assertFalse(server.CACHE)
 def test_no_static_probabilities_or_secret_routes(self):
  # 기록된 초기 확률이 없고 민감한 파일을 HTTP로 제공하지 않는지 확인한다.
  with self.client.get('/static/reference/choice.html') as response:
   self.assertNotIn(b'>0.94<',response.data)
   self.assertNotIn(b'>1.00<',response.data)
  for url in ['/.env','/server.py','/.venv-api/pyvenv.cfg']:
   self.assertEqual(self.client.get(url).status_code,404)

if __name__=='__main__': unittest.main()
