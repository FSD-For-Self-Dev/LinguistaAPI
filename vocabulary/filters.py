import django_filters as df
from .models import Collection


class CollectionFilter(df.FilterSet):
    """Фильтры коллекций."""

    words_count__gt = df.NumberFilter(field_name='words_count',
                                       lookup_expr='gt')
    words_count__lt = df.NumberFilter(field_name='words_count',
                                       lookup_expr='lt')

    class Meta:
        model = Collection
        fields = {
            'created': [
                'exact', 'gt', 'lt', 'year', 'year__gt', 'year__lt',
                'month', 'month__gt', 'month__lt'
            ],
        }
