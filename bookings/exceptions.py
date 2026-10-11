from rest_framework import status
from rest_framework.exceptions import APIException


class CarNotAvailable(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The car is not available for these dates."
    default_code = "car_not_available"


class BookingNotCancellable(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This booking cannot be cancelled."
    default_code = "booking_not_cancellable"
