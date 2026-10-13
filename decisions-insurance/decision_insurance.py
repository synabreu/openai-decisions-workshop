# 프로젝트 이름: OpenAI Decisions API를 사용한 AI 보험 사고 접수 분류 데모(Prototype)
# 설명: OpenAI Decisions API로 보험 사고 접수 내용을 분석하고 담당자의 검토 경로를 제안한다.
# 작성자: 서진호
# 버전: v1.0
# 실행은 python decision_insurance.py --input examples/claim.txt --output output/result.json 명령으로 수행한다.
# 설정 확인: python decision_insurance.py --mock

import argparse
import json
import os
from pathlib import Path
import sys
from insurance.service import create_decision
from insurance.workflow import select_workflow

ROOT = Path(__file__).resolve().parent


def load_environment():
    # 기존 환경변수를 유지하며 프로젝트 폴더의 .env.local과 .env를 순서대로 읽는다.
    # 로딩 패키지가 없고 실행 환경에 키도 없으면 설치 방법을 담은 오류를 발생시킨다.
    """기존 환경변수를 우선하고 프로젝트의 설정 파일을 읽는다."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        # 키가 없으면 외부 요청을 보내지 않고 설정 오류를 반환한다.
        if not os.environ.get("OPENAI_API_KEY", "").strip():
            raise RuntimeError("환경 설정 로딩에 python-dotenv가 필요하다. python -m pip install -U -r requirements.txt를 실행하라.") from None
        return
    for filename in (".env.local", ".env"):
        load_dotenv(ROOT / filename, override=False, encoding="utf-8-sig")


def main():
    # 명령행 옵션을 검증하고 실제 API 응답 또는 고정 모의 응답으로 검토 경로를 계산한다.
    # 결과를 JSON으로 출력하며 출력 경로가 지정되면 파일로 저장한다.
    # 실행이 성공하면 0을 반환하고 처리 가능한 오류가 발생하면 1을 반환한다.
    parser = argparse.ArgumentParser(description="Decisions API 보험 접수 분류 데모")
    parser.add_argument("--mock", action="store_true", help="API 호출 없이 고정 예시 응답 사용")
    parser.add_argument("--input", type=Path, help="UTF-8 사고 접수 텍스트 파일")
    parser.add_argument("--model", default=None, help="Decisions 모델 (기본: OPENAI_DECISIONS_MODEL 또는 gpt-6-luna)")
    parser.add_argument("--threshold", type=float, default=0.80)
    parser.add_argument("--output", type=Path, help="분석 결과를 JSON 파일로 저장")
    args = parser.parse_args()

    # Mock 모드에서는 고정된 샘플 데이터만 사용하도록 제한한다.
    # --mock과 --input을 동시에 지정하면 오류 메시지를 출력하고 실행을 중단한다.
    if args.mock and args.input:
        parser.error("--mock은 고정 샘플 전용이다. 사용자 입력 분석은 --mock을 빼고 실행하라.")
    try:
        # 1. 실행 환경 설정
        # 실제 OpenAI API를 호출하는 Live 모드에서만 환경변수를 로드한다.
        # Mock 모드는 API 호출이 없으므로 환경변수를 로드하지 않는다.
        if not args.mock:
            load_environment()

        # 2. Decisions 모델과 임계값 검증
        model = args.model or os.getenv("OPENAI_DECISIONS_MODEL", "").strip() or "gpt-6-luna"
        # 임계값은 0~1 사이의 실수여야 한다.
        if not 0 <= args.threshold <= 1:
            raise ValueError("threshold는 0~1이어야 한다.")
        if args.mock:
            print("[MOCK] 고정 예시 응답. 실제 API 판단 결과가 아니다.")
            decision = json.loads((ROOT / "examples/mock_response.json").read_text(encoding="utf-8"))
        else:
            text = (args.input or ROOT / "examples/claim.txt").read_text(encoding="utf-8-sig")
            decision = create_decision(text, model) # 실제 Decisions API 호출

        # 3. 판단 결과를 기반으로 워크플로 선택
        workflow = select_workflow(decision, args.threshold)
        result = {"mode": "mock" if args.mock else "live", "decision": decision, "workflow": workflow}
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))

        # 4. 결과를 파일로 저장
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1


# 파일을 직접 실행한 경우에만 서버나 콘솔 작업을 시작한다.
if __name__ == "__main__":
    raise SystemExit(main())
