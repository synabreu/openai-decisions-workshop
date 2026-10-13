# 프로젝트의 입력 처리와 결과 제공을 담당한다.
"""Local web UI for the existing insurance workflow (no extra web dependency)."""
import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from decision_insurance import ROOT, load_environment
from insurance.service import create_decision
from insurance.workflow import probability, select_workflow


def analyze(payload):
    # 실제 분석과 고정 예제 모드를 구분하고 담당자 검토 경로를 계산한다.
    mode = payload.get("mode", "live")
    threshold = payload.get("threshold", 0.8)
    if mode not in ("live", "mock") or not probability(threshold):
        raise ValueError("모드와 0~1 사이의 임계값을 확인하세요.")
    if mode == "mock":
        decision = json.loads((ROOT / "examples/mock_response.json").read_text(encoding="utf-8"))
    else:
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip() or len(text) > 20000:
            raise ValueError("사고 내용을 1~20,000자로 입력하세요.")
        load_environment()
        model = os.getenv("OPENAI_DECISIONS_MODEL", "").strip() or "gpt-6-luna"
        decision = create_decision(text, model)
    return {"mode": mode, "decision": decision, "workflow": select_workflow(decision, threshold)}


# 보험 접수 화면과 분석 API의 HTTP 요청을 처리한다.
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        # 사고 원문과 API 오류가 기본 요청 로그에 노출되지 않도록 로그 출력을 생략한다.
        pass  # 사고 원문과 API 오류를 기본 요청 로그에 남기지 않는다.

    def send_data(self, status, data, content_type="application/json; charset=utf-8"):
        # 응답 내용을 직렬화하고 상태 코드와 콘텐츠 형식을 설정해 전송한다.
        body = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # 화면과 가상 사고 예제를 제공하며 지원하지 않는 주소는 거부한다.
        if self.path == "/":
            self.send_data(200, (ROOT / "static/index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/sample":
            self.send_data(200, {"text": (ROOT / "examples/claim.txt").read_text(encoding="utf-8-sig")})
        else:
            self.send_data(404, {"error": "페이지를 찾을 수 없습니다."})

    def do_POST(self):
        # 요청 출처와 JSON 형식 및 크기를 확인하고 분석 결과나 오류를 반환한다.
        if self.path != "/api/analyze":
            return self.send_data(404, {"error": "페이지를 찾을 수 없습니다."})
        # JSON 형식과 동일 출처를 확인해 다른 웹사이트의 브라우저 요청을 차단한다.
        if self.headers.get("Origin") not in (None, "http://" + self.headers.get("Host", "")):
            return self.send_data(403, {"error": "허용되지 않은 요청입니다."})
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.send_data(415, {"error": "JSON 요청이 필요합니다."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 100000:
                raise ValueError("요청 크기를 확인하세요.")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("JSON 객체가 필요합니다.")
            self.send_data(200, analyze(payload))
        except (ValueError, UnicodeError) as exc:
            self.send_data(400, {"error": str(exc)})
        except RuntimeError as exc:
            self.send_data(502, {"error": str(exc)})
        except Exception:
            self.send_data(500, {"error": "처리 중 오류가 발생했습니다. 서버 설정을 확인하세요."})


# 파일을 직접 실행한 경우에만 서버나 콘솔 작업을 시작한다.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="보험 접수 웹 UI")
    parser.add_argument("--port", type=int, default=8093)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"보험 접수 웹 UI: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
