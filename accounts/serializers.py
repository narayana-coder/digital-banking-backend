from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    pin = serializers.CharField(write_only=True, min_length=4, max_length=4)
    confirm_pin = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone', 'password', 'confirm_password', 'pin', 'confirm_pin']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        if data['pin'] != data['confirm_pin']:
            raise serializers.ValidationError({"pin": "PINs do not match."})
        if not data['pin'].isdigit():
            raise serializers.ValidationError({"pin": "PIN must contain digits only."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data.pop('confirm_pin')
        pin = validated_data.pop('pin')
        password = validated_data.pop('password')

        user = User(**validated_data)
        user.set_password(password)
        user.pin = make_password(pin)
        user.is_verified = False
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'phone', 'account_number', 'is_verified', 'date_joined']
        read_only_fields = ['account_number', 'email', 'is_verified', 'date_joined']


class ChangePinSerializer(serializers.Serializer):
    old_pin = serializers.CharField(min_length=4, max_length=4)
    new_pin = serializers.CharField(min_length=4, max_length=4)
    confirm_pin = serializers.CharField(min_length=4, max_length=4)

    def validate(self, data):
        if not data['old_pin'].isdigit():
            raise serializers.ValidationError({"old_pin": "PIN must be digits only."})
        if data['new_pin'] != data['confirm_pin']:
            raise serializers.ValidationError({"new_pin": "New PINs do not match."})
        if not data['new_pin'].isdigit():
            raise serializers.ValidationError({"new_pin": "PIN must be digits only."})
        return data
