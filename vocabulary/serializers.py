"""Vocabulary serializers."""

from itertools import chain
from collections import OrderedDict

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from django.db.models import Count, Model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet
from django.db.models.fields.files import ImageFieldFile

from drf_spectacular.utils import extend_schema_field
from drf_extra_fields.fields import HybridImageField
from drf_extra_fields.relations import PresentablePrimaryKeyRelatedField
from rest_framework import serializers
from rest_framework.fields import Field
from rest_framework.utils.serializer_helpers import ReturnDict
from rest_framework.serializers import Serializer

from core.serializers_fields import (
    ReadableHiddenField,
    KwargsMethodField,
)
from core.serializers_mixins import (
    ListUpdateSerializer,
    NestedSerializerMixin,
    FavoriteSerializerMixin,
    CountObjsSerializerMixin,
    AlreadyExistSerializerHandler,
    AmountLimitsSerializerHandler,
    UpdateSerializerMixin,
)
from users.models import UserLearningLanguage
from users.serializers import (
    UserShortSerializer,
    LearningLanguageShortSerailizer,
    LearningLanguageSerailizer,
)
from users.constants import UsersAmountLimits
from languages.models import LanguageImage
from languages.serializers import LanguageSerializer

from .constants import (
    VocabularyAmountLimits,
    MAX_IMAGE_SIZE,
    MAX_IMAGE_SIZE_MB,
)
from .models import (
    Antonym,
    Collection,
    Definition,
    FavoriteCollection,
    FavoriteWord,
    Form,
    FormsGroup,
    Language,
    Note,
    Similar,
    Synonym,
    Tag,
    Type,
    UsageExample,
    Word,
    WordTranslation,
    ImageAssociation,
    QuoteAssociation,
    WordSelfRelatedModel,
    clear_extra_objects,
)

User = get_user_model()


class CurrentWordDefault:
    """
    The current word as the default value for the field.
    Lookup field must be `slug`.
    """

    requires_context = True

    def __call__(self, serializer_field: Field) -> QuerySet[Word] | Word:
        request_word_slug = serializer_field.context['view'].kwargs.get('slug')
        try:
            return Word.objects.get(slug=request_word_slug)
        except KeyError or ObjectDoesNotExist:
            return Word.objects.none()

    def __repr__(self) -> str:
        return '%s()' % self.__class__.__name__


class NativeLanguageDefault:
    """User latest native language as the default value for the field."""

    requires_context = True

    def __call__(self, serializer_field: Field) -> QuerySet[Language] | Language:
        request_user = serializer_field.context['request'].user
        try:
            return request_user.native_languages.latest()
        except KeyError:
            return Language.objects.none()

    def __repr__(self) -> str:
        return '%s()' % self.__class__.__name__


class ValidateLanguageMixin:
    """
    Custom serializer mixin to add a check for whether the given language belongs to
    user's learning or native language.
    """

    def validate_language_is_native_or_learning(
        self, language: Language
    ) -> Language | None:
        """
        Raises ValidationError if language does not belong either to user's
        learning or native languages.
        """
        user = self.context.get('request').user
        if not (
            language in user.native_languages.all()
            or language in user.learning_languages.all()
        ):
            raise serializers.ValidationError(
                _('Language must be in your learning or native languages.'),
                code='invalid_language',
            )
        return language

    def validate_language_is_learning(self, language: Language) -> Language | None:
        """
        Raises ValidationError if language does not belong to user's
        learning languages.
        """
        user = self.context.get('request').user
        if language not in user.learning_languages.all():
            raise serializers.ValidationError(
                _('Language must be in your learning languages.'),
                code='invalid_language',
            )
        return language

    def validate_language_is_native(self, language: Language) -> Language | None:
        """
        Raises ValidationError if language does not belong to user's
        native languages.
        """
        user = self.context.get('request').user
        if language not in user.native_languages.all():
            raise serializers.ValidationError(
                _('Language must be in your native languages.'),
                code='invalid_language',
            )
        return language


class NoteInLineSerializer(AlreadyExistSerializerHandler, serializers.ModelSerializer):
    """Serializer to list, create word notes inside word serializer."""

    id = serializers.IntegerField(required=False)
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
    )
    word = serializers.HiddenField(default=None)

    already_exist_detail = _('Such a note already exists for the word.')

    class Meta:
        model = Note
        list_serializer_class = ListUpdateSerializer
        foreign_key_field_name = 'word'
        fields = (
            'id',
            'slug',
            'text',
            'word',
            'author',
            'created',
            'modified',
        )
        read_only_fields = (
            'slug',
            'word',
            'created',
            'modified',
        )


class WordTranslationInLineSerializer(
    AlreadyExistSerializerHandler, ValidateLanguageMixin, serializers.ModelSerializer
):
    """Serializer to list, create word translations inside word serializer."""

    id = serializers.IntegerField(required=False)
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
    )
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        default=NativeLanguageDefault(),
    )

    already_exist_detail = _(
        'This translation already exists in your vocabulary. Update it?'
    )

    class Meta:
        model = WordTranslation
        list_serializer_class = ListUpdateSerializer
        fields = (
            'id',
            'slug',
            'text',
            'language',
            'author',
            'created',
            'modified',
        )
        read_only_fields = (
            'id',
            'slug',
            'created',
            'modified',
        )

    def validate_language(self, language: Language) -> Language | None:
        return self.validate_language_is_native_or_learning(language)


class UsageExampleInLineSerializer(
    AlreadyExistSerializerHandler, serializers.ModelSerializer
):
    """Serializer to list, create word usage examples inside word serializer."""

    id = serializers.IntegerField(required=False)
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
    )
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        required=True,
    )

    already_exist_detail = _(
        'This example already exists in your vocabulary. Update it?'
    )

    class Meta:
        model = UsageExample
        list_serializer_class = ListUpdateSerializer
        fields = (
            'id',
            'slug',
            'author',
            'language',
            'text',
            'translation',
            'created',
            'modified',
        )
        read_only_fields = (
            'id',
            'slug',
            'created',
            'modified',
        )


class DefinitionInLineSerializer(
    AlreadyExistSerializerHandler, serializers.ModelSerializer
):
    """Serializer to list, create word definitions inside word serializer."""

    id = serializers.IntegerField(required=False)
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
    )
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        required=True,
    )

    already_exist_detail = _(
        'This definition already exists in your vocabulary. Update it?'
    )

    class Meta:
        model = Definition
        list_serializer_class = ListUpdateSerializer
        fields = (
            'id',
            'slug',
            'author',
            'language',
            'text',
            'translation',
            'created',
            'modified',
        )
        read_only_fields = (
            'id',
            'slug',
            'created',
            'modified',
        )


class CollectionShortSerializer(
    FavoriteSerializerMixin,
    AlreadyExistSerializerHandler,
    CountObjsSerializerMixin,
    serializers.ModelSerializer,
):
    """
    Serializer to list, create collections inside word serializer or
    to list, create collections in shortened form.
    """

    id = serializers.IntegerField(required=False)
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
    )
    words_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='words',
    )
    last_3_words = serializers.SerializerMethodField('get_last_3_words')

    already_exist_detail = _(
        'This collection already exists in your vocabulary. Update it?'
    )

    class Meta:
        model = Collection
        list_serializer_class = ListUpdateSerializer
        favorite_model = FavoriteCollection
        favorite_model_field = 'collection'
        fields = (
            'id',
            'slug',
            'author',
            'title',
            'description',
            'favorite',
            'words_count',
            'last_3_words',
            'created',
            'modified',
        )
        read_only_fields = (
            'slug',
            'favorite',
            'words_count',
            'created',
            'modified',
        )

    @extend_schema_field({'type': 'object'})
    def get_last_3_words(self, obj: Collection) -> QuerySet[Word]:
        """Returns list of 3 last added words in the given collection."""
        return obj.words.order_by('-wordsincollections__created').values_list(
            'text', flat=True
        )[:3]


