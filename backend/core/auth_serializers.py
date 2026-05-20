from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login with email instead of username."""

    username_field = User.EMAIL_FIELD
