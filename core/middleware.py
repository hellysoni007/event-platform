import logging
import time
import uuid

from core.request_context import request_id_var

logger = logging.getLogger(__name__)


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.request_id = request_id
        request_id_var.set(request_id)
        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.monotonic()
        response = self.get_response(request)
        duration_ms = int((time.monotonic() - started) * 1000)
        user_id = request.user.id if getattr(request, "user", None) and request.user.is_authenticated else None
        logger.info(
            "request.complete",
            extra={
                "request_id": getattr(request, "request_id", ""),
                "path": request.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "user_id": user_id,
            },
        )
        return response
