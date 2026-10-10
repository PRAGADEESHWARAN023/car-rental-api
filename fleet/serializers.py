from rest_framework import serializers

from .models import Car


class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = [
            "id",
            "registration_number",
            "make",
            "model",
            "daily_price",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