class FormsGroupInLineSerializer(
    AlreadyExistSerializerHandler, serializers.ModelSerializer
):
    """Serializer to list, create word form groups inside word serializer."""

    id = serializers.IntegerField(required=False)
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
    )
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        required=True,
    )

    already_exist_detail = _(
        'This form group already exists in your vocabulary. Update it?'
    )

    class Meta:
        model = FormsGroup
        list_serializer_class = ListUpdateSerializer
        fields = (
            'id',
            'slug',
            'author',
            'name',
            'language',
            'color',
            'translation',
        )
        read_only_fields = (
            'slug',
            'author',
        )

    def validate_name(self, name: str) -> str:
        """Check if name does not match with `Infinitive` before create."""
        if name.capitalize() == 'Infinitive':
            raise serializers.ValidationError(
                _('The forms group `Infinitive` already exists.')
            )
        return name


class ImageInLineSerializer(serializers.ModelSerializer):
    """Serializer to list, create word image-associations inside word serializer."""

    image = HybridImageField()
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
    )
    association_type = serializers.SerializerMethodField(
        'get_association_type',
    )
    image_height = serializers.SerializerMethodField(
        'get_image_height',
    )
    image_width = serializers.SerializerMethodField(
        'get_image_width',
    )

    class Meta:
        model = ImageAssociation
        list_serializer_class = ListUpdateSerializer
        fields = (
            'association_type',
            'id',
            'author',
            'image',
            'image_height',
            'image_width',
            'created',
        )
        read_only_fields = (
            'association_type',
            'id',
            'image_height',
            'image_width',
            'created',
        )

    def validate_image(self, image: ImageFieldFile) -> ImageFieldFile:
        """Check image size."""
        if image.size > MAX_IMAGE_SIZE:
            raise serializers.ValidationError(
                _(f'Image file too large ( > {MAX_IMAGE_SIZE_MB} MB )')
            )
        return image

    @extend_schema_field({'type': 'string'})
    def get_association_type(self, obj: ImageAssociation) -> str:
        """Returns type of represented association"""
        return 'image'

    @extend_schema_field({'type': 'integer'})
    def get_image_height(self, obj: ImageAssociation) -> int | None:
        try:
            return obj.image.height
        except ValueError:
            return None

    @extend_schema_field({'type': 'integer'})
    def get_image_width(self, obj: ImageAssociation) -> int | None:
        try:
            return obj.image.width
        except ValueError:
            return None


class QuoteInLineSerializer(serializers.ModelSerializer):
    """Serializer to list, create word quote-associations inside word serializer."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
    )
    association_type = serializers.SerializerMethodField(
        'get_association_type',
    )

    class Meta:
        model = QuoteAssociation
        list_serializer_class = ListUpdateSerializer
        fields = (
            'association_type',
            'id',
            'text',
            'quote_author',
            'author',
            'created',
        )
        read_only_fields = (
            'association_type',
            'id',
            'created',
        )

    @extend_schema_field({'type': 'string'})
    def get_association_type(self, obj: ImageAssociation) -> str:
        """Returns type of represented association"""
        return 'quote'


class TagSerializer(AlreadyExistSerializerHandler, serializers.ModelSerializer):
    """Serializer to list, create word tags."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
        write_only=True,
    )
    name = serializers.CharField()

    already_exist_detail = _('This tag already exists in your vocabulary. Update it?')

    class Meta:
        model = Tag
        list_serializer_class = ListUpdateSerializer
        fields = ('name', 'author')


class WordSuperShortSerializer(serializers.ModelSerializer):
    """Serializer to list words with no details."""

    author = serializers.SlugRelatedField(slug_field='username', read_only=True)
    language = LanguageSerializer(many=False, read_only=True)

    class Meta:
        model = Word
        fields = (
            'id',
            'slug',
            'language',
            'text',
            'author',
            'created',
            'modified',
        )
        read_only_fields = fields


class WordShortCardSerializer(
    FavoriteSerializerMixin,
    WordSuperShortSerializer,
):
    """Serializer to list words with minimum details."""

    types = serializers.SlugRelatedField(slug_field='name', read_only=True, many=True)
    tags = serializers.SlugRelatedField(slug_field='name', read_only=True, many=True)
    forms_groups = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
        many=True,
    )
    language = serializers.SlugRelatedField(slug_field='name', read_only=True)
    activity_status = serializers.SerializerMethodField('get_activity_status_display')

    class Meta(WordSuperShortSerializer.Meta):
        favorite_model = FavoriteWord
        favorite_model_field = 'word'
        fields = WordSuperShortSerializer.Meta.fields + (
            'types',
            'tags',
            'forms_groups',
            'favorite',
            'is_problematic',
            'activity_status',
            'last_exercise_date',
        )

    @extend_schema_field({'type': 'string'})
    def get_activity_status_display(self, obj: Word) -> str:
        """Get activity status full text for display."""
        return obj.get_activity_status_display()


class GetImagesSerializerMixin(serializers.ModelSerializer):
    """
    Custom serializer mixin to add `images` and `image` field obtained through
    related manager to retrieve one latest image-association or full list.
    Related name for images must be `images_associations`.
    """

    image = serializers.SerializerMethodField('get_last_image')

    images = serializers.SerializerMethodField('get_images')

    @extend_schema_field({'type': 'string'})
    def get_last_image(self, obj: Word) -> str | None:
        """Returns last added image association."""
        try:
            url = obj.images_associations.latest().image.url
            request = self.context.get('request', None)
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        except ObjectDoesNotExist:
            return None
        except ValueError:
            return None

    @extend_schema_field({'type': 'object'})
    def get_images(self, obj: Word) -> list[str]:
        """Returns list of image associations."""
        return obj.images_associations.values_list('image', flat=True)


class WordLongCardSerializer(
    GetImagesSerializerMixin,
    CountObjsSerializerMixin,
    WordShortCardSerializer,
):
    """Serializer to list words with 6 last added translations."""

    other_translations_count = serializers.SerializerMethodField(
        'get_other_translations_count'
    )
    last_6_translations = serializers.SerializerMethodField('get_last_6_translations')

    class Meta(WordShortCardSerializer.Meta):
        fields = WordShortCardSerializer.Meta.fields + (
            'last_6_translations',
            'other_translations_count',
            'image',
        )

    @extend_schema_field({'type': 'integer'})
    def get_other_translations_count(self, obj: Word) -> int:
        """Returns amount of translations for the given word minus 6 last added."""
        translations_count = obj.translations.count()
        return translations_count - 6 if translations_count > 6 else 0

    @extend_schema_field({'type': 'string'})
    def get_last_6_translations(self, obj: Word) -> QuerySet[WordTranslation]:
        """Returns list of 6 last added translations for the given word."""
        return obj.translations.order_by('-wordtranslations__created').values_list(
            'text', flat=True
        )[:6]


class WordStandartCardSerializer(
    GetImagesSerializerMixin,
    CountObjsSerializerMixin,
    WordShortCardSerializer,
):
    """Serializer to list words in standart form with all translations."""

    translations_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='translations',
    )
    translations = serializers.SerializerMethodField('get_translations')

    class Meta(WordShortCardSerializer.Meta):
        fields = WordShortCardSerializer.Meta.fields + (
            'translations_count',
            'translations',
            'image',
        )

    @extend_schema_field({'type': 'string'})
    def get_translations(self, obj: Word) -> QuerySet[WordTranslation]:
        """Returns list of all related translations for the given word."""
        return obj.translations.order_by('-wordtranslations__created').values_list(
            'text', flat=True
        )


