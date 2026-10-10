from rest_framework import mixins, viewsets

from fleet.permissions import is_fleet_staff

from .models import Booking
from .serializers import BookingSerializer
from .services import create_booking


class BookingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = BookingSerializer

    def get_queryset(self):
        bookings = Booking.objects.order_by("-id")
        if is_fleet_staff(self.request.user):
            return bookings
        return bookings.filter(user=self.request.user)

    def perform_create(self, serializer):
        data = serializer.validated_data
        serializer.instance = create_booking(
            user=self.request.user,
            car=data["car"],
            start_date=data["start_date"],
            end_date=data["end_date"],
        )
