# Decisions API 보험 접수 분류 프로젝트

이 프로젝트는 지금까지 배운 OpenAI의 Decisions API 를 응용해 실제로 B2B에서 사용할만 한 응용 AI로 보험 접수 분류 프로젝트를 작성해 보았다. 보험 기록자가 사고 접수 문장을 받아 접수 대상 여부(predicate), 처리 경로(choice), 긴급도(score), 부상 관련 검토 필요성(predicate)을 평가한다.




## 1. 실제 OpenAI API 연결

실제 Decisions API를 사용하려면 `OPENAI_API_KEY`가 필요하다. `decisions-insurance` 프로젝트 루트의 `.env` 파일에 기존 API 키와 모델을 설정한다. `.env` 파일이 없다면 `.env.example`을 복사해 만든다.

다음과 같이 여러분의 API 키를 <Your_OpenAI_API_Key>에 대체해 입력한다.

```dotenv
OPENAI_API_KEY=<Your_OpenAI_API_Key>
OPENAI_DECISIONS_MODEL=gpt-6-luna
```

설정은 현재 환경변수 → `.env.local` → `.env` 순서로 적용한다. 앞에서 읽은 값은 뒤의 파일로 덮어쓰지 않는다. 키는 서버에서만 사용하며 브라우저에 전달하지 않는다.

실제 분석은 다음 명령으로 실행한다.

```powershell
python decision_insurance.py --input examples/car_accident.txt --output output/car_accident_result.json
```

사고 접수 텍스트를 Decisions API에 전달해 접수 대상 여부, 처리 경로, 긴급도, 부상 관련 검토 필요성을 판단한다. 반환된 결과를 검증한 뒤 담당자의 검토 경로를 제안하고 JSON 파일로 저장한다. 실제 부서 배정이나 보험금 지급은 실행하지 않는다.

웹 화면은 `.\start-web.ps1`로 실행하고 http://127.0.0.1:8093 에 접속한다. 실제 분석 모드를 선택해야 API를 호출한다. 환경 설정을 변경했다면 서버를 재시작한다.

`--mock`은 고정 예제 응답만 사용하며 API를 호출하지 않는다. 실제 호출에는 API 사용료가 발생한다. 실제 키가 들어 있는 `.env`와 `.env.local`은 Git에 올리지 않는다.





## 2. Decisions-insurance 예제 실행

### 2-1. Windows 11 PowerShell

1) 가상환경 생성

```powershell
python -m venv .venv
```

2) 가상환경 활성화

```powershell
.\.venv\Scripts\Activate.ps1
```

3) 필요한 패키지 설치

```powershell
python -m pip install -U -r requirements.txt
```

4) 설치가 끝나면 모의 실행한다.

```powershell
python decision_insurance.py --mock
```

5) 콘솔에서 실제 실행은 다음과 같다.

```powershell
python decision_insurance.py --input examples/claim.txt --output output/result.json
```

### 2-2. macOS / Linux 운영체제에서 설치

```bash
cd decisions-insurance
python3 -m venv .venv
.venv/bin/python -m pip install -U -r requirements.txt
.venv/bin/python decision_insurance.py --input examples/claim.txt --output output/result.json
```

VS Code에서는 이 폴더를 열고 Python 인터프리터를 `.venv`로 선택한다. 명령은 VS Code 터미널에서도 그대로 사용할 수 있다.

### 2-3. API 키 없이 실행하려면?

모의 모드는 별도 패키지 설치가 필요 없다.

```bash
python decision_insurance.py --mock
```

고정된 가상 응답을 읽고 `MEDICAL_REVIEW`를 표시한다. 확률은 설명용으로 작성한 값이며 실제 모델 결과가 아니다. 임의 텍스트를 분석하지 않으므로 `--mock`과 `--input`을 함께 사용할 수 없다.

### 2-4. 웹 UI 실행

decisions-insurance 프로젝트 폴더에서 다음을 실행하고 http://127.0.0.1:8093 을 연다.

```powershell
.\start-web.ps1
```

일반 Python 환경에서는 기존 설치 절차 후 `python server.py`로 실행할 수 있다. 포트 변경은 `python server.py --port 8094` 또는 `./start-web.ps1 -Port 8094`를 사용한다. 종료는 실행 터미널에서 Ctrl+C를 누른다.

웹 화면에서 사고 내용 입력, 가상 예시 불러오기, 임계값 설정, 질문별 확률 및 검토 경로 확인, 전체 응답 보기와 JSON 다운로드를 지원한다. 실제 모드는 기존 `.env.local` 또는 `.env`의 키를 서버에서만 읽는다. 모의 모드는 입력 내용을 분석하지 않고 고정된 예시 응답만 표시한다. 사고 내용과 결과는 서버 파일로 자동 저장하지 않는다. 브라우저에서 JSON을 다운로드할 수 있다.





















## 구성

| 파일                            | 역할                               |
| ------------------------------- | ---------------------------------- |
| `decision_insurance.py`       | CLI와 JSON 출력·저장              |
| `insurance/questions.py`      | 질문 4개 및 경로·등급 정의        |
| `insurance/service.py`        | API 호출과 연결 오류 처리          |
| `insurance/workflow.py`       | 검토 경로 규칙                     |
| `examples/claim.txt`          | 원래 예제 기반의 가상 사고 접수    |
| `examples/mock_response.json` | 고정 모의 응답                     |
| `tests/test_workflow.py`      | 응답 거부·누락·확률 오류 등 검증 |