class WordShortCreateSerializer(
    ValidateLanguageMixin,
    FavoriteSerializerMixin,
    UpdateSerializerMixin,
    AlreadyExistSerializerHandler,
    AmountLimitsSerializerHandler,
    NestedSerializerMixin,
    CountObjsSerializerMixin,
    GetImagesSerializerMixin,
    serializers.ModelSerializer,
):
    """
    Serializer to create words in shortened form.
    Used within multiple words creation.
    """

    id = serializers.IntegerField(required=False)
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        required=True,
    )
    types = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Type.objects.all(),
        many=True,
        required=False,
    )
    tags = TagSerializer(
        many=True,
        required=False,
    )
    forms_groups = FormsGroupInLineSerializer(
        many=True,
        required=False,
    )
    translations_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='translations',
    )
    translations = WordTranslationInLineSerializer(
        many=True,
        required=False,
    )
    examples_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='examples',
    )
    examples = UsageExampleInLineSerializer(
        many=True,
        required=False,
    )
    definitions_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='definitions',
    )
    definitions = DefinitionInLineSerializer(
        many=True,
        required=False,
    )
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        serializer_class=UserShortSerializer,
        many=False,
    )
    notes_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='notes',
    )
    notes = NoteInLineSerializer(
        many=True,
        required=False,
    )
    associations_count = serializers.SerializerMethodField('get_associations_count')
    associations = serializers.SerializerMethodField('get_associations')
    images_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='images_associations',
    )
    images_associations = serializers.PrimaryKeyRelatedField(
        queryset=ImageAssociation.objects.all(),
        required=False,
        many=True,
        write_only=True,
    )
    quotes_associations = QuoteInLineSerializer(
        many=True,
        required=False,
        write_only=True,
    )
    activity_status = serializers.SerializerMethodField('get_activity_status_display')

    already_exist_detail = _('This word already exists in your vocabulary. Update it?')
    default_error_messages = {
        'examples_same_language_detail': {
            'examples': _(
                'The usage examples should be in the same language as the word itself.'
            )
        },
        'definitions_same_language_detail': {
            'definitions': _(
                'The definitions should be in the same language as the word itself.'
            )
        },
        'forms_groups_same_language_detail': {
            'forms_groups': _(
                'The form groups should be in the same language as the word itself.'
            )
        },
    }

    class Meta:
        model = Word
        list_serializer_class = ListUpdateSerializer
        favorite_model = FavoriteWord
        favorite_model_field = 'word'
        fields = (
            'id',
            'slug',
            'language',
            'text',
            'author',
            'types',
            'tags',
            'forms_groups',
            'favorite',
            'is_problematic',
            'activity_status',
            'translations_count',
            'translations',
            'examples_count',
            'examples',
            'definitions_count',
            'definitions',
            'images_count',
            'images',
            'images_associations',
            'quotes_associations',
            'associations_count',
            'associations',
            'notes_count',
            'notes',
            'created',
            'modified',
        )
        read_only_fields = (
            'slug',
            'activity_status',
            'translations_count',
            'examples_count',
            'definitions_count',
            'images_count',
            'images',
            'associations_count',
            'associations',
            'notes_count',
            'created',
            'modified',
        )
        # Related objects that need to be added to word through related manager,
        # format: {serializer_field_name: objects_related_name},
        # used within NestedSerializerMixin
        objs_related_names = {
            'translations': 'translations',
            'examples': 'examples',
            'definitions': 'definitions',
            'tags': 'tags',
            'forms_groups': 'forms_groups',
            'quotes_associations': 'quotes_associations',
        }
        # Limits for related objects amount
        amount_limits_check = {
            'tags': (
                VocabularyAmountLimits.MAX_TAGS_AMOUNT,
                VocabularyAmountLimits.Details.TAGS_AMOUNT_EXCEEDED,
            ),
            'types': (
                VocabularyAmountLimits.MAX_TYPES_AMOUNT,
                VocabularyAmountLimits.Details.TYPES_AMOUNT_EXCEEDED,
            ),
            'forms_groups': (
                VocabularyAmountLimits.MAX_FORM_GROUPS_AMOUNT,
                VocabularyAmountLimits.Details.FORM_GROUPS_AMOUNT_EXCEEDED,
            ),
            'translations': (
                VocabularyAmountLimits.MAX_TRANSLATIONS_AMOUNT,
                VocabularyAmountLimits.Details.TRANSLATIONS_AMOUNT_EXCEEDED,
            ),
            'examples': (
                VocabularyAmountLimits.MAX_EXAMPLES_AMOUNT,
                VocabularyAmountLimits.Details.EXAMPLES_AMOUNT_EXCEEDED,
            ),
            'definitions': (
                VocabularyAmountLimits.MAX_DEFINITIONS_AMOUNT,
                VocabularyAmountLimits.Details.DEFINITIONS_AMOUNT_EXCEEDED,
            ),
            'notes': (
                VocabularyAmountLimits.MAX_NOTES_AMOUNT,
                VocabularyAmountLimits.Details.NOTES_AMOUNT_EXCEEDED,
            ),
            'images_associations': (
                VocabularyAmountLimits.MAX_IMAGES_AMOUNT,
                VocabularyAmountLimits.Details.IMAGES_AMOUNT_EXCEEDED,
            ),
            'quotes_associations': (
                VocabularyAmountLimits.MAX_QUOTES_AMOUNT,
                VocabularyAmountLimits.Details.QUOTES_AMOUNT_EXCEEDED,
            ),
        }
        # Related objects whose language must match the given word language
        objs_with_same_language = [
            'examples',
            'definitions',
            'forms_groups',
        ]

    def create(self, validated_data: OrderedDict, parent_first: bool = True) -> Word:
        """
        Passing `parent_first` argument with True value to create instance before
        related objects.
        Used in NestedSerializerMixin.
        """
        return super().create(validated_data, parent_first)

    def update(self, instance: Word, validated_data: OrderedDict) -> Word:
        """
        Delete word related objects if they no longer relate to other words after
        word update.
        """
        instance = super().update(instance, validated_data)
        clear_extra_objects(sender=Word)
        return instance

    def validate(self, attrs: dict) -> OrderedDict:
        """
        Check if languages if related objects in `objs_with_same_language` meta
        attribute match the given word language.
        """
        for attr_name in self.Meta.objs_with_same_language:
            objs_data = attrs.get(attr_name, [])
            for data in objs_data:
                if 'language' in data and (
                    self.instance
                    and data['language'] != self.instance.language
                    or 'language' in attrs
                    and data['language'] != attrs['language']
                ):
                    self.fail(attr_name + '_same_language_detail')
        return super().validate(attrs)

    def fail(self, key: str, *args, **kwargs) -> None:
        """A helper method that simply raises a validation error."""
        raise serializers.ValidationError(self.error_messages[key], code=key)

    @extend_schema_field({'type': 'integer'})
    def get_associations_count(self, obj: Word) -> int:
        """Returns common amount of all associations of any type."""
        return obj.images_associations.count() + obj.quotes_associations.count()

    @extend_schema_field({'type': 'object'})
    def get_associations(self, obj: Word) -> list:
        """Returns common list of all associations of any type."""
        images = ImageInLineSerializer(
            obj.images_associations.all(),
            many=True,
            context={'request': self.context.get('request')},
        )
        quotes = QuoteInLineSerializer(
            obj.quotes_associations.all(),
            many=True,
            context={'request': self.context.get('request')},
        )
        result_list = sorted(
            chain(quotes.data, images.data),
            key=lambda d: d.get('created'),
            reverse=True,
        )
        return result_list

    @extend_schema_field({'type': 'string'})
    def get_activity_status_display(self, obj: Word) -> str:
        """Get activity status full text for display."""
        return obj.get_activity_status_display()

    def validate_language(self, language: Language) -> Language | None:
        """Check if passed language belongs to users learning languages."""
        return self.validate_language_is_learning(language)


