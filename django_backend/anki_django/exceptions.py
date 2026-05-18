"""Shared DRF exception formatting."""
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    request = context.get("request")
    if response is not None and request and request.path.startswith("/api/v1/") and response.status_code == 400:
        response.status_code = 422
        response.data = {"detail": response.data, "type": "validation_error"}
    return response
