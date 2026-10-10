# 기존 API 키의 로딩 순서를 정의하며 키 값을 복사하거나 출력하지 않는다.
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
# 환경변수 값을 덮어쓰지 않고 프로젝트의 기존 설정 파일을 순서대로 읽는다.
for name in ('.env.local', '.env'):
    load_dotenv(ROOT / name)
if os.environ.get('OPENAI_ENV_FILE'):
    load_dotenv(os.environ['OPENAI_ENV_FILE'])