class WordSelfRelatedSerializer(NestedSerializerMixin, serializers.ModelSerializer):
    """Common abstract serializer for words related to other words."""

    to_word = serializers.HiddenField(default=None)
    from_word = WordShortCreateSerializer(read_only=False, required=True, many=False)

    validate_same_language = True
    default_error_messages = {
        'same_language_detail': _('Words must be in the same language.'),
        'same_words_detail': _('Object can not be the same word.'),
    }

    class Meta:
        abstract = True

    def validate(self, attrs: dict) -> OrderedDict:
        """
        Checks if languages of passed words are the same.
        Checks if words are different.
        """
        to_word = attrs.get('to_word', None)
        from_word = attrs.get('from_word', None)
        if to_word and from_word:
            if (
                self.validate_same_language
                and 'language' in from_word
                and to_word.language != from_word['language']
            ):
                self.fail('same_language_detail')
            from_word_slug = Word.get_slug_from_data(**from_word)
            if to_word.slug == from_word_slug:
                self.fail('same_words_detail')
        return super().validate(attrs)

    def create(
        self, validated_data: OrderedDict, parent_first: bool = False, *args, **kwargs
    ) -> Synonym | Antonym | Form | Similar:
        """
        Passing `parent_first` argument with False value to create related objects
        before instance.
        Used in NestedSerializerMixin.
        """
        return super().create(validated_data, parent_first)

    def fail(self, key: str, *args, **kwargs) -> None:
        """A helper method that simply raises a validation error."""
        raise serializers.ValidationError(self.error_messages[key], code=key)


class SynonymInLineSerializer(WordSelfRelatedSerializer):
    """Serializer to list, create word synonyms inside word serializer."""

    default_error_messages = {
        'same_language_detail': {
            'synonyms': _(
                'The synonyms should be in the same language as the word itself.'
            )
        },
        'same_words_detail': {
            'synonyms': _('The word itself cannot be its own synonym.')
        },
    }

    class Meta:
        model = Synonym
        list_serializer_class = ListUpdateSerializer
        foreign_key_field_name = 'to_word'
        fields = (
            'to_word',
            'from_word',
            'note',
            'created',
        )
        read_only_fields = (
            'created',
            'to_word',
        )


class AntonymInLineSerializer(WordSelfRelatedSerializer):
    """Serializer to list, create word antonyms inside word serializer."""

    default_error_messages = {
        'same_language_detail': {
            'antonyms': _(
                'The antonyms should be in the same language as the word itself.'
            )
        },
        'same_words_detail': {
            'antonyms': _('The word itself cannot be its own antonym.')
        },
    }

    class Meta:
        model = Antonym
        list_serializer_class = ListUpdateSerializer
        foreign_key_field_name = 'to_word'
        fields = (
            'to_word',
            'from_word',
            'note',
            'created',
        )
        read_only_fields = (
            'created',
            'to_word',
        )


class FormInLineSerializer(WordSelfRelatedSerializer):
    """Serializer to list, create word forms inside word serializer."""

    default_error_messages = {
        'same_language_detail': {
            'forms': _('The forms should be in the same language as the word itself.')
        },
        'same_words_detail': {'forms': _('The word itself cannot be its own form.')},
    }

    class Meta:
        model = Form
        list_serializer_class = ListUpdateSerializer
        foreign_key_field_name = 'to_word'
        fields = (
            'to_word',
            'from_word',
            'created',
        )
        read_only_fields = (
            'created',
            'to_word',
        )


class SimilarInLineSerializer(WordSelfRelatedSerializer):
    """Serializer to list, create similar words inside word serializer."""

    default_error_messages = {
        'same_language_detail': {
            'similars': _(
                'The similar words should be in the same language as the word itself.'
            )
        },
        'same_words_detail': {
            'similars': _('The word itself cannot be its own similar.')
        },
    }

    class Meta:
        model = Similar
        list_serializer_class = ListUpdateSerializer
        foreign_key_field_name = 'to_word'
        fields = (
            'to_word',
            'from_word',
            'created',
        )
        read_only_fields = (
            'created',
            'to_word',
        )


class WordSerializer(WordShortCreateSerializer):
    """
    Serializer to create, retrieve, update words with all details.
    Used within single word creation.
    """

    id = serializers.IntegerField(required=False)
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        required=True,
    )
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        serializer_class=UserShortSerializer,
        many=False,
    )
    types = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Type.objects.order_by('name'),
        many=True,
        required=False,
    )
    tags = TagSerializer(many=True, required=False)
    forms_groups = FormsGroupInLineSerializer(many=True, required=False)
    translations_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='translations',
    )
    translations = WordTranslationInLineSerializer(many=True, required=False)
    examples_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='examples',
    )
    examples = UsageExampleInLineSerializer(many=True, required=False)
    definitions_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='definitions',
    )
    definitions = DefinitionInLineSerializer(many=True, required=False)
    synonyms_count = KwargsMethodField('get_objs_count', objs_related_name='synonyms')
    synonyms = SynonymInLineSerializer(
        many=True,
        required=False,
        source='synonym_to_words',
    )
    antonyms_count = KwargsMethodField('get_objs_count', objs_related_name='antonyms')
    antonyms = AntonymInLineSerializer(
        many=True,
        required=False,
        source='antonym_to_words',
    )
    forms_count = KwargsMethodField('get_objs_count', objs_related_name='forms')
    forms = FormInLineSerializer(many=True, required=False, source='form_to_words')
    similars_count = KwargsMethodField('get_objs_count', objs_related_name='similars')
    similars = SimilarInLineSerializer(
        many=True,
        required=False,
        source='similar_to_words',
    )
    collections_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='collections',
    )
    collections = CollectionShortSerializer(many=True, required=False)
    notes_count = KwargsMethodField('get_objs_count', objs_related_name='notes')
    notes = NoteInLineSerializer(many=True, required=False)

    already_exist_detail = _('This word already exists in your vocabulary. Update it?')

    class Meta(WordShortCreateSerializer.Meta):
        list_serializer_class = serializers.ListSerializer
        fields = (
            'id',
            'slug',
            'language',
            'text',
            'author',
            'favorite',
            'is_problematic',
            'types',
            'tags',
            'forms_groups',
            'activity_status',
            'translations_count',
            'translations',
            'examples_count',
            'examples',
            'definitions_count',
            'definitions',
            'images_count',
            'images',
            'images_associations',
            'quotes_associations',
            'associations_count',
            'associations',
            'synonyms_count',
            'synonyms',
            'antonyms_count',
            'antonyms',
            'forms_count',
            'forms',
            'similars_count',
            'similars',
            'collections_count',
            'collections',
            'notes_count',
            'notes',
            'created',
            'modified',
        )
        read_only_fields = (
            'slug',
            'translations_count',
            'examples_count',
            'definitions_count',
            'images_count',
            'images',
            'associations_count',
            'associations',
            'synonyms_count',
            'antonyms_count',
            'forms_count',
            'similars_count',
            'collections_count',
            'notes_count',
            'activity_status',
            'created',
            'modified',
        )
        # Related objects that need to be added to word through related manager,
        # format: {serializer_field_name: objects_related_name},
        # used within NestedSerializerMixin
        objs_related_names = {
            'examples': 'examples',
            'definitions': 'definitions',
            'translations': 'translations',
            'tags': 'tags',
            'forms_groups': 'forms_groups',
            'collections': 'collections',
            'quotes_associations': 'quotes_associations',
        }
        # Limits for related objects amount
        amount_limits_check = {
            'tags': (
                VocabularyAmountLimits.MAX_TAGS_AMOUNT,
                VocabularyAmountLimits.Details.TAGS_AMOUNT_EXCEEDED,
            ),
            'types': (
                VocabularyAmountLimits.MAX_TYPES_AMOUNT,
                VocabularyAmountLimits.Details.TYPES_AMOUNT_EXCEEDED,
            ),
            'forms_groups': (
                VocabularyAmountLimits.MAX_FORM_GROUPS_AMOUNT,
                VocabularyAmountLimits.Details.FORM_GROUPS_AMOUNT_EXCEEDED,
            ),
            'translations': (
                VocabularyAmountLimits.MAX_TRANSLATIONS_AMOUNT,
                VocabularyAmountLimits.Details.TRANSLATIONS_AMOUNT_EXCEEDED,
            ),
            'examples': (
                VocabularyAmountLimits.MAX_EXAMPLES_AMOUNT,
                VocabularyAmountLimits.Details.EXAMPLES_AMOUNT_EXCEEDED,
            ),
            'definitions': (
                VocabularyAmountLimits.MAX_DEFINITIONS_AMOUNT,
                VocabularyAmountLimits.Details.DEFINITIONS_AMOUNT_EXCEEDED,
            ),
            'notes': (
                VocabularyAmountLimits.MAX_NOTES_AMOUNT,
                VocabularyAmountLimits.Details.NOTES_AMOUNT_EXCEEDED,
            ),
            'images_associations': (
                VocabularyAmountLimits.MAX_IMAGES_AMOUNT,
                VocabularyAmountLimits.Details.IMAGES_AMOUNT_EXCEEDED,
            ),
            'quotes_associations': (
                VocabularyAmountLimits.MAX_QUOTES_AMOUNT,
                VocabularyAmountLimits.Details.QUOTES_AMOUNT_EXCEEDED,
            ),
            'synonym_to_words': (
                VocabularyAmountLimits.MAX_SYNONYMS_AMOUNT,
                VocabularyAmountLimits.Details.SYNONYMS_AMOUNT_EXCEEDED,
            ),
            'antonym_to_words': (
                VocabularyAmountLimits.MAX_ANTONYMS_AMOUNT,
                VocabularyAmountLimits.Details.ANTONYMS_AMOUNT_EXCEEDED,
            ),
            'form_to_words': (
                VocabularyAmountLimits.MAX_FORMS_AMOUNT,
                VocabularyAmountLimits.Details.FORMS_AMOUNT_EXCEEDED,
            ),
            'similar_to_words': (
                VocabularyAmountLimits.MAX_SIMILARS_AMOUNT,
                VocabularyAmountLimits.Details.SIMILARS_AMOUNT_EXCEEDED,
            ),
        }


