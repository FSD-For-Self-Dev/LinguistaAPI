"""Database queries logging."""

import logging

from django.db import connection

queries_logger = logging.getLogger(__name__)


class DatabaseQueriesLogMiddleware:
    """Database queries logging middleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Pass request to controller
        response = self.get_response(request)

        try:
            # Variable to store total execution time
            query_time = 0

            for query in connection.queries:
                # Add the time that the query took to the total
                queries_logger.info(
                    {
                        'query': query['sql'],
                        'execution time': float(query['time']),
                    }
                )
                query_time += float(query['time'])

            queries_logger.info(
                {
                    'total execution time': query_time,
                    'total number of queries': len(connection.queries),
                }
            )
        except Exception:
            pass

        return response
