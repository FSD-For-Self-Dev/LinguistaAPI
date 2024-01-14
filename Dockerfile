FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt --no-cache-dir

COPY . .

EXPOSE 8000

CMD export && (gunicorn --log-level debug --bind 0.0.0.0:80 config.wsgi)
