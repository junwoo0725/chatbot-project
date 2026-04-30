FROM python:3.12-slim

WORKDIR /app

# 의존성 먼저 복사 및 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY community_api/app ./app

# uvicorn으로 FastAPI 실행 (EC2 직접 배포용)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
