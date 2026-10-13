# OpenAI Decisions Workshop

실제 Decisions API를 사용하는 Python 데모 4개다. 함수와 핵심 로직에 한글 주석을 포함한다.

| 프로젝트 | 기능 | 로컬 포트 |
| --- | --- | --- |
| [decisions-visible-damage](decisions-visible-damage/) | 이미지 손상 및 텍스트 predicate 판단 | 5052 |
| [decisions-fixed-options](decisions-fixed-options/) | 고정 선택지의 choice 판단 | 5054 |
| [decisions-score-rubric](decisions-score-rubric/) | 기준에 따른 score 채점 | 5083 |
| [decisions-insurance](decisions-insurance/) | 보험 접수 분류 CLI 및 웹 UI | 8093 |

각 폴더의 README를 따라 가상환경을 생성하고 실행한다. Decisions API 접근 권한이 있는 기존 API 키가 필요하며 실제 호출에는 사용료가 발생한다.

API 키, 개인 환경 파일, 가상환경, 백업, 실행 결과, 로그, 화면 캡처는 포함하지 않는다. `.env.example`은 키가 없는 설정 양식이다. 보험 예제는 가상 사고 내용만 포함하며 실제 부서 배정이나 지급을 실행하지 않는다.

공식 문서: https://developers.openai.com/api/docs/guides/decisions
