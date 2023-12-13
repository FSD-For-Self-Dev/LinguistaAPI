# schema.py

from drf_spectacular.openapi import AutoSchema
from rest_framework import status

from .serializers import WordShortSerializer
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
)

data = {
    'WordViewSet': {
        'tags': ['vocabulary'],
        'list': {
            'summary': 'Просмотр списка слов из своего словаря',
            'description': (
                'Просмотреть список своих слов с пагинацией и применением '
                'фильтров, сортировки и поиска. Нужна авторизация.'
            ),
            'responses': {status.HTTP_200_OK: WordShortSerializer},
            'parameters': [
                OpenApiParameter(
                    'created',
                    OpenApiTypes.DATETIME,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по дате добавления. Включая сравнение больше и '
                        'меньше: created__gt и created__lt.'
                    ),
                ),
                OpenApiParameter(
                    'created__year',
                    OpenApiTypes.INT,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по году добавления. Включая сравнение больше и '
                        'меньше: created__year__gt и created__year__lt.'
                    ),
                ),
                OpenApiParameter(
                    'created__month',
                    OpenApiTypes.INT,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по месяцу добавления. Включая сравнение больше и '
                        'меньше: created__month__gt и created__month__lt.'
                    ),
                ),
                OpenApiParameter(
                    'language',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=('Фильтр по языку. Принимает isocode языка.'),
                ),
                OpenApiParameter(
                    'is_problematic',
                    OpenApiTypes.BOOL,
                    OpenApiParameter.QUERY,
                    description=('Фильтр по метке "проблемное".'),
                ),
                OpenApiParameter(
                    'tags',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по тегам. Принимает name тегов через запятую, '
                        'если несколько.'
                    ),
                ),
                OpenApiParameter(
                    'activity',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по статусу активности. Принимает варианты '
                        'INACTIVE, ACTIVE, MASTERED.'
                    ),
                ),
                OpenApiParameter(
                    'types',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по типам. Принимает slug типов через запятую, '
                        'если несколько.'
                    ),
                ),
                OpenApiParameter(
                    'first_letter',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=('Фильтр по первой букве слова.'),
                ),
                OpenApiParameter(
                    'translations_count',
                    OpenApiTypes.INT,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по кол-ву переводов. Включая сравнение больше и '
                        'меньше: translations_count__gt и translations_count__lt.'
                    ),
                ),
                OpenApiParameter(
                    'examples_count',
                    OpenApiTypes.INT,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по кол-ву примеров. Включая сравнение больше и '
                        'меньше: examples_count__gt и examples_count__lt.'
                    ),
                ),
            ],
        },
        # other methods
    },
    # other viewsets
}


class CustomSchema(AutoSchema):
    def get_tags(self):
        # return ['Activity']
        return data[self.view.__class__.__name__]['tags']

    def get_description(self):
        return data[self.view.__class__.__name__][self.method.lower()]['description']

    def get_summary(self):
        return data[self.view.__class__.__name__][self.method.lower()]['summary']

    def get_operation_id(self):
        return data[self.view.__class__.__name__][self.method.lower()]['operation_id']
