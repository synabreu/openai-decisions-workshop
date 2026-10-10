# 모의 API 응답으로 탭 전환과 결과 표시 및 화면 배치를 검증한다.
"""Optional local browser QA (Playwright + installed Microsoft Edge)."""
import json
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import app
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server, WSGIRequestHandler


# 검증 서버의 요청 로그를 생략한다.
class QuietHandler(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        # 브라우저 검증 중 반복되는 요청 로그 출력을 생략한다.
        pass


def main():
    # 임시 서버와 Edge를 실행해 데모 화면을 검증하고 캡처와 결과를 저장한다.
    output = ROOT / 'validation'
    output.mkdir(exist_ok=True)
    report = {'errors': [], 'failed_resources': []}
    server = make_server('127.0.0.1', 0, app, request_handler=QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='msedge', headless=True)
            page = browser.new_page(viewport={'width': 1280, 'height': 1000}, reduced_motion='reduce')
            # 화면 검증은 구분 가능한 모의 결과를 사용하며 실제 API 호출은 별도로 검증한다.
            page.route('**/api/predicate', lambda route: route.fulfill(json={'probability':0.831,'source':'decisions_api','cached':False}))
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.on('response', lambda response: report['failed_resources'].append(response.url) if response.status >= 400 else None)
            page.goto(url, wait_until='networkidle')
            frame = page.frame_locator('#reference-demo')
            assert frame.locator('.dent-flow').is_visible()
            from playwright.sync_api import expect
            expect(frame.locator('.dent-flow .number')).to_have_text('0.83')
            assert frame.locator('.carousel img').evaluate_all('(images) => images.every(i => i.complete && i.naturalWidth > 0)')
            page.screenshot(path=str(output / 'reference-desktop.png'), full_page=True)
            page.locator('#tab-cancellation').click()
            frame.locator('.cancel-flow').wait_for(state='visible')
            expect(frame.locator('.cancel-flow .cancel-number')).to_have_text('0.83')
            page.locator('#tab-answer_relevance').click()
            frame.locator('.relevance-flow').wait_for(state='visible')
            expect(frame.locator('.relevance-flow .relevance-number')).to_have_text('0.83')
            page.locator('#tab-dent').click()
            page.locator('#animation-toggle').click()
            assert page.locator('#animation-toggle').get_attribute('aria-pressed') == 'false'
            page.locator('#animation-toggle').click()
            assert page.locator('form, input[type=file], #threshold, #raw').count() == 0
            for endpoint in ['inspect', 'evaluate-text', 'example']:
                response = page.request.get(url + 'api/' + endpoint)
                assert response.status == 404
            page.set_viewport_size({'width': 390, 'height': 844})
            page.screenshot(path=str(output / 'reference-mobile.png'), full_page=True)
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
            report.update(tabs='all three passed', probability='API response rendered in all three tabs (mocked 0.831)', playback='passed', analysis_controls='removed', mobile_overflow=False)
            browser.close()
    finally:
        # 검증이 끝나면 임시 서버를 종료해 포트를 반환한다.
        server.shutdown()
        (output / 'reference-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True))
    assert not report['errors'] and not report['failed_resources']


# 파일을 직접 실행한 경우에만 서버나 콘솔 작업을 시작한다.
if __name__ == '__main__':
    main()
