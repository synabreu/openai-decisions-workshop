# 모의 API 응답으로 탭 전환과 결과 표시 및 화면 배치를 검증한다.
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server
from server import app
server=make_server('127.0.0.1',0,app,threaded=True)
threading.Thread(target=server.serve_forever,daemon=True).start()
errors=[]
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='msedge',headless=True)
  page=browser.new_page(viewport={'width':947,'height':508},reduced_motion='no-preference')
  page.on('pageerror',lambda error:errors.append(str(error)))
  def respond(route):
   # 외부 API 호출 대신 검증용 응답을 반환해 화면 표시를 확인한다.
   mode=route.request.post_data_json['mode'];labels=['No damage','Minor damage','Major damage'] if mode=='package' else ['Low','Medium','High']
   route.fulfill(json={'source':'decisions_api','answer':{'score':1.7,'probabilities':[{'label':label,'probability':prob} for label,prob in zip(labels,[.1,.1,.8])]}})
  # 브라우저 검증에서는 실제 호출 대신 지정한 모의 응답을 사용한다.
  page.route('**/api/score',respond)
  page.goto(f'http://127.0.0.1:{server.server_port}/')
  expect(page.locator('#package-panel .score-number')).to_have_text('1.70')
  Path('validation').mkdir(exist_ok=True)
  page.screenshot(path='validation/card-desktop.png')
  for mode in ['package','urgency']:
   page.locator('#'+mode+'-tab').click()
   expect(page.locator('#'+mode+'-panel .score-number')).to_have_text('1.70')
  assert page.locator('iframe,header,footer,pre,select').count()==0
  expect(page.locator('#playback')).to_have_text('Pause animation')
  page.locator('#playback').click();expect(page.locator('#playback')).to_have_text('Resume animation')
  page.locator('#playback').click()
  page.set_viewport_size({'width':390,'height':844})
  assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
  Path('validation').mkdir(exist_ok=True)
  page.screenshot(path='validation/demo-mobile.png',full_page=True)
  browser.close()
finally:server.shutdown()
assert not errors,errors
print('PASS: two tabs, API results, playback, no document UI, mobile overflow, no JavaScript errors')
