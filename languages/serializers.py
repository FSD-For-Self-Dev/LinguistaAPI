"""Languages serializers."""

from rest_framework import serializers

from .models import Language


class LanguageSerailizer(serializers.ModelSerializer):
    """Сериализатор языков."""

    class Meta:
        model = Language
        fields = (
            'id',
            'name',
            'flag_icon',
        )
        read_only_fields = (
            'id',
            'flag_icon',
        )
