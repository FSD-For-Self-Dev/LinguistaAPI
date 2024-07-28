"""Request logging."""

import socket
import time
import json
import logging

request_logger = logging.getLogger(__name__)


class RequestLogMiddleware:
    """Request logging middleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.monotonic()
        log_data = {
            'remote_address': request.META['REMOTE_ADDR'],
            'server_hostname': socket.gethostname(),
            'request_method': request.method,
            'request_path': request.get_full_path(),
        }

        # Only log requests with "/api/" in path
        if '/api/' in str(request.get_full_path()):
            try:
                req_body = (
                    json.loads(request.body.decode('utf-8')) if request.body else {}
                )
                log_data['request_body'] = req_body
            except json.JSONDecodeError:
                pass

        # Pass request to controller
        response = self.get_response(request)

        # Add runtime to log_data
        if (
            response
            and 'content-type' in response
            and response['content-type'] == 'application/json'
        ):
            response_body = json.loads(response.content.decode('utf-8'))
            log_data['response_body'] = response_body
            log_data['run_time'] = time.time() - start_time

        request_logger.info(msg=log_data)

        return response
