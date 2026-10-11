from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from fleet.models import Car

from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    refund_amount = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "car",
            "start_date",
            "end_date",
            "total_price",
            "status",
            "payment_status",
            "cancelled_at",
            "cancellation_fee",
            "refund_amount",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "total_price",
            "status",
            "payment_status",
            "cancelled_at",
            "cancellation_fee",
            "refund_amount",
            "created_at",
        ]

    def get_refund_amount(self, booking):
        if booking.payment_status == Booking.PaymentStatus.REFUNDED:
            return booking.total_price - booking.cancellation_fee
        return Decimal("0.00")

    def validate(self, attrs):
        if attrs["start_date"] < timezone.localdate():
            raise serializers.ValidationError(
                {"start_date": "Start date cannot be in the past."}
            )
        if attrs["end_date"] <= attrs["start_date"]:
            raise serializers.ValidationError(
                {"end_date": "End date must be after the start date."}
            )
        if attrs["car"].status != Car.Status.AVAILABLE:
            raise serializers.ValidationError(
                {"car": "This car is not available for booking."}
            )
        return attrs
