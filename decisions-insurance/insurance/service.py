# 파일명: insurance/service.py
# 설명: 사고 접수 내용과 API 키 및 SDK 기능을 확인하고 Decisions API의 분석 결과를 반환하며 연결과 모델 접근 등의 오류를 안전한 메시지로 처리한다.
# 작성자: 서진호
# 버전: v1.0

import os
from .questions import QUESTIONS


def create_decision(text, model):
    # 사고 접수 내용과 API 키를 확인한 뒤 지정한 모델에 네 가지 질문을 전달한다.
    # API 응답을 JSON으로 저장할 수 있는 사전으로 반환한다.
    # 키나 사고 원문이 오류 로그에 노출되지 않도록 API 예외를 실행 오류로 변환한다.
    if not text.strip():
        raise ValueError("사고 접수 내용이 비어 있다.")
    # 키가 없으면 외부 요청을 보내지 않고 설정 오류를 반환한다.
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        raise RuntimeError("OPENAI_API_KEY가 없다. 프로젝트의 .env.local 또는 .env에 기존 키를 설정하거나 실행 터미널의 환경변수를 확인하라.")
    try:
        from openai import OpenAI, APIError, APIStatusError
    except ImportError as exc:
        raise RuntimeError("python -m pip install -U -r requirements.txt를 먼저 실행하라.") from exc
    # 요청 시간이 무한정 늘어나지 않도록 제한하고 사용이 끝나면 API 클라이언트를 닫는다.
    with OpenAI(timeout=45.0, max_retries=2) as client:
        # SDK 버전에 따라 정적 타입 정의에 없는 기능을 실행 시점에 확인한다.
        decisions = getattr(client, "decisions", None)
        if decisions is None:
            raise RuntimeError("현재 SDK에 decisions가 없다. python -m pip install -U openai로 갱신하라.")
        try:
            return decisions.create(
                model=model, input=text, questions=QUESTIONS,
            ).model_dump(mode="json")
        # API 상태 코드를 기준으로 접근 권한과 요청 오류를 안내한다.
        except APIStatusError as exc:
            # 원문 응답이나 키, 사고 개인정보를 오류 로그에 출력하지 않는다.
            if exc.status_code == 404:
                body = exc.body if isinstance(exc.body, dict) else {}
                error = body.get("error", body)
                code = error.get("code") if isinstance(error, dict) else None
                if code == "model_not_found":
                    raise RuntimeError("API HTTP 404 (model_not_found): 선택한 모델을 Decisions API에서 사용할 수 없다. --model gpt-6-luna로 실행하고 OPENAI_DECISIONS_MODEL 설정 및 계정 접근 권한을 확인하라.") from None
                raise RuntimeError("API HTTP 404: Decisions API 요청 경로를 찾을 수 없다. OPENAI_BASE_URL 및 /v1/decisions 지원 여부를 확인하라.") from None
            raise RuntimeError(f"API HTTP {exc.status_code}: 키, 모델 접근 권한, 한도 및 요청 형식을 확인하라.") from None
        except APIError:
            raise RuntimeError("API 연결 또는 응답 오류. 네트워크와 서비스 상태를 확인하라.") from None
