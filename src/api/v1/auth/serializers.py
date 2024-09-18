"""Authentication custom serializers."""

from django.utils.translation import gettext as _

from dj_rest_auth.serializers import LoginSerializer
from rest_framework import serializers


class CustomLoginSerializer(LoginSerializer):
    """Serializer to log in user."""

    def validate(self, attrs):
        username = attrs.get('username', None)
        email = attrs.get('email', None)

        if not (username or email):
            if username is None:
                raise serializers.ValidationError(
                    {
                        'username': [
                            serializers.Field.default_error_messages.get(
                                'required', _('This field may not be blank.')
                            )
                        ]
                    }
                )
            raise serializers.ValidationError(
                {
                    'username': [
                        serializers.CharField.default_error_messages.get(
                            'blank', _('This field may not be blank.')
                        )
                    ]
                }
            )

        return super().validate(attrs)
