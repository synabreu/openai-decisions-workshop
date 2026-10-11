# 프로젝트 이름: OpenAI Descisions API (3) - Score API
# 설명: 예제3 - 평가 기준에 따라 점수 매기는 Score API 사용
# 작성자: 서진호
# 버전: v1.0
# 실행 예시: python server.py

import base64
import math
import os
from flask import Flask, jsonify, request, send_from_directory, redirect, url_for
from openai import OpenAI, APIStatusError, OpenAIError
from config import ROOT


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024
# Choices와 질문을 정의하고 각 모드에 대해 선택지와 질문을 매핑한다.
TEXTS = [
    'Could you add a dark mode? It would be helpful when I work at night.',
    'CSV exports keep failing for one teammate. The rest of our team can still export.',
    'Checkout is failing for every customer. We haven’t processed an order in 20 minutes.',
]
RUBRICS = {
    'package': ('How damaged is this package?', [
        {'label': 'No damage', 'description': 'The package has no visible damage.'},
        {'label': 'Minor damage', 'description': 'Minor dents or wear; the package remains intact.'},
        {'label': 'Major damage', 'description': 'Major crushing, tearing, or structural damage.'}]),
    'urgency': ('How urgent is this request?', [
        {'label': 'Low', 'description': 'A feature request or nonblocking issue.'},
        {'label': 'Medium', 'description': 'A task fails for some users, but others can still work.'},
        {'label': 'High', 'description': 'A critical task is blocked for every customer.'}]),
}

def evidence(mode, index):
    # 선택한 요청 문구 또는 패키지 이미지를 API 입력 형식으로 구성한다.
    if mode == 'urgency':
        return TEXTS[index]
    name = ['package-intact.webp', 'package-minor.webp', 'package-major.webp'][index]
    data = base64.b64encode((ROOT / 'static/reference' / name).read_bytes()).decode()
    return [{'role': 'user', 'content': [{'type': 'input_image', 'image_url': 'data:image/webp;base64,' + data}]}]

@app.get('/')
def index():
    # 루트 주소에서 프로젝트의 데모 화면을 제공한다.
    return send_from_directory(ROOT / 'static', 'index.html')


@app.get('/api/docs/guides/decisions')
@app.get('/api/docs/guides/decisions/')
@app.get('/playground')
@app.get('/playground/')
@app.get('/static/official/index.html')
@app.get('/static/original.html')
@app.get('/static/reference/original.html')
@app.get('/static/reference/live.html')
def legacy_demo():
    # 기존 문서와 분석 주소를 현재 데모의 루트 주소로 연결한다.
    return redirect(url_for('index'), code=302)

@app.post('/api/score')
def score():
    # 예제 입력을 채점하고 점수와 단계별 확률을 검증해 반환한다.
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='올바른 JSON 입력이 필요합니다.'), 400
    mode, index = data.get('mode'), data.get('index')
    if not isinstance(mode, str) or mode not in RUBRICS or type(index) is not int or not 0 <= index < 3:
        return jsonify(error='예제 종류와 번호를 확인하세요.'), 400
    # 키가 없으면 외부 요청을 보내지 않고 설정 오류를 반환한다.
    if not os.environ.get('OPENAI_API_KEY', '').strip():
        return jsonify(error='기존 OPENAI_API_KEY를 찾을 수 없습니다. README의 설정을 확인하세요.'), 503
    instructions, levels = RUBRICS[mode]
    try:
        # 요청 시간이 무한정 늘어나지 않도록 제한하고 사용이 끝나면 API 클라이언트를 닫는다.
        with OpenAI(timeout=45, max_retries=0) as client:
            # 선택한 입력과 질문을 실제 Decisions API로 전달한다.
            result = client.decisions.create(model='gpt-6-luna', input=evidence(mode, index), questions=[
                {'type': 'score', 'name': mode, 'instructions': instructions, 'levels': levels}])
        answers = result.model_dump(mode='json')['answers']
        if len(answers) != 1 or answers[0].get('type') != 'score':
            return jsonify(error='판단이 거부되었거나 채점 응답이 없습니다.'), 422
        answer = answers[0]
        value, confidence = answer['score'], answer['confidence']
        probs = answer['probabilities']
        # 유한하지 않은 값과 허용 범위를 벗어난 수치는 정상 결과로 표시하지 않는다.
        if not math.isfinite(value) or not 0 <= value <= 2 or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError()
        if len(probs) != 3 or {p['label'] for p in probs} != {l['label'] for l in levels}:
            raise ValueError()
        if any(not math.isfinite(p['probability']) or not 0 <= p['probability'] <= 1 for p in probs):
            raise ValueError()
        if abs(sum(p['probability'] for p in probs) - 1) > .02:
            raise ValueError()
        return jsonify(source='decisions_api', answer=answer)
    # API 상태 코드를 기준으로 접근 권한과 요청 오류를 안내한다.
    except APIStatusError as exc:
        return jsonify(error=f'API HTTP {exc.status_code}: 키 권한, 사용 한도 및 요청을 확인하세요.'), 502
    # API 연결 실패는 비밀정보를 제외한 오류 응답으로 변환한다.
    except OpenAIError:
        return jsonify(error='API 연결에 실패했습니다. 네트워크와 서비스 상태를 확인하세요.'), 502
    except (ValueError, KeyError, TypeError):
        return jsonify(error='채점 응답 형식이 올바르지 않습니다.'), 502

# 파일을 직접 실행한 경우에만 서버나 콘솔 작업을 시작한다.
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', '5083')), debug=False)
