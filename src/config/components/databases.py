import os
import dj_database_url

DATABASE_URL = os.getenv('DATABASE_URL', default='')

DATABASES = {
    'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
    if DATABASE_URL
    else {
        'ENGINE': os.getenv('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME', default='postgres'),
        'USER': os.getenv('DB_USER', default='postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', default='postgres_password'),
        'HOST': os.getenv('DB_HOST', default='localhost'),
        'PORT': os.getenv('DB_PORT', default='5432'),
    }
}
