# Check an image for visible damage

Dent / Cancellation / Answer relevance의 실제 probability(0~1)를 표시한다. 이미지와 텍스트 예제를 판단하며 실제 응답은 서버 실행 중 같은 항목에서 재사용한다.

## 실행

Python 3.10 이상이 필요하다. 각 프로젝트 폴더에서 실행한다. 기존 가상환경을 다른 Python 버전으로 덮어쓰지 않는다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# .env에 본인의 OPENAI_API_KEY를 설정한다.
.\.venv\Scripts\python.exe app.py
```

macOS/Linux에서는 `.venv/bin/python`을 사용한다. 접속 주소는 http://127.0.0.1:5052/ 이다.

환경변수 또는 프로젝트 `.env.local`, `.env`에서 기존 키를 읽는다. `OPENAI_ENV_FILE`로 기존 환경 파일의 경로를 지정할 수도 있다. 키는 서버에서만 사용하며 브라우저에 전달하지 않는다.

실제 `gpt-6-luna` Decisions API를 사용하며 API 사용료가 발생한다. 자동 재생은 Pause animation으로 멈출 수 있다. 호출 실패 시 기록된 샘플 수치로 대체하지 않는다.

## 검증

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

테스트는 모의 API 응답을 사용하며 실제 API 요청을 보내지 않는다. `verify_ui.py` 또는 `scripts/verify_ui.py`를 이용한 선택적 화면 검증에는 Playwright와 Microsoft Edge가 필요하다.

화면 자료의 출처는 `static/reference/SOURCE.md`에 기록했다. 공개 배포 자료에서 추출한 화면이며 공식 개발 저장소 전체는 아니다.
