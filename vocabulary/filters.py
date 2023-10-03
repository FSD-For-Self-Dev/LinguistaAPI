import django_filters as df
from django.db.models import Count


class CollectionFilter(df.FilterSet):
    """Collection filter."""
    date_added__gt = df.DateFilter(field_name='created', lookup_expr='gt')
    date_added__lt = df.DateFilter(field_name='created', lookup_expr='lt')
    words_amount__gt = df.NumberFilter(method='filter_words_amount',
                                       lookup_expr='gt')
    words_amount__lt = df.NumberFilter(method='filter_words_amount',
                                       lookup_expr='lt')

    def filter_words_amount(self, queryset, name, value):
        filter = {name: value}
        if value:
            return queryset.annotate(
                words_amount=Count('words',
                                   distinct=True)).filter(**filter)
        return queryset
