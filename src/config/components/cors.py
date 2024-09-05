CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost',
    'https://fsd-for-self-dev.github.io',
    'http://localhost:3030',
    'https://linguista.online',
    # Дополнительные разрешенные источники, если есть
]

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
