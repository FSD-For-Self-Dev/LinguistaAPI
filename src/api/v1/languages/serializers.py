"""Languages app serializers."""

from collections import OrderedDict

from rest_framework import serializers
from drf_extra_fields.relations import PresentableSlugRelatedField
from drf_spectacular.utils import extend_schema_field

from apps.languages.models import (
    Language,
    LanguageCoverImage,
    UserLearningLanguage,
    UserNativeLanguage,
)
from apps.core.constants import ExceptionDetails, ExceptionCodes

from ..core.serializers_fields import (
    CapitalizedCharField,
    CurrentObjectDefault,
    CustomHybridImageField,
)
from ..core.serializers_mixins import (
    CountObjsSerializerMixin,
    AlreadyExistSerializerHandler,
    HybridImageSerializerMixin,
)


class LanguageSerializer(serializers.ModelSerializer):
    """Serializer to list languages."""

    name = CapitalizedCharField()
    name_local = CapitalizedCharField()

    class Meta:
        model = Language
        fields = (
            'name',
            'name_local',
            'isocode',
            'flag_icon',
        )
        read_only_fields = fields


class LearningLanguageListSerailizer(
    CountObjsSerializerMixin, serializers.ModelSerializer
):
    """Serializer to list users's learning languages."""

    language = PresentableSlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='isocode',
        required=True,
        presentation_serializer=LanguageSerializer,
    )
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    words_count = serializers.SerializerMethodField('get_words_count')
    inactive_words_count = serializers.SerializerMethodField('get_inactive_words_count')
    active_words_count = serializers.SerializerMethodField('get_active_words_count')
    mastered_words_count = serializers.SerializerMethodField('get_mastered_words_count')
    cover = serializers.ImageField(source='cover.image', read_only=True)
    cover_id = serializers.CharField(source='cover.id', read_only=True)
    cover_height = serializers.SerializerMethodField('get_cover_height')
    cover_width = serializers.SerializerMethodField('get_cover_width')

    class Meta:
        model = UserLearningLanguage
        fields = (
            'id',
            'user',
            'language',
            'cover',
            'cover_id',
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
            'cover_id',
            'cover_height',
            'cover_width',
            'words_count',
            'inactive_words_count',
            'active_words_count',
            'mastered_words_count',
        )

    @extend_schema_field({'type': 'integer'})
    def get_cover_height(self, obj: UserLearningLanguage) -> int | None:
        try:
            return obj.cover.image.height
        except AttributeError:
            return None

    @extend_schema_field({'type': 'integer'})
    def get_cover_width(self, obj: UserLearningLanguage) -> int | None:
        try:
            return obj.cover.image.width
        except AttributeError:
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


class LearningLanguageSerializer(
    AlreadyExistSerializerHandler,
    LearningLanguageListSerailizer,
):
    """Serializer to retrieve users's learning language details."""

    already_exist_detail = ExceptionDetails.Languages.LEARNING_LANGUAGE_ALREADY_EXIST

    class Meta:
        model = UserLearningLanguage
        fields = (
            'id',
            'slug',
            'user',
            'language',
            'level',
            'cover',
            'cover_id',
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
            'cover_id',
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
            {'language': ExceptionDetails.Languages.LANGUAGE_NOT_AVAILABLE}
        )

    def create(self, validated_data):
        """Set default cover image for learning language."""
        instance: UserLearningLanguage = super().create(validated_data)

        default_cover_image: LanguageCoverImage = LanguageCoverImage.objects.filter(
            language=instance.language
        ).last()
        if default_cover_image:
            instance.cover = default_cover_image
            instance.save()

        return instance


class NativeLanguageSerailizer(serializers.ModelSerializer):
    """Serializer to list, create users's native languages."""

    language = LanguageSerializer(many=False, read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UserNativeLanguage
        fields = (
            'user',
            'language',
        )


class CoverListSerializer(HybridImageSerializerMixin):
    """Serializer to list available images for given language."""

    language = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
    )
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
    )

    class Meta:
        model = LanguageCoverImage
        fields = (
            'id',
            'language',
            'image',
            'image_height',
            'image_width',
            'author',
        )
        read_only_fields = fields


class CoverSetSerializer(AlreadyExistSerializerHandler, serializers.ModelSerializer):
    """
    Serializer to use for setting new cover image for user's learning language.
    """

    id = serializers.CharField(required=False)
    image = CustomHybridImageField(required=False)
    language = serializers.HiddenField(
        default=CurrentObjectDefault(
            object_lookup_model=Language,
            object_lookup_field='isocode',
        )
    )
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = LanguageCoverImage
        fields = (
            'id',
            'image',
            'language',
            'author',
        )

    def validate(self, attrs):
        image = attrs.get('image', None)
        image_id = attrs.get('id', None)
        if image is None and image_id is None:
            raise serializers.ValidationError(
                detail=ExceptionDetails.Images.IMAGE_FILE_OR_ID_IS_REQUIRED,
                code=ExceptionCodes.Images.IMAGE_FILE_OR_ID_IS_REQUIRED,
            )
        return super().validate(attrs)
