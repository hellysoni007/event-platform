from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from core.error_codes import ErrorCodes


class DomainError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Domain validation failed."
    default_code = ErrorCodes.BAD_REQUEST

    def __init__(self, detail=None, code=None, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail=detail, code=code or self.default_code)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return Response(
            {"detail": "Internal server error.", "code": ErrorCodes.INTERNAL_ERROR},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, ValidationError):
        detail = "Validation error."
        code = ErrorCodes.VALIDATION_ERROR
    elif isinstance(exc, APIException):
        detail = response.data.get("detail", "Request failed.")
        resolved_code = exc.get_codes()
        if isinstance(resolved_code, dict):
            resolved_code = resolved_code.get("detail", ErrorCodes.BAD_REQUEST)
        code = str(resolved_code)
    else:
        detail = response.data.get("detail", "Request failed.")
        code = response.data.get("code", ErrorCodes.BAD_REQUEST)

    if isinstance(detail, (list, dict)):
        detail = "Validation error."

    response.data = {"detail": str(detail), "code": str(code)}
    return response
