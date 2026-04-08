FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
ARG PIP_INDEX_URL=https://pypi.org/simple

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt -i ${PIP_INDEX_URL}

COPY . /app/

EXPOSE 9000
CMD ["python", "main.py", "run", "--host", "0.0.0.0", "--port", "9000"]
