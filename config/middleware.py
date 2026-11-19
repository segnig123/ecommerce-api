import logging

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class ExceptionLoggingMiddleware(MiddlewareMixin):

    def process_exception(self, request, exception):
        logger.exception(
            "API ERROR: %s %s",
            request.method,
            request.path,
            exc_info=(
                type(exception),
                exception,
                exception.__traceback__,
            ),
        )
        return None