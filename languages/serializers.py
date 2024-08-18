"""Languages serializers."""

from rest_framework import serializers

from .models import Language


class LanguageSerializer(serializers.ModelSerializer):
    """Serializer to list languages."""

    class Meta:
        model = Language
        fields = (
            'id',
            'name',
            'name_local',
            'flag_icon',
        )
        read_only_fields = fields
