FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt --no-cache-dir

COPY . .

RUN python manage.py collectstatic --no-input
RUN python manage.py migrate
RUN python manage.py loaddata data_dump.json

EXPOSE 80

CMD export && (gunicorn --log-level debug --bind 0.0.0.0:80 config.wsgi)
