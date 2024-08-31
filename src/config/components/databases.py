import os
import dj_database_url

DATABASE_URL = os.getenv('DATABASE_URL', default='')

DATABASES = {
    'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
    if DATABASE_URL
    else {
        'ENGINE': os.getenv('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME', default='postgres'),
        'USER': os.getenv('DB_USER', default=''),
        'PASSWORD': os.getenv('DB_PASSWORD', default='postgres'),
        'HOST': os.getenv('DB_HOST', default=''),
        'PORT': os.getenv('DB_PORT', default='5432'),
    }
}
