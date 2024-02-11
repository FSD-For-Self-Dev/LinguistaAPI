# API for Linguista
backend | rest api

<!-- [![CI](https://github.com/FSD-For-Self-Dev/LinguistaAPI/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/FSD-For-Self-Dev/LinguistaAPI/actions/workflows/main.yml) -->

## Описание

Платформа для помощи в самообучении иностранным языкам и пополнении словарного запаса

## Запуск проекта в режиме разработчика

### Создание окружения poetry

Установка poetry:
```bash
pip install poetry | pip3 install poetry
```

Проверка установки poetry:
```bash
poetry --version
```

Создание виртуального окружения:
+ Если python3.11 есть в PATH:
```bash
poetry env use python3.11
```
+ Через полный путь:
```bash
poetry env use /path/to/python
```

Проверка активированного окружения:
```bash
poetry env info
```

Установка зависимостей (для разработки):
```bash
poetry install --with dev --no-root
```

***Установка хуков прекоммита:***
```bash
poetry run pre-commit install
```

### Для справки, работа с зависимостями в poetry

Добавление нового пакета:
```bash
poetry add package
```

Обновление версии пакета:
```bash
poetry update package
```

Удаление пакета:
```bash
poetry remove package
```

Cведения обо всех установленных пакетах:
```bash
poetry show --tree
```

### Запуск в режиме разработчика

*Добавить файл .env в директорию проекта, заполнить по примеру example.env*

Выполнение миграций (из директории с manage.py):
```bash
poetry run python manage.py migrate
```

Сбор статики (из директории с manage.py):
```bash
poetry run python manage.py collectstatic
```

Загрузка псевдоданных (из директории с manage.py и data_dump.json; логин и пароль админа: admin 123):
```bash
poetry run python manage.py loaddata data_dump.json
```

Создание нового админа (из директории с manage.py):
```bash
poetry run python manage.py makesuperuser
```

Запуск в режиме разработчика (из директории с manage.py):
```bash
poetry run python manage.py runserver
```

## Запуск проекта в контейнерах

*Добавить файл .env в директорию с файлом docker-compose.yaml, заполнить по примеру infra/example.env*

Запуск контейнеров (из директории с файлом docker-compose.yaml):
```bash
docker-compose up -d --build
```
или
```bash
docker compose up -d --build
```

## Документация

Доступна на эндпоинтах
```
api/schema/docs/
```
