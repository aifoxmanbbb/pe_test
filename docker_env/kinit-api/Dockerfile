FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY kinit-api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY kinit-api/ /app/

EXPOSE 9000
CMD ["python", "main.py", "run", "--host", "0.0.0.0", "--port", "9000"]