class MultipleWordsSerializer(serializers.Serializer):
    """
    Serializer to create multiple words at time or add multiple words to collections.
    """

    words = WordShortCreateSerializer(many=True, required=True)
    collections = CollectionShortSerializer(many=True, required=False)

    def create(self, validated_data: OrderedDict) -> dict:
        """
        Creates passed words and collections, if some have already been created,
        uses existing ones.
        Adds given words to given collections.
        Returns created words and collections they were added to.
        """
        _new_words = WordSerializer(many=True, context=self.context).create(
            validated_data['words']
        )
        _collections = CollectionShortSerializer(
            many=True, context=self.context
        ).create(validated_data['collections'])

        for collection in _collections:
            collection.words.add(*_new_words)

        return {'words': _new_words, 'collections': _collections}


class OtherWordsSerializerMixin:
    """
    Custom serializer mixin to add `get_other_words`, `get_other_self_related_words`
    methods to represent object related words excluding given word.
    """

    @extend_schema_field(WordShortCardSerializer(many=True))
    def get_other_words(
        self, obj: Model, related_attr: str, *args, **kwargs
    ) -> ReturnDict:
        """
        Returns object related words data excluding the given word.
        """
        other_words = obj.__getattribute__(related_attr).words.exclude(pk=obj.word.id)
        return WordShortCardSerializer(
            other_words,
            many=True,
            context={'request': self.context.get('request')},
        ).data

    @extend_schema_field(WordShortCardSerializer(many=True))
    def get_other_self_related_words(
        self, obj: WordSelfRelatedModel, related_attr: str, *args, **kwargs
    ) -> ReturnDict:
        """
        Returns object related words data excluding the given word for words with
        recursive relation.
        """
        other_words = obj.from_word.__getattribute__(related_attr).exclude(
            pk=obj.to_word.id
        )
        return WordShortCardSerializer(
            other_words,
            many=True,
            context={'request': self.context.get('request')},
        ).data

    @extend_schema_field({'type': 'integer'})
    def get_other_words_count(self, obj, attr: str, *args, **kwargs) -> int:
        """Returns amount of related words minus 1 for the given word."""
        words_attr = kwargs.get('words_attr', 'words')
        if attr:
            return obj.__getattribute__(attr).__getattribute__(words_attr).count() - 1
        return obj.__getattribute__(words_attr).count() - 1


class AddSelfRelatedWordsThroughDefaultsMixin(NestedSerializerMixin):
    """
    Custom serializer mixin to create words with recursive relation through related
    manager with `through_defaults`.
    """

    def create(
        self,
        validated_data: OrderedDict,
        words_related_name: str,
        intermediary_related_name: str,
        parent_first: bool = False,
        *args,
        **kwargs,
    ) -> Word:
        """
        Creates related word for given word, adds recursive relation through
        related manager with validated_data as value for `through_defaults` to
        fill intermediary instance.

        Args:
            words_related_name (str): related name to set new words through
            intermediary_related_name (str): related name to get intermediary instance
                                             data for response
        """
        to_word = validated_data.pop('to_word')
        from_word_data = validated_data.pop('from_word')

        serializer = self.get_fields()['from_word']
        self.set_child_context(serializer, 'request', self.context.get('request', None))
        from_word = serializer.create(from_word_data)

        to_word.__getattribute__(words_related_name).add(
            from_word, through_defaults=validated_data
        )

        return to_word.__getattribute__(intermediary_related_name).get(
            from_word=from_word
        )


class SynonymForWordListSerializer(
    AddSelfRelatedWordsThroughDefaultsMixin,
    SynonymInLineSerializer,
):
    """Serializer to list, create synonyms for given word."""

    to_word = serializers.HiddenField(default=CurrentWordDefault())

    def create(
        self, validated_data: OrderedDict, parent_first: bool = False, *args, **kwargs
    ) -> Word:
        return super().create(
            validated_data,
            words_related_name='synonyms',
            intermediary_related_name='synonym_to_words',
            parent_first=parent_first,
        )


class AntonymForWordListSerializer(
    AddSelfRelatedWordsThroughDefaultsMixin,
    AntonymInLineSerializer,
):
    """Serializer to list, create antonyms for given word."""

    to_word = serializers.HiddenField(default=CurrentWordDefault())

    def create(
        self, validated_data: OrderedDict, parent_first: bool = False, *args, **kwargs
    ) -> Word:
        return super().create(
            validated_data,
            words_related_name='antonyms',
            intermediary_related_name='antonym_to_words',
            parent_first=parent_first,
        )


class FormForWordListSerializer(
    AddSelfRelatedWordsThroughDefaultsMixin,
    FormInLineSerializer,
):
    """Serializer to list, create forms for given word."""

    to_word = serializers.HiddenField(default=CurrentWordDefault())

    def create(
        self, validated_data: OrderedDict, parent_first: bool = False, *args, **kwargs
    ) -> Word:
        return super().create(
            validated_data,
            words_related_name='forms',
            intermediary_related_name='form_to_words',
            parent_first=parent_first,
        )


class SimilarForWordListSerializer(
    AddSelfRelatedWordsThroughDefaultsMixin,
    SimilarInLineSerializer,
):
    """Serializer to list, create similars for given word."""

    to_word = serializers.HiddenField(default=CurrentWordDefault())

    def create(
        self, validated_data: OrderedDict, parent_first: bool = False, *args, **kwargs
    ) -> Word:
        return super().create(
            validated_data,
            words_related_name='similars',
            intermediary_related_name='similar_to_words',
            parent_first=parent_first,
        )


