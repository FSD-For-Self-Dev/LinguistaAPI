# Развёртывание проекта на Ubuntu (reg.ru)

## Первичная настройка

### Закажите на reg.ru облачный сервер на Ubuntu

### Привяжите к серверу ваш ssh ключ

### Подключитесь к серверу через bash и авторизируйтесь
```bash
ssh root@ip_вашего_сервера
```

### Обновите пакетный менеджер
```bash
sudo apt update
sudo apt upgrade
```

### Установите необходимые пакеты
```bash
sudo apt install python3-venv python3-pip git -y
```

### Клонируйте репозиторий GitHub
```bash
git clone https://github.com/FSD-For-Self-Dev/LinguistaAPI.git
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

### Создайте файл окружения .env и заполните его по примеру [example_prod.env](https://github.com/FSD-For-Self-Dev/LinguistaAPI/blob/develop/src/example_prod.env)
```bash
neno .env
```

## Создание базы данных Postgresql

### Настройте локализацию
```bash
locale  # проверка текущих настроек локализации
sudo dpkg-reconfigure locales  # изменение настроек локализации
sudo reboot  # перезапуск сервера
```

### Установите необходимые для работы PostgreSQL пакеты
```bash
sudo apt install postgresql postgresql-contrib -y
```

После установки пакетов в операционной системе будет автоматически создан пользователь postgres, который имеет все права для работы с PostgreSQL: от его имени запускаются все процессы, обслуживающие базу данных, и ему принадлежат все файлы, относящиеся к ней.

После установки автоматически создаётся юнит для сервера PostgreSQL и настраивается его конфигурация: это значит, что демон systemd будет поддерживать постоянную работу сервера PostgreSQL и автоматически загружать его при каждом запуске системы.

Логи БД лежат по адресу /var/log/postgresql/postgresql-12-main.log. В зависимости от версии имя файла может отличаться, в примере имя файла соответствует двенадцатой версии PostgreSQL.

### От имени пользователя postgres переключитесь на управление СУБД psql
```bash
sudo -u postgres psql
```

### Задайте свой пароль для пользователя postgres
```psql
ALTER USER postgres WITH PASSWORD 'postgres_password';
```

### Создайте БД
```psql
CREATE DATABASE linguista_db;
```

### Посмотреть список всех БД на сервере можно по команде \l, выйти из просмотра по команде \q
```psql
\l
```

### Выйдите из psql
```psql
\q
```

### Вернитесь в директорию с файлом manage.py и обновите .env
```bash
cd LinguistaAPI/src
nano .env
```

#### Укажите данные для подключения к вашей БД
```
DB_NAME=linguista_db
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres_password
```

### Выполните миграции
```bash
python manage.py migrate
```

### Заполните БД тестовыми данными
```bash
python manage.py loaddata test_data.json
```

### Соберите статические файлы
```bash
python manage.py collectstatic
```

### Резервное копирование можно выполнить с помощью встроенной утилиты pg_dump
```bash
sudo -u postgres pg_dump linguista_db > linguista_db.dump
```

## Запуск WSGI-сервера Gunicorn

### Установите gunicorn
```bash
pip install gunicorn
```

### Настройте юнит gunicorn для автоматического запуска
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

#### В этом файле опишите конфигурацию юнита
```
[Unit]
# это текстовое описание юнита, пояснение для разработчика
Description=gunicorn daemon

# при старте операционной системы запускать процесс только после того,
# как операционная система загрузится и настроит подключение к сети
After=network.target

[Service]
# от чьего имени запускать процесс:
# укажите имя, под которым вы подключались к серверу
User=<имя-пользователя-в-системе>

# адрес к директории, где установлен Gunicorn
WorkingDirectory=/home/<имя-пользователя-в-системе>/
<директория-с-проектом>/<директория-с-файлом-manage.py>/

# команду, которую вы запускали руками, теперь будет запускать systemd:
# в указанной директории будет выполнена команда bind
# и по запросу к 127.0.0.1:8000 будет выполнен файл запуска приложения config.wsgi
ExecStart=/home/<имя-пользователя-в-системе>/
<директория-с-проектом>/<путь-до-gunicorn-в-виртуальном-окружении> --bind 127.0.0.1:8000 config.wsgi:application

