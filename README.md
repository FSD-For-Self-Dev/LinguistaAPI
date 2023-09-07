# API for Linguista
backend | rest api

<!-- [![CI](https://github.com/FSD-For-Self-Dev/LinguistaAPI/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/FSD-For-Self-Dev/LinguistaAPI/actions/workflows/main.yml) -->

## Описание

Платформа для помощи в самообучении иностранным языкам и пополнении словарного запаса

## Запуск проекта в режиме разработчика

Выполнить из директории проекта

```
python -m venv venv
. venv/Sctipts/actvate | source venv/Scripts/activate
python -m pip install --upgrade pip
```

Выполнить из директории с requirements.txt для установки зависимостей

```
pip install -r requirements.txt
```

Выполнить миграции из директории с manage.py

```
py manage.py makemigrations
py manage.py migrate
```

Добавить админа

```
py manage.py makesuperuser
```

Добавить файл .env в директорию проекта, заполнить по примеру example.env

Запустить в режиме разработчика

```
py manage.py runserver
```

## Запуск проекта в контейнерах

Выполнить из директории с файлом docker-compose.yaml

```
docker-compose up -d --build
```

## Документация

Доступна на эндпоинтах

```
api/schema/docs/
```
