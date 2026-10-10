from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User=get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model=User
        fields=["id", "email", "password", "first_name", "last_name", "phone"]
        read_only_fields=["id"]

    def validate(self, attrs):
        candidate=User(**{k: v for k, v in attrs.items() if k != "password"})
        validate_password(attrs["password"], user=candidate)
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=["id", "email", "first_name", "last_name", "phone", "role"]
        read_only_fields=fields
