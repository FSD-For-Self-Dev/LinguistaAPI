"""Фильтры приложения words."""

import django_filters as df

from .models import Word


class WordFilter(df.FilterSet):
    """Фильтр модели слова"""

    having_tag = df.Filter(field_name="tags", lookup_expr='in')
    created_after = df.Filter(field_name="created", lookup_expr='date__gte')
    created_before = df.Filter(field_name="created", lookup_expr='date__lt')
    created = df.Filter(field_name="created", lookup_expr='date__exact')
    min_trnsl_count = df.Filter(field_name="trnsl_count", lookup_expr='gte')
    max_trnsl_count = df.Filter(field_name="trnsl_count", lookup_expr='lte')
    min_exmpl_count = df.Filter(field_name="exmpl_count", lookup_expr='gte')
    max_exmpl_count = df.Filter(field_name="exmpl_count", lookup_expr='lte')

    class Meta:
        model = Word
        fields = ['status', 'type', 'language', 'created']
