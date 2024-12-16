REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_PAGINATION_CLASS': 'api.v1.core.pagination.LimitPagination',
    'PAGE_SIZE': 50,
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M',
    'DEFAULT_SCHEMA_CLASS': 'api.v1.schema.generator.FromDataSchema',
}
