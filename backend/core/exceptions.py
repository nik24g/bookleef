from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """Return clear JSON errors instead of generic 500s where possible."""
    response = exception_handler(exc, context)
    if response is not None:
        return response

    return None
