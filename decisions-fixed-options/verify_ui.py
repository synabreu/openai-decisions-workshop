# 모의 API 응답으로 탭 전환과 결과 표시 및 화면 배치를 검증한다.
"""Browser QA uses mocked API responses; live requests are checked separately."""
import json
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server
from server import app
ROOT=Path(__file__).resolve().parent
server=make_server('127.0.0.1',0,app,threaded=True)
threading.Thread(target=server.serve_forever,daemon=True).start()
report={'errors':[]}
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(channel='msedge',headless=True)
  page=browser.new_page(viewport={'width':1280,'height':900},reduced_motion='reduce')
  page.on('pageerror',lambda error:report['errors'].append(str(error)))
  def respond(route):
   # 외부 API 호출 대신 검증용 응답을 반환해 화면 표시를 확인한다.
   mode=route.request.post_data_json['mode']
   labels={'driving':['Lane 1','Lane 2','Lane 3'],'routing':['Billing','Technical support','Account access'],'document':['Invoice','Receipt','Contract']}[mode]
   route.fulfill(json={'source':'decisions_api','choice':labels[0],'probabilities':dict(zip(labels,[.83,.12,.05])),'cached':False})
  # 브라우저 검증에서는 실제 호출 대신 지정한 모의 응답을 사용한다.
  page.route('**/api/choice',respond)
  page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='networkidle')
  frame=page.frame_locator('#reference-demo')
  out=ROOT/'validation';out.mkdir(exist_ok=True)
  for width,height in [(1280,900),(390,844)]:
   page.set_viewport_size({'width':width,'height':height})
   for mode in ['driving','routing','document']:
    page.locator(f'[data-mode="{mode}"]').click()
    panel=frame.locator('#'+mode+'-panel')
    expect(panel).to_be_visible()
    expect(panel.locator('.prob').first).to_have_text('0.83')
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    assert not frame.locator('html').evaluate('el=>el.scrollWidth>innerWidth')
    page.screenshot(path=str(out/f'{mode}-{width}.png'),full_page=True)
  # 브라우저 검증에서는 실제 호출 대신 지정한 모의 응답을 사용한다.
  page.route('**/api/choice',lambda route:route.fulfill(status=502,json={'error':'Test API failure'}))
  page.locator('[data-mode="routing"]').click()
  expect(page.locator('#api-retry')).to_be_visible()
  expect(frame.locator('#routing-panel .prob').first).to_have_text('—')
  # 브라우저 검증에서는 실제 호출 대신 지정한 모의 응답을 사용한다.
  page.route('**/api/choice',respond)
  page.locator('#api-retry').click()
  expect(frame.locator('#routing-panel .prob').first).to_have_text('0.83')
  report.update(tabs='all 3 passed, desktop and mobile',probabilities='mock API response rendered',error_and_retry='passed',mobile_overflow=False)
  browser.close()
finally:
 # 검증이 끝나면 임시 서버를 종료해 포트를 반환한다.
 server.shutdown()
 (ROOT/'validation/report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
assert not report['errors']
