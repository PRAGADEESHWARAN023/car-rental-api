from rest_framework import mixins, viewsets

from .models import Car
from .permissions import IsStaffOrReadOnly, is_fleet_staff
from .serializers import CarSerializer


class CarViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CarSerializer
    permission_classes = [IsStaffOrReadOnly]

    def get_queryset(self):
        cars = Car.objects.order_by("id")
        if is_fleet_staff(self.request.user):
            return cars
        return cars.filter(status=Car.Status.AVAILABLE)
