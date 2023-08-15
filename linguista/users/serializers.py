''' Users serializers '''

from django.contrib.auth import get_user_model

from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    '''Сериализатор модели пользователя.'''

#     is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
        )

#     def get_is_subscribed(self, obj):
#         user = self.context['request'].user
#         return (
#             user.is_authenticated
#             and Follow.objects.filter(user=user, following=obj).exists()
#         )
