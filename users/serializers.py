"""Users serializers."""

from collections import OrderedDict

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

from rest_framework import serializers
from drf_extra_fields.fields import HybridImageField
from drf_extra_fields.relations import PresentableSlugRelatedField
from drf_spectacular.utils import extend_schema_field

from languages.models import Language
from languages.serializers import LanguageSerializer
from core.serializers_mixins import CountObjsSerializerMixin
from core.serializers_fields import KwargsMethodField

from .models import UserLearningLanguage, UserNativeLanguage

User = get_user_model()


class UserShortSerializer(serializers.ModelSerializer):
    """Serializer to list users."""

    image = HybridImageField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'image',
        )
        read_only_fields = ('id',)


class LearningLanguageShortSerailizer(
    CountObjsSerializerMixin, serializers.ModelSerializer
):
    """Serializer to list users's learning languages."""

    words_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='words',
    )
    language = PresentableSlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        required=True,
        presentation_serializer=LanguageSerializer,
    )
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    words_count = serializers.SerializerMethodField('get_words_count')
    inactive_words_count = serializers.SerializerMethodField('get_inactive_words_count')
    active_words_count = serializers.SerializerMethodField('get_active_words_count')
    mastered_words_count = serializers.SerializerMethodField('get_mastered_words_count')
    cover_height = serializers.SerializerMethodField('get_cover_height')
    cover_width = serializers.SerializerMethodField('get_cover_width')

    class Meta:
        model = UserLearningLanguage
        fields = (
            'id',
            'user',
            'language',
            'cover',
            'cover_height',
            'cover_width',
            'words_count',
            'inactive_words_count',
            'active_words_count',
            'mastered_words_count',
        )
        read_only_fields = (
            'id',
            'cover',
            'cover_height',
            'cover_width',
            'words_count',
            'inactive_words_count',
            'active_words_count',
            'mastered_words_count',
        )

    @extend_schema_field({'type': 'int'})
    def get_cover_height(self, obj: UserLearningLanguage) -> int | None:
        try:
            return obj.cover.height
        except ValueError:
            return None

    @extend_schema_field({'type': 'int'})
    def get_cover_width(self, obj: UserLearningLanguage) -> int | None:
        try:
            return obj.cover.width
        except ValueError:
            return None

    @extend_schema_field({'type': 'integer'})
    def get_words_count(self, obj: UserLearningLanguage) -> int:
        """Returns words amount in given language."""
        return obj.user.words.filter(language=obj.language).count()

    @extend_schema_field({'type': 'integer'})
    def get_inactive_words_count(self, obj: UserLearningLanguage) -> int:
        """Returns words with `Inactive` activity status amount in given language."""
        return obj.user.words.filter(language=obj.language, activity_status='I').count()

    @extend_schema_field({'type': 'integer'})
    def get_active_words_count(self, obj: UserLearningLanguage) -> int:
        """Returns words with `Active` activity status amount in given language."""
        return obj.user.words.filter(language=obj.language, activity_status='A').count()

    @extend_schema_field({'type': 'integer'})
    def get_mastered_words_count(self, obj: UserLearningLanguage) -> int:
        """Returns words with `Mastered` activity status amount in given language."""
        return obj.user.words.filter(language=obj.language, activity_status='M').count()


class LearningLanguageSerailizer(LearningLanguageShortSerailizer):
    """Serializer to retrieve users's learning language details."""

    class Meta:
        model = UserLearningLanguage
        fields = (
            'id',
            'slug',
            'user',
            'language',
            'level',
            'cover',
            'cover_height',
            'cover_width',
            'words_count',
            'inactive_words_count',
            'active_words_count',
            'mastered_words_count',
        )
        read_only_fields = (
            'id',
            'slug',
            'cover',
            'cover_height',
            'cover_width',
            'words_count',
            'inactive_words_count',
            'active_words_count',
            'mastered_words_count',
        )

    def validate(self, attrs: dict) -> OrderedDict:
        """Check that language is available for adding to learning."""
        if attrs.get('language', None) in Language.objects.filter(
            learning_available=True
        ):
            return super().validate(attrs)
        raise serializers.ValidationError(
            {'language': _('The selected language is not yet able for learning.')}
        )


class NativeLanguageSerailizer(serializers.ModelSerializer):
    """Serializer to list, create users's native languages."""

    language = PresentableSlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        required=True,
        presentation_serializer=LanguageSerializer,
    )
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UserNativeLanguage
        fields = (
            'user',
            'language',
        )
