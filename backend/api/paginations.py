from rest_framework.pagination import PageNumberPagination

from recipes.constants import PAGE_SIZE


class Pagination(PageNumberPagination):
    page_size = PAGE_SIZE
    page_query_param = 'page'
    page_size_query_param = 'limit'