class NoteForWordSerializer(NoteInLineSerializer):
    """Serializer to retrieve, update note for given word."""

    word = ReadableHiddenField(
        default=CurrentWordDefault(),
        serializer_class=WordSuperShortSerializer,
    )


class WordTranslationListSerializer(serializers.ModelSerializer):
    """Serializer to list translations of all words in user vocabulary."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
    )
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        required=True,
    )
    other_words_count = KwargsMethodField(
        'get_other_words_count',
        objs_related_name='words',
    )
    last_4_words = serializers.SerializerMethodField('get_last_4_words')

    class Meta:
        model = WordTranslation
        fields = (
            'id',
            'slug',
            'author',
            'language',
            'text',
            'other_words_count',
            'last_4_words',
            'words',
        )
        read_only_fields = fields

    @extend_schema_field({'type': 'integer'})
    def get_other_words_count(
        self, obj: WordTranslation, objs_related_name: str = ''
    ) -> int:
        """Returns amount of words for the given translation minus 4 last added."""
        words_count = obj.__getattribute__(objs_related_name).count()
        return words_count - 4 if words_count > 4 else 0

    @extend_schema_field({'type': 'string'})
    def get_last_4_words(self, obj: WordTranslation) -> QuerySet[Word]:
        """Returns list of 4 last added words for the given translation."""
        return obj.words.order_by('-wordtranslations__created').values(
            'text', 'language__name'
        )[:4]


class WordTranslationSerializer(
    ValidateLanguageMixin,
    CountObjsSerializerMixin,
    AlreadyExistSerializerHandler,
    serializers.ModelSerializer,
):
    """Serializer to retrieve translation with all related words."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
    )
    language = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
    )

    already_exist_detail = _(
        'This translation already exists in your vocabulary. Update it?'
    )

    class Meta:
        model = WordTranslation
        fields = (
            'id',
            'slug',
            'author',
            'language',
            'text',
        )
        read_only_fields = (
            'id',
            'slug',
        )

    def validate_language(self, language: Language) -> Language | None:
        """Check if passed language belongs to users learning or native languages."""
        return self.validate_language_is_native_or_learning(language)


class WordTranslationCreateSerializer(
    UpdateSerializerMixin,
    NestedSerializerMixin,
    WordTranslationSerializer,
):
    """Serializer to create translation and add related words to it."""

    id = serializers.IntegerField(required=False)
    language = serializers.SlugRelatedField(
        slug_field='name',
        read_only=False,
        queryset=Language.objects.all(),
    )
    words = WordShortCreateSerializer(
        many=True,
        required=True,
        write_only=True,
    )

    already_exist_detail = _(
        'This translation already exists in your vocabulary. Update it?'
    )

    class Meta(WordTranslationSerializer.Meta):
        fields = WordTranslationSerializer.Meta.fields + ('words',)
        read_only_fields = ('slug',)
        objs_related_names = {
            'words': 'words',
        }


class DefinitionListSerializer(serializers.ModelSerializer):
    """Serializer to list definitions of all words in user vocabulary."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
    )
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        required=True,
    )
    other_words_count = KwargsMethodField(
        'get_other_words_count',
        objs_related_name='words',
    )
    last_4_words = serializers.SerializerMethodField('get_last_4_words')

    class Meta:
        model = Definition
        fields = (
            'id',
            'slug',
            'author',
            'language',
            'text',
            'other_words_count',
            'last_4_words',
        )
        read_only_fields = fields

    @extend_schema_field({'type': 'integer'})
    def get_other_words_count(
        self, obj: Definition, objs_related_name: str = ''
    ) -> int:
        """Returns amount of words for the given definition minus 4 last added."""
        words_count = obj.__getattribute__(objs_related_name).count()
        return words_count - 4 if words_count > 4 else 0

    @extend_schema_field({'type': 'string'})
    def get_last_4_words(self, obj: Definition) -> QuerySet[Word]:
        """Returns list of 4 last added words for the given definition."""
        return obj.words.order_by('-worddefinitions__created').values_list(
            'text', flat=True
        )[:4]


class DefinitionSerializer(
    CountObjsSerializerMixin, AlreadyExistSerializerHandler, serializers.ModelSerializer
):
    """Serializer to retrieve definition with all related words."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
    )
    language = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
    )

    already_exist_detail = _(
        'This definition already exists in your vocabulary. Update it?'
    )

    class Meta:
        model = Definition
        fields = (
            'id',
            'slug',
            'author',
            'language',
            'text',
            'translation',
        )
        read_only_fields = (
            'id',
            'slug',
            'language',
        )


class DefinitionCreateSerializer(
    ValidateLanguageMixin,
    UpdateSerializerMixin,
    NestedSerializerMixin,
    DefinitionSerializer,
):
    """Serializer to create definition and add related words to it."""

    id = serializers.IntegerField(required=False)
    language = serializers.SlugRelatedField(
        slug_field='name',
        read_only=False,
        queryset=Language.objects.all(),
    )
    words = WordShortCreateSerializer(many=True, required=True, write_only=True)

    already_exist_detail = _(
        'This definition already exists in your vocabulary. Update it?'
    )
    default_error_messages = {
        'words_same_language_detail': {
            'words': _(
                'The words should be in the same language as the definition itself.'
            )
        },
    }

    class Meta(DefinitionSerializer.Meta):
        fields = DefinitionSerializer.Meta.fields + ('translation', 'words')
        read_only_fields = ('slug',)
        objs_related_names = {
            'words': 'words',
        }

    def validate(self, attrs: dict) -> OrderedDict:
        """
        Checks if languages of passed definition and its related words are the same.
        """
        objs_data = attrs.get('words', [])
        for data in objs_data:
            if 'language' in data and (
                self.instance
                and data['language'] != self.instance.language
                or 'language' in attrs
                and data['language'] != attrs['language']
            ):
                self.fail('words_same_language_detail')
        return super().validate(attrs)

    def fail(self, key: str, *args, **kwargs) -> None:
        """A helper method that simply raises a validation error."""
        raise serializers.ValidationError(self.error_messages[key], code=key)

    def validate_language(self, language: Language) -> Language | None:
        """Check if passed language belongs to users learning languages."""
        return self.validate_language_is_learning(language)


class UsageExampleListSerializer(serializers.ModelSerializer):
    """Serializer to list usage examples of all words in user vocabulary."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
    )
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        required=True,
    )
    other_words_count = KwargsMethodField(
        'get_other_words_count',
        objs_related_name='words',
    )
    last_4_words = serializers.SerializerMethodField('get_last_4_words')

    class Meta:
        model = UsageExample
        fields = (
            'id',
            'slug',
            'author',
            'language',
            'text',
            'other_words_count',
            'last_4_words',
        )
        read_only_fields = fields

    @extend_schema_field({'type': 'integer'})
    def get_other_words_count(
        self, obj: UsageExample, objs_related_name: str = ''
    ) -> int:
        """Returns amount of words for the given usage example minus 4 last added."""
        words_count = obj.__getattribute__(objs_related_name).count()
        return words_count - 4 if words_count > 4 else 0

    @extend_schema_field({'type': 'string'})
    def get_last_4_words(self, obj: UsageExample) -> QuerySet[Word]:
        """Returns list of 4 last added words for the given usage example."""
        return obj.words.order_by('-wordusageexamples').values_list('text', flat=True)[
            :4
        ]


class UsageExampleSerializer(
    CountObjsSerializerMixin, AlreadyExistSerializerHandler, serializers.ModelSerializer
):
    """Serializer to retrieve usage example with all related words."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
    )
    language = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
    )

    already_exist_detail = _(
        'This usage example already exists in your vocabulary. Update it?'
    )

    class Meta:
        model = UsageExample
        fields = (
            'id',
            'slug',
            'author',
            'language',
            'text',
            'translation',
        )
        read_only_fields = (
            'id',
            'slug',
            'language',
        )


