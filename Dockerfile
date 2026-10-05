# Student: Soni Pope
# Project 1 - Schools

FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY templates ./templates
COPY static ./static

EXPOSE 5000

CMD ["python", "-m", "flask", "--app", "src/app", "run", "--host=0.0.0.0"]