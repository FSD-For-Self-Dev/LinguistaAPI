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

### Создайте и активируйте виртуальное окружение
```bash
python3 -m venv venv
. venv/bin/activate
```

### Установите зависимости
```bash
python -m pip install -r requirements.txt
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
python manage.py loaddata test_data.json
```

### Соберите статические файлы
```bash
python manage.py collectstatic
```

## Создайте администратора
```bash
poetry run python manage.py createsuperuser --username admin --password 123
```

## Запустите сервер в режиме разработчика
```bash
poetry run python manage.py runserver 127.0.0.1:8000
```
