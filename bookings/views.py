from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from fleet.permissions import is_fleet_staff

from .models import Booking
from .serializers import BookingSerializer
from .services import cancel_booking, create_booking


class BookingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = BookingSerializer

    def get_queryset(self):
        bookings = Booking.objects.select_related("car", "user").order_by("-id")
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

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()  # 404 unless the caller may see this booking
        cancelled = cancel_booking(booking_id=booking.pk, actor=request.user)
        return Response(self.get_serializer(cancelled).data)
