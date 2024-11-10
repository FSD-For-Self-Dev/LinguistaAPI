# Развёртывание проекта локально

### Клонируйте репозиторий
```bash
git clone https://github.com/huggerkios/my_cloud_api.git
cd my_cloud_api
```

### Перейдите в папку репозитория с файлом manage.py
```bash
cd LinguistaAPI/src
```

### Создайте и активируйте виртуальное окружение poetry
```bash
poetry env use python
. venv/bin/activate
```

### Установите зависимости
```bash
poetry install
```

## Создайте файл .env по примеру [example.env](https://github.com/FSD-For-Self-Dev/LinguistaAPI/blob/develop/src/example.env)
```bash
nano .env
```

## Выполните миграции
```bash
poetry run python manage.py migrate
```

### Заполните БД тестовыми данными
```bash
poetry run python manage.py loaddata test_data.json
```

### Соберите статические файлы
```bash
poetry run python manage.py collectstatic
```

## Создайте администратора
```bash
poetry run python manage.py createsuperuser --username admin --password 123
```

## Запустите сервер в режиме разработчика
```bash
poetry run python manage.py runserver 127.0.0.1:8000
```

## Установите хуки пре коммита
```bash
pre-commit install
```