텍스트 입력 → Decisions API → JSON 응답 → 경로 규칙 → 콘솔 표시/JSON 저장 순서로 동작한다. 실제 부서 배정, 연락, 지급 처리는 하지 않는다. 결과의 `executed`는 항상 `false`다.

## 원래 코드에서 보완한 내용

- `client.decisions.create(model=..., input=..., questions=...)`와 질문 4개를 유지했다.
- API 키·SDK 기능 확인, 타임아웃과 최대 2회 재시도, API 오류 처리를 추가했다.
- 응답 거부, 필수 결과 누락, 중복 이름, 잘못된 확률과 알 수 없는 경로는 `HUMAN_REVIEW`로 처리한다.
- 기본 경로 신뢰도 임계값은 0.80이다. 미달이면 담당자 검토를 제안한다. 긴급 경로는 낮은 신뢰도라도 긴급 검토 제안을 유지한다.
- `AUTO_APPROVE` 후보는 유지하지만 지급 승인 없이 담당자 검토로 전환한다.
- 일반 경로에서 부상 검토 확률이 임계값 이상이면 의료 검토를 제안한다.

`valid_insurance_claim`은 사고 접수 대상으로 볼 수 있는지에 관한 질문이며 사고의 진위, 보장 자격이나 지급 여부를 확정하지 않는다. `medical_attention_required`도 담당자 검토 필요성에 대한 예제 질문이다. 임계값과 업무 규칙은 데모용이며 실제 업무 적용 전 평가 데이터로 검증해야 한다. confidence가 실제 정확도를 보장하지 않는다.

## 옵션과 테스트

`decision_insurance.py`는 다음 명령행 인자를 지원한다.

| 인자 | 설명 | 기본값 |
| --- | --- | --- |
| `--input` | UTF-8 사고 접수 텍스트 파일 경로 | `examples/claim.txt` |
| `--output` | 결과 JSON 저장 경로 | 파일 저장 없이 콘솔 출력 |
| `--model` | 사용할 Decisions 모델 | `OPENAI_DECISIONS_MODEL` 환경변수 또는 `gpt-6-luna` |
| `--threshold` | 검토 경로를 선택하는 확률 기준, 0~1 | `0.80` |
| `--mock` | API 호출 없이 고정 예제 응답 사용 | 사용하지 않음 |
| `-h`, `--help` | 도움말 표시 후 종료 | — |

가상의 자동차 사고 접수 예제는 [car_accident.txt](examples/car_accident.txt)에 있다. `decisions-insurance` 폴더에서 다음 명령을 실행한다.

```bash
python decision_insurance.py --input examples/car_accident.txt --output output/car_accident_result.json
```

기존 API 키로 실제 Decisions API를 호출하고, 결과를 `output/car_accident_result.json`에 저장한다. API 사용료가 발생한다.

확률 기준을 `0.9`로 지정하려면 다음과 같이 실행한다.

```bash
python decision_insurance.py --input examples/car_accident.txt --threshold 0.9 --output output/car_accident_result.json
```

`--mock`은 고정 예제 전용이므로 `--input`과 함께 사용할 수 없다.

```bash
python decision_insurance.py --help
python decision_insurance.py --mock --output output/mock.json
python decision_insurance.py --input examples/claim.txt --threshold 0.85
python decision_insurance.py --model gpt-6-luna
python -m unittest discover -s tests -v
```

모델은 `--model`, `OPENAI_DECISIONS_MODEL`, 기본값 `gpt-6-luna` 순서로 선택한다. 일반 API용 `OPENAI_MODEL`은 Decisions 모델 선택에 사용하지 않는다. 실제 실행 시 프로젝트 폴더의 `.env.local`, `.env`를 순서대로 자동 로딩하며 이미 설정된 환경변수를 덮어쓰지 않는다. 기존 파일의 `OPENAI_API_KEY`를 그대로 사용할 수 있다. 환경 설정 로딩 패키지는 `python -m pip install -U -r requirements.txt`로 설치한다. 입력 파일은 UTF-8이다. `--output` 지정 시 같은 이름의 파일을 덮어쓴다.

## 검증 범위와 문제 해결

모의 실행과 6개 경로 규칙 테스트를 통과했다. 2026-10-07에 기존 프로젝트 키와 `gpt-6-luna`로 실제 API 호출 및 `output/result.json` 저장을 확인했다. 다른 계정의 모델 접근 권한은 별도로 확인해야 한다. SDK 최소 버전은 고정하지 않았으며 최신 SDK를 설치한다. 설치된 SDK에 `decisions`가 없다면 명시적으로 오류를 표시한다.

- 키 오류: 실행 터미널의 `OPENAI_API_KEY`를 확인한다.
- `decisions` 속성 없음: 같은 Python으로 `python -m pip install -U openai`를 실행한다.
- HTTP 401/403/404: 키, API·모델 접근 권한과 모델명을 확인한다.
- HTTP 429: 계정 한도와 요청량을 확인한다.
- 모의 실행 성공은 실제 API 연결 성공을 의미하지 않는다.

## 공식 문서

2026-10-07에 아래 문서의 요청·응답 형식을 확인했다. Decisions는 beta API이며 질문별 refusal이 가능하다. score 확률 항목은 label, value, probability를 포함한다. 모의 응답의 점수와 확률은 설명용이다.

- [Python Decisions create](https://developers.openai.com/api/reference/python/resources/decisions/methods/create)
- [요청·응답 스키마](https://developers.openai.com/api/reference/resources/decisions/methods/create)
