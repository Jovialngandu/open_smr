from rest_framework import serializers, status
from django.contrib.auth import get_user_model


User = get_user_model()

class UserSearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Terme de recherche sur le username ou l’email.',
    )


class UserSearchResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
