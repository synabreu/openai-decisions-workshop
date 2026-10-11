# 프로젝트의 입력 처리와 결과 제공을 담당한다.
import base64
import math
import os
import threading
import argparse

from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from openai import OpenAI, OpenAIError

ROOT = Path(__file__).resolve().parent

# 기존 설정을 우선하면서 로컬 키 파일을 순서대로 읽는다.
for env in (ROOT / '.env.local', ROOT / '.env'):
    load_dotenv(env)
if os.environ.get('OPENAI_ENV_FILE'):
    load_dotenv(os.environ['OPENAI_ENV_FILE'])


cache = {}
cache_lock = threading.Lock()


def sample_input(mode, index):
    # 배포된 HTML의 문구를 직접 읽어 화면과 API 입력이 일치하도록 한다.
    # 화면에 표시되는 고정 예제를 이미지 또는 텍스트 증거와 판단 질문으로 구성한다.
    from html.parser import HTMLParser

    # HTML에서 현재 예제의 인용문을 추출하는 상태를 관리한다.
    class Quotes(HTMLParser):
        def __init__(self):
            # HTML에서 추출할 문구 목록과 현재 수집 상태를 초기화한다.
            super().__init__()
            self.values = []
            self.active = False
        def handle_starttag(self, tag, attrs):
            # 대상 인용문 태그를 만나면 새로운 문구 수집을 시작한다.
            if tag == 'blockquote' and dict(attrs).get('class', '').split()[0] == ('cancel-quote' if mode == 'cancellation' else 'relevance-quote'):
                self.active = True
                self.values.append('')
        def handle_data(self, data):
            # 대상 태그 안의 텍스트를 현재 문구에 추가한다.
            if self.active:
                self.values[-1] += data
        def handle_endtag(self, tag):
            # 인용문 태그가 닫히면 현재 문구 수집을 종료한다.
            if tag == 'blockquote':
                self.active = False

    # HTMLParser를 사용해 예제 문구를 추출하고 판단 질문과 함께 반환한다.
    if mode == 'dent':
        names = ['can', 'bottle', 'travel-cup', 'dented-mug', 'dimpled-tin']
        encoded = base64.b64encode((ROOT / 'static/reference' / (names[index] + '.webp')).read_bytes()).decode()
        return [{'role': 'user', 'content': [{'type': 'input_image', 'image_url': 'data:image/webp;base64,' + encoded}]}], 'Does this item have a dent?'

    parser = Quotes()
    parser.feed((ROOT / 'static/reference/predicate.html').read_text(encoding='utf-8'))
    evidence = parser.values[index]

    # 판단 질문을 예제 종류에 따라 반환한다.
    if mode == 'cancellation':
        return evidence, 'Does this customer want to cancel their subscription?'
    return 'Question: Can I return an item after 30 days?\nAnswer: ' + evidence, 'Does the answer directly address the question?'


def evaluate_sample(mode, index):
    # 동일 예제의 중복 호출을 막고 실제 API 확률을 검증해 재사용한다.
    # 동시 요청에서도 같은 예제를 중복 판단하지 않도록 캐시 접근과 호출을 잠근다.
    with cache_lock:
        key = (mode, index)
        if key in cache:
            return {**cache[key], 'cached': True}
        evidence, instructions = sample_input(mode, index)

        # 요청 시간이 무한정 늘어나지 않도록 제한하고 사용이 끝나면 API 클라이언트를 닫는다.
        with OpenAI(timeout=45, max_retries=0) as client:
            # 선택한 입력과 질문을 실제 Decisions API로 전달한다.
            result = client.decisions.create(model='gpt-6-luna', input=evidence,
                questions=[{'type': 'predicate', 'name': mode, 'instructions': instructions}])

        # 반환된 첫 판단의 형식과 확률을 확인할 준비를 한다.
        answer = result.answers[0]
        if answer.type != 'predicate':
            raise ValueError('판단이 거부되었습니다. 확률을 표시할 수 없습니다.')
        probability = answer.probability

        # 유한하지 않은 값과 허용 범위를 벗어난 수치는 정상 결과로 표시하지 않는다.
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError('API 응답의 probability가 올바르지 않습니다.')
        cache[key] = {'probability': probability, 'source': 'decisions_api', 'cached': False}
        return cache[key]

app = Flask(__name__)


@app.get("/")
def index():
    # 루트 주소에서 프로젝트의 데모 화면을 제공한다.
    return render_template("index.html")


@app.post('/api/predicate')
def predicate():
    # 예제 종류와 번호를 확인한 뒤 실제 참거짓 판단 확률을 반환한다.
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='판단할 예제를 지정하세요.'), 400
    mode, index = data.get('mode'), data.get('index')
    counts = {'dent': 5, 'cancellation': 3, 'answer_relevance': 3}
    if not isinstance(mode, str) or mode not in counts or type(index) is not int or not 0 <= index < counts[mode]:
        return jsonify(error='지원하지 않는 예제입니다.'), 400
    # 키가 없으면 외부 요청을 보내지 않고 설정 오류를 반환한다.
    if not os.environ.get('OPENAI_API_KEY'):
        return jsonify(error='서버에 기존 OPENAI_API_KEY를 설정한 뒤 다시 실행하세요.'), 503
    try:
        return jsonify(evaluate_sample(mode, index))
    # API 연결 실패는 비밀정보를 제외한 오류 응답으로 변환한다.
    except OpenAIError:
        return jsonify(error='Decisions API 호출에 실패했습니다. 키 권한, 사용 한도 및 네트워크를 확인하세요.'), 502
    except ValueError as error:
        return jsonify(error=str(error)), 502


# 파일을 직접 실행한 경우에만 서버나 콘솔 작업을 시작한다.
if __name__ == "__main__":

    # 명령줄 인자를 처리해 포트 번호를 지정할 수 있도록 한다.
    parser = argparse.ArgumentParser(description="Decisions 공식 데모 로컬 서버")
    parser.add_argument("--port", type=int, default=5052,
                        help="로컬 서버 포트 (기본값: 5052)")
    args = parser.parse_args()
    # 포트 번호가 유효한 범위인지 확인한다.
    if not 1 <= args.port <= 65535:
        parser.error("포트는 1~65535 사이여야 합니다.")
    app.run(host="127.0.0.1", port=args.port, debug=False)
