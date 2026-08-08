# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_staff']
        read_only_fields = ['id', 'email'] 

    def validate_first_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("نام باید حداقل 3 حرف باشد.")
        return value

