# API for Linguista
backend | rest api

<!-- [![CI](https://github.com/FSD-For-Self-Dev/LinguistaAPI/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/FSD-For-Self-Dev/LinguistaAPI/actions/workflows/main.yml) -->

## Описание

Платформа для помощи в самообучении иностранным языкам и пополнении словарного запаса

## Запуск проекта в режиме разработчика

### Создание окружения

#### Poetry

Создание виртуального окружения:
```bash
poetry env use python3.11
```

Установка зависимостей (для разработки):
```bash
poetry install --with dev
```

Запуск оболочки и активация виртуального окружения (из папки проекта):
```bash
poetry shell
```

Проверка активации виртуального окружения:
```bash
poetry env list
```

***Установка хуков прекоммита:***
```bash
pre-commit install
```

#### Venv

Создание виртуального окружения:
```bash
python -m venv venv
. venv/Sctipts/actvate | source venv/Scripts/activate
python -m pip install --upgrade pip
```

Установка зависимостей (из директории с requirements.txt):
```bash
pip install -r requirements.txt
```

***Установка хуков прекоммита:***
```bash
pre-commit install
```

### Запуск в режиме разработчика

Выполнение миграций (из директории с manage.py):
```bash
python manage.py migrate
```

Сбор статики (из директории с manage.py):
```bash
python manage.py collectstatic
```

Загрузка псевдоданных (из директории с manage.py и data_dump.json; логин и пароль админа: admin 123):
```bash
python manage.py loaddata data_dump.json
```

Создание нового админа (из директории с manage.py):
```bash
python manage.py makesuperuser
```

Добавить файл .env в директорию проекта, заполнить по примеру example.env

Запуск в режиме разработчика (из директории с manage.py):
```bash
python manage.py runserver
```

## Запуск проекта в контейнерах

Добавить файл .env в директорию с файлом docker-compose.yaml, заполнить по примеру infra/example.env

Запуск контейнеров (из директории с файлом docker-compose.yaml):
```bash
docker-compose up -d --build | docker compose up -d --build
```

## Документация

Доступна на эндпоинтах
```
api/schema/docs/
```
