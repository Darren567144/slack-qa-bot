FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install deps
RUN pip install --no-cache-dir slack-sdk==3.27.0 python-dateutil tqdm

COPY extract_slack.py /app/

ENTRYPOINT ["python", "/app/extract_slack.py"]