[Install]
# группировка юнитов
WantedBy=multi-user.target
```

#### Узнать путь до gunicorn можно по команде which
```bash
which gunicorn
```

### Запустите юнит gunicorn
```bash
sudo systemctl start gunicorn
```

### Добавьте юнит gunicorn в список автозапуска операционной системы
```bash
sudo systemctl enable gunicorn
```

### Проверьте работоспособность запущенного демона
```bash
sudo systemctl status gunicorn
```

#### Управлять юнитом можно командами sudo systemctl start/stop/restart

## Настройка HTTP-сервера nginx

### Установите nginx
```bash
sudo apt install nginx -y
```

### Настройте файрвол
```bash
sudo ufw allow 'Nginx Full'  # разрешает принимать запросы на порты — 80 и 443: на них по умолчанию приходят запросы по HTTP и HTTPS
sudo ufw allow OpenSSH  # открывает порт 22 — это стандартный порт для соединения по SSH. Если этот порт не открыть, то после запуска файрвола доступ по SSH будет заблокирован: замок защёлкнется, а ключ останется внутри
```

### Включите файрвол
```bash
sudo ufw enable
```

### Проверьте внесённые изменения
```bash
sudo ufw status
```

### Настройте юнит nginx
```bash
sudo nano /etc/nginx/sites-enabled/default
```

#### Добавьте свои инструкции для nginx
```
server {
    # следить за портом 80 на сервере с IP <ваш-ip>
    listen 80;
    server_name <ваш-ip>;

    # если в адресе запроса есть аргумент '/static/' (STATIC_URL в настройках проекта) - вернуть файл из этой директории
    location /static/ {
        root /home/<имя_пользователя>/<название_проекта>/<папка_где_manage.py>/;
    }

    # медиа файлы (MEDIA_URL в настройках проекта)
    location /media/ {
        root /home/<имя_пользователя>/<название_проекта>/<папка_где_manage.py>/;
    }

    # любой другой запрос передать серверу Gunicorn
    location / {
        include proxy_params;
        # передавать запросы нужно на внутренний IP на порт 8000
        proxy_pass http://127.0.0.1:8000;
    }
}
```

#### Проверьте внесенные изменения
```bash
sudo nginx -t

# текст успешной проверки:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### Перезапустите все службы
```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
sudo systemctl status gunicorn  # убедиться что gunicorn активен
sudo systemctl reload nginx
```

## Основные работы на сервере проведены. Далее дополнительные разделы.

## Дополнительно: Разделение прав пользователей

### Разделение администраторов и разработчиков

#### Создайте группу разработчиков
```bash
sudo groupadd developer
sudo usermod -aG developer user  # добавляет пользователя user в группу developer; будьте внимательны к регистру: ключ -g заменит главную группу пользователя (группу по умолчанию), и пользователь может потерять доступ к своим файлам
```

#### Дайте группе developer полный доступ к директории с проектом и закройте доступ для других директорий
```bash
chgrp developer /home/root/LinguistaAPI/  # сделать developer группой директории с кодом
chmod -R 775 /home/root/LinguistaAPI/  # дать права группе на внесения изменений
```

Информация о группах хранится в файле /etc/group
Информация о пользователях хранится в файле /etc/passwd
Команда ps (англ. process status — «состояние процесса») выведет на экран список запущенных процессов.

## Дополнительно: Шифрование https

### Получение и настройка SSL-сертификата

#### Установка certbot
```bash
sudo apt install snapd
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

#### Получение сертификата
```bash
sudo certbot --nginx
```

#### Перезапустите nginx
```bash
sudo systemctl reload nginx
```

Бесплатный сертификат нужно обновлять минимум раз в три месяца. Certbot делает это по умолчанию, если вы не меняли стандартных настроек. Убедиться, что всё обновляется, можно с помощью команды
```bash
sudo certbot renew --dry-run
```

Если по каким-то причинам автообновление не происходит, то можно выполнить следующую команду
```bash
sudo certbot renew --pre-hook "service nginx stop" --post-hook "service nginx start"
```

## Дополнительно: Деплой с помощью DockerHub

### Установите на свой сервер Docker
```bash
sudo apt install docker.io
```

### Авторизируйтесь в DockerHub
```bash
sudo docker login
```

### Выполните pull образа с DockerHub
```bash
sudo docker pull <имя-пользователя>/<имя-репозитория>
```

### Остановите и перезапустите контейнеры
```bash
sudo docker stop $(sudo docker ps -a -q)
sudo docker run --rm -d -p 5000:5000 <имя-пользователя>/<имя-репозитория>
```

## Дополнительно: Деплой с помощью git pull

### Подтяните изменения из репозитория
```bash
git pull
```

### Перейдите в директорию с файлом build.sh и выполните build-скрипт
```bash
sudo chmod +x build.sh  # добавить разрешение на исполнение скрипта
sudo ./build.sh
```

### Перезапустите все службы
```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
sudo systemctl status gunicorn  # убедиться что gunicorn активен
sudo systemctl reload nginx
```
