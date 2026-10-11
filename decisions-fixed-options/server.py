# 프로젝트의 입력 처리와 결과 제공을 담당한다.
"""Local choice demo with server-side Decisions API evaluation."""

# 프로젝트 이름: OpenAI Descisions API (2) - Choice API
# 설명: 예제2 - 정해진 선택지 중에서 선택하는 Choice API 사용
# 작성자: 서진호
# 버전: v1.0
# 실행 예시: python server.py

import argparse
import json
import math
import os
import threading
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from openai import OpenAI, OpenAIError

# 현재 파일의 위치를 기준으로 환경 설정 파일을 읽는다.
ROOT = Path(__file__).resolve().parent
for path in (ROOT / '.env.local', ROOT / '.env'):
    load_dotenv(path)
if os.environ.get('OPENAI_ENV_FILE'):
    load_dotenv(os.environ['OPENAI_ENV_FILE'])


# Decisions API를 호출하고 결과를 캐시하는 서버를 제공한다.
app = Flask(__name__)
SAMPLES = json.loads((ROOT / 'static/samples.json').read_text(encoding='utf-8'))
# Choices와 질문을 정의하고 각 모드에 대해 선택지와 질문을 매핑한다.
CHOICES = {
    'driving': [('Lane 1', 'The left lane'), ('Lane 2', 'The middle lane'), ('Lane 3', 'The right lane')],
    'routing': [('Billing', 'Charges, payments, refunds and invoices'), ('Technical support', 'Product errors and broken functionality'), ('Account access', 'Login and authentication problems')],
    'document': [('Invoice', 'Requests a payment that is due'), ('Receipt', 'Confirms a completed payment'), ('Contract', 'Agreement defining obligations between parties')],
}
QUESTIONS = {
    'driving': 'Which lane should the car choose? Choose an unobstructed lane. Prefer lane 2 if clear; otherwise prefer lane 1 if clear, then lane 3.',
    'routing': 'Which team should handle this customer message?',
    'document': 'What kind of document is this?',
}
CACHE = {}
LOCK = threading.Lock()

def evaluate(mode, index):
    # 현재 예제를 Decisions API로 판단하고 검증한 실제 응답을 메모리에 보관한다.
    # 여러 요청이 같은 예제를 동시에 처리하지 않도록 캐시와 API 호출을 보호한다.
    with LOCK:
        key = (mode, index)
        if key in CACHE:
            return {**CACHE[key], 'cached': True}
        # 요청 시간이 무한정 늘어나지 않도록 제한하고 사용이 끝나면 API 클라이언트를 닫는다.
        with OpenAI(timeout=45, max_retries=0) as client:
            # 화면의 증거와 평가 기준을 실제 Decisions API로 전달한다.
            decision = client.decisions.create(model='gpt-6-luna', input=SAMPLES[mode][index], questions=[{
                'name': mode, 'type': 'choice', 'instructions': QUESTIONS[mode],
                'choices': [{'value': value, 'description': description} for value, description in CHOICES[mode]],
            }])
        # API 응답이 올바른지 검증하고 선택 결과와 확률을 반환한다.
        if not decision.answers or decision.answers[0].type != 'choice':
            raise ValueError('API가 판단을 거부했습니다. 확률을 표시할 수 없습니다.')

        answer = decision.answers[0] # API 응답의 선택지와 확률이 정의된 범위 내에 있는지 확인
        values = [value for value, _ in CHOICES[mode]] # 선택지와 확률이 정의된 범위 내에 있는지 확인

        # 선택지와 확률이 정의된 범위 내에 있는지 확인
        probabilities = {item.value: item.probability for item in answer.probabilities}
        if (set(probabilities) != set(values) or answer.choice not in values
                or any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities.values())
                or not math.isclose(sum(probabilities.values()), 1, abs_tol=0.001)):
            raise ValueError('API 확률 응답이 올바르지 않습니다.')
        result = {'choice': answer.choice, 'probabilities': probabilities, 'source':'decisions_api', 'cached':False}
        CACHE[key] = result
        return result

@app.get('/')
def index():
    # 루트 주소에서 프로젝트의 데모 화면을 제공한다.
    return send_file(ROOT / 'index.html')

@app.post('/api/choice')
def choice():
    # 모드와 예제 번호를 검증한 뒤 실제 선택 결과와 확률을 JSON으로 반환한다.
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='예제를 지정하세요.'), 400
    mode, index = data.get('mode'), data.get('index')
    if not isinstance(mode, str) or mode not in SAMPLES or type(index) is not int or not 0 <= index < len(SAMPLES[mode]):
        return jsonify(error='지원하지 않는 예제입니다.'), 400
    # 키가 없으면 외부 요청을 보내지 않고 설정 오류를 반환한다.
    if not os.environ.get('OPENAI_API_KEY'):
        return jsonify(error='서버에 기존 OPENAI_API_KEY를 설정하고 다시 실행하세요.'), 503
    try:
        return jsonify(evaluate(mode, index))
    # API 연결 실패는 비밀정보를 제외한 오류 응답으로 변환한다.
    except OpenAIError:
        return jsonify(error='Decisions API 호출 실패: 키 권한, 사용 한도 및 네트워크를 확인하세요.'), 502
    except ValueError as error:
        return jsonify(error=str(error)), 502

def main():
    # 실행 인자를 읽고 프로젝트의 주요 작업을 시작한다.
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5054)

    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('Port must be between 1 and 65535')
    # 서버를 시작하고 지정된 포트에서 요청을 수신한다.
    app.run(host='127.0.0.1', port=args.port, threaded=True)

# 파일을 직접 실행한 경우에만 서버나 콘솔 작업을 시작한다.
if __name__ == '__main__':
    main()
