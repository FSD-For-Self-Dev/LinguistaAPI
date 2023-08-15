''' Custom pagination '''

from rest_framework.pagination import PageNumberPagination


class LimitPagination(PageNumberPagination):
    page_size = 100
    page_query_param = 'page'
    page_size_query_param = 'limit'
    max_page_size = 1000