class UsageExampleCreateSerializer(
    ValidateLanguageMixin,
    UpdateSerializerMixin,
    NestedSerializerMixin,
    UsageExampleSerializer,
):
    """Serializer to create usage example and add related words to it."""

    id = serializers.IntegerField(required=False)
    language = serializers.SlugRelatedField(
        slug_field='name',
        read_only=False,
        queryset=Language.objects.all(),
    )
    words = WordShortCreateSerializer(
        many=True,
        required=True,
        write_only=True,
    )

    already_exist_detail = _(
        'This usage example already exists in your vocabulary. Update it?'
    )
    default_error_messages = {
        'words_same_language_detail': {
            'words': _(
                'The words should be in the same language as the usage example itself.'
            )
        },
    }

    class Meta(UsageExampleSerializer.Meta):
        fields = UsageExampleSerializer.Meta.fields + ('translation', 'words')
        read_only_fields = ('slug',)
        objs_related_names = {
            'words': 'words',
        }

    def validate(self, attrs: dict) -> OrderedDict:
        """
        Checks if languages of passed definition and its related words are the same.
        """
        objs_data = attrs.get('words', [])
        for data in objs_data:
            if 'language' in data and (
                self.instance
                and data['language'] != self.instance.language
                or 'language' in attrs
                and data['language'] != attrs['language']
            ):
                self.fail('words_same_language_detail')
        return super().validate(attrs)

    def fail(self, key: str, *args, **kwargs) -> None:
        """A helper method that simply raises a validation error."""
        raise serializers.ValidationError(self.error_messages[key], code=key)

    def validate_language(self, language: Language) -> Language | None:
        """Check if passed language belongs to users learning languages."""
        return self.validate_language_is_learning(language)


class ImageListSerializer(serializers.ModelSerializer):
    """Serializer to list image-associations of all words in user vocabulary."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
    )
    image = HybridImageField()
    image_height = serializers.SerializerMethodField('get_image_height')
    image_width = serializers.SerializerMethodField('get_image_width')
    other_words_count = KwargsMethodField(
        'get_other_words_count',
        objs_related_name='words',
    )
    last_4_words = serializers.SerializerMethodField('get_last_4_words')

    class Meta:
        model = ImageAssociation
        fields = (
            'id',
            'author',
            'image',
            'image_height',
            'image_width',
            'other_words_count',
            'last_4_words',
        )
        read_only_fields = (
            'id',
            'other_words_count',
            'last_4_words',
        )

    @extend_schema_field({'type': 'integer'})
    def get_image_height(self, obj: ImageAssociation) -> int | None:
        try:
            return obj.image.height
        except ValueError:
            return None

    @extend_schema_field({'type': 'integer'})
    def get_image_width(self, obj: ImageAssociation) -> int | None:
        try:
            return obj.image.width
        except ValueError:
            return None

    @extend_schema_field({'type': 'integer'})
    def get_other_words_count(
        self,
        obj: ImageAssociation,
        objs_related_name: str = '',
    ) -> int:
        """
        Returns amount of words for the given image-association minus 4 last added.
        """
        words_count = obj.__getattribute__(objs_related_name).count()
        return words_count - 4 if words_count > 4 else 0

    @extend_schema_field({'type': 'string'})
    def get_last_4_words(self, obj: ImageAssociation) -> QuerySet[Word]:
        """Returns list of 4 last added words for the given image-association."""
        return obj.words.order_by('-wordimageassociations').values_list(
            'text', flat=True
        )[:4]


class AssociationsCreateSerializer(serializers.Serializer):
    """Serializer to create associations of any type."""

    quotes = QuoteInLineSerializer(
        many=True,
        required=False,
    )
    images = PresentablePrimaryKeyRelatedField(
        queryset=ImageAssociation.objects.all(),
        required=False,
        many=True,
        write_only=True,
        presentation_serializer=ImageInLineSerializer,
    )

    def create(self, validated_data: OrderedDict) -> dict:
        """Creates associations of any type."""
        _quotes_data = self.get_fields()['quotes'].create(
            validated_data.get('quotes', [])
        )
        return {
            'quotes': _quotes_data,
            'images': validated_data.get('images', []),
        }


class LanguageImageSerailizer(serializers.ModelSerializer):
    """Serializer to list available images for given language."""

    language = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
    )
    image_height = serializers.SerializerMethodField('get_image_height')
    image_width = serializers.SerializerMethodField('get_image_width')

    class Meta:
        model = LanguageImage
        fields = (
            'id',
            'language',
            'image',
            'image_height',
            'image_width',
        )
        read_only_fields = fields

    @extend_schema_field({'type': 'integer'})
    def get_image_height(self, obj: LanguageImage) -> int | None:
        try:
            return obj.image.height
        except ValueError:
            return None

    @extend_schema_field({'type': 'integer'})
    def get_image_width(self, obj: LanguageImage) -> int | None:
        try:
            return obj.image.width
        except ValueError:
            return None


class CoverSetSerailizer(serializers.ModelSerializer):
    """
    Serializer to use for setting new cover image for user's learning language.
    """

    image_id = serializers.PrimaryKeyRelatedField(
        queryset=LanguageImage.objects.all(),
        many=False,
        read_only=False,
        source='images',
        required=True,
    )

    class Meta:
        model = Language
        fields = ('image_id',)


class SynonymSerializer(
    ValidateLanguageMixin,
    CountObjsSerializerMixin,
    AlreadyExistSerializerHandler,
    GetImagesSerializerMixin,
    serializers.ModelSerializer,
):
    """Serializer to retrieve synonym with all related words."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
    )
    language = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
    )

    already_exist_detail = _('This word already exists in your vocabulary. Update it?')

    class Meta:
        model = Word
        fields = (
            'id',
            'slug',
            'author',
            'language',
            'text',
            'image',
        )
        read_only_fields = (
            'id',
            'slug',
            'image',
        )

    def validate_language(self, language: Language) -> Language | None:
        """Check if passed language belongs to users learning languages."""
        return self.validate_language_is_learning(language)


class AntonymSerializer(SynonymSerializer):
    """Serializer to retrieve antonym with all related words."""

    pass


class SimilarSerializer(SynonymSerializer):
    """Serializer to retrieve similar word with all related words."""

    pass


class TagListSerializer(TagSerializer, CountObjsSerializerMixin):
    """Serializer to list all user's tags."""

    words_count = KwargsMethodField('get_objs_count', objs_related_name='words')

    class Meta:
        model = Tag
        fields = ('name', 'author', 'words_count')
        read_only_fields = ('words_count',)


class TypeSerializer(CountObjsSerializerMixin, serializers.ModelSerializer):
    """Serializer to list all possible types of words and phrases."""

    words_count = KwargsMethodField('get_objs_count', objs_related_name='words')

    class Meta:
        model = Type
        fields = (
            'id',
            'name',
            'slug',
            'words_count',
        )
        read_only_fields = fields


