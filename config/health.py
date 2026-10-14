from django.db import Error, connection
from django.http import JsonResponse


def health(request):
    """Tell a load balancer or uptime monitor whether the app and database answer."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Error:
        return JsonResponse({"status": "unavailable", "database": "down"}, status=503)
    return JsonResponse({"status": "ok", "database": "up"})
