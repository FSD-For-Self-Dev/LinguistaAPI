"""Users app serializers."""

from django.contrib.auth import get_user_model

from rest_framework import serializers

from ..core.serializers_mixins import HybridImageSerializerMixin

User = get_user_model()


class UserListSerializer(HybridImageSerializerMixin, serializers.ModelSerializer):
    """Serializer to list users."""

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'image',
            'image_height',
            'image_width',
        )
        read_only_fields = (
            'id',
            'image_height',
            'image_width',
        )