class FormsGroupListSerializer(
    ValidateLanguageMixin, CountObjsSerializerMixin, serializers.ModelSerializer
):
    """Serializer to list all user's form groups."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
    )
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        required=True,
    )
    words_count = KwargsMethodField('get_objs_count', objs_related_name='forms_groups')

    class Meta:
        model = FormsGroup
        fields = (
            'id',
            'slug',
            'author',
            'language',
            'name',
            'color',
            'words_count',
        )
        read_only_fields = (
            'id',
            'slug',
            'author',
            'words_count',
        )

    def validate_language(self, language: Language) -> Language | None:
        """Check if passed language belongs to users learning languages."""
        return self.validate_language_is_learning(language)


class CollectionSerializer(CollectionShortSerializer):
    """Serializer to retrieve collection with all related words."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        serializer_class=UserShortSerializer,
        many=False,
    )
    words_languages = serializers.SerializerMethodField('get_words_languages')
    words_images = serializers.SerializerMethodField('get_words_images')
    words_images_count = serializers.SerializerMethodField('get_words_images_count')

    class Meta(CollectionShortSerializer.Meta):
        fields = (
            'id',
            'slug',
            'author',
            'title',
            'description',
            'favorite',
            'words_languages',
            'words_count',
            'words_images_count',
            'words_images',
            'created',
            'modified',
        )
        read_only_fields = (
            'id',
            'slug',
            'author',
            'favorite',
            'words_languages',
            'words_count',
            'words_images_count',
            'words_images',
            'created',
            'modified',
        )

    @extend_schema_field({'type': 'object'})
    def get_words_languages(self, obj: Collection) -> QuerySet[Word]:
        """
        Returns languages list of all words in given collection sorted by
        words amount for each language.
        """
        return (
            obj.words.values('language__name').annotate(words_count=Count('language'))
        ).order_by('-words_count')

    @extend_schema_field({'type': 'integer'})
    def get_words_images_count(self, obj: Collection) -> int:
        """
        Returns amount of image-associations for all words in given collection.
        """
        return obj.words.filter(images_associations__isnull=False).count()

    @extend_schema_field({'type': 'object'})
    def get_words_images(self, obj: Collection) -> QuerySet[Word]:
        """
        Returns list of image-associations for all words in given collection.
        """
        return obj.words.filter(images_associations__isnull=False).values_list(
            'images_associations__image', flat=True
        )


class LearningLanguageWithLastWordsSerailizer(LearningLanguageSerailizer):
    """Serializer to list all user's learning languages."""

    last_10_words = serializers.SerializerMethodField('get_last_10_words')

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
            'last_10_words',
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
            'last_10_words',
        )

    @extend_schema_field(WordStandartCardSerializer(many=True))
    def get_last_10_words(self, obj: UserLearningLanguage) -> ReturnDict:
        """Return list of 10 last added words for each learning language."""
        words = obj.user.words.filter(language=obj.language)[:10]
        return WordStandartCardSerializer(
            words, many=True, context={'request': self.context['request']}
        ).data


class UserDetailsSerializer(
    CountObjsSerializerMixin,
    UserShortSerializer,
):
    """Serializer to retrieve, update user's profile data."""

    native_languages = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        required=False,
        many=True,
    )
    learning_languages_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='learning_languages',
    )
    learning_languages = LearningLanguageShortSerailizer(
        read_only=True,
        many=True,
        source='learning_languages_detail',
    )
    words_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='words',
    )
    last_10_words = serializers.SerializerMethodField('get_last_10_words')

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'image',
            'native_languages',
            'learning_languages_count',
            'learning_languages',
            'words_count',
            'last_10_words',
        )
        read_only_fields = (
            'id',
            'learning_languages_count',
            'learning_languages',
            'words_count',
            'last_10_words',
        )

    def validate_native_languages(
        self, languages: QuerySet[Language]
    ) -> QuerySet[Language]:
        """Raises ValidationError if amount limits for native languages exceeded."""
        if len(languages) > UsersAmountLimits.MAX_NATIVE_LANGUAGES_AMOUNT:
            raise serializers.ValidationError(
                UsersAmountLimits.Details.NATIVE_LANGUAGES_AMOUNT_EXCEEDED
            )
        return languages

    @extend_schema_field(WordStandartCardSerializer(many=True))
    def get_last_10_words(self, obj) -> ReturnDict:
        """Returns list of 10 last added words from user's vocabulary."""
        words = obj.words.all()[:10]
        return WordStandartCardSerializer(
            words, many=True, context={'request': self.context['request']}
        ).data


class MainPageSerailizer(UserDetailsSerializer):
    """Serializer to retrieve main page data."""

    collections_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='collections',
    )
    last_10_collections = serializers.SerializerMethodField('get_last_10_collections')
    tags_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='tags',
    )
    last_10_tags = serializers.SerializerMethodField('get_last_10_tags')
    images_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='imageassociations',
    )
    last_10_images = serializers.SerializerMethodField('get_last_10_images')
    definitions_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='definitions',
    )
    last_10_definitions = serializers.SerializerMethodField('get_last_10_definitions')
    examples_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='usageexamples',
    )
    last_10_examples = serializers.SerializerMethodField('get_last_10_examples')
    translations_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='wordtranslations',
    )
    last_10_translations = serializers.SerializerMethodField('get_last_10_translations')

    class Meta:
        model = User
        fields = (
            'learning_languages_count',
            'learning_languages',
            'collections_count',
            'last_10_collections',
            'tags_count',
            'last_10_tags',
            'images_count',
            'last_10_images',
            'definitions_count',
            'last_10_definitions',
            'examples_count',
            'last_10_examples',
            'translations_count',
            'last_10_translations',
            'words_count',
            'last_10_words',
            # last_exercise_results
            # random_word_challenge
            # word_of_day
        )
        read_only_fields = fields

    def get_last_10_objs(
        self, obj, objs_related_name: str, serializer_class: Serializer
    ) -> ReturnDict:
        """Common method to return list of 10 last added by user objects."""
        return serializer_class(
            obj.__getattribute__(objs_related_name).all()[:10],
            many=True,
            context={'request': self.context['request']},
        ).data

    @extend_schema_field(CollectionShortSerializer(many=True))
    def get_last_10_collections(self, obj) -> ReturnDict:
        """Returns list of 10 last added user's collections."""
        return self.get_last_10_objs(obj, 'collections', CollectionShortSerializer)

    @extend_schema_field(TagListSerializer(many=True))
    def get_last_10_tags(self, obj) -> ReturnDict:
        """Returns list of 10 last added user's tags."""
        return self.get_last_10_objs(obj, 'tags', TagListSerializer)

    @extend_schema_field(ImageListSerializer(many=True))
    def get_last_10_images(self, obj) -> ReturnDict:
        """Returns list of 10 last added user's words image-associations."""
        return self.get_last_10_objs(obj, 'imageassociations', ImageListSerializer)

    @extend_schema_field(DefinitionListSerializer(many=True))
    def get_last_10_definitions(self, obj) -> ReturnDict:
        """Returns list of 10 last added user's words definitions."""
        return self.get_last_10_objs(obj, 'definitions', DefinitionListSerializer)

    @extend_schema_field(UsageExampleListSerializer(many=True))
    def get_last_10_examples(self, obj) -> ReturnDict:
        """Returns list of 10 last added user's words usage examples."""
        return self.get_last_10_objs(obj, 'usageexamples', UsageExampleListSerializer)

    @extend_schema_field(WordTranslationListSerializer(many=True))
    def get_last_10_translations(self, obj) -> ReturnDict:
        """Returns list of 10 last added user's words translations."""
        return self.get_last_10_objs(
            obj, 'wordtranslations', WordTranslationListSerializer
        )


class AllUserAssociationsSerializer(serializers.ModelSerializer):
    associations_list = serializers.SerializerMethodField('get_user_associations')

    class Meta:
        model = User
        fields = ('associations_list',)

    @extend_schema_field(list)
    def get_user_associations(self, obj) -> chain:
        """Returns list of all user's words associations."""
        images = ImageInLineSerializer(
            obj.imageassociations.all(),
            many=True,
            context=self.context,
        )

        quotes = QuoteInLineSerializer(
            obj.quoteassociations.all(),
            many=True,
            context=self.context,
        )

        result_list = sorted(
            chain(quotes.data, images.data),
            key=lambda d: d.get('created'),
            reverse=True,
        )

        return result_list
