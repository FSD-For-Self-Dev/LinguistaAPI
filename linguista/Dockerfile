FROM python:3.10-slim

WORKDIR /linguista

COPY requirements.txt .

RUN pip3 install -r requirements.txt --no-cache-dir

COPY . .

CMD ["gunicorn", "config.wsgi:application", "--bind", "0:8000" ] 
