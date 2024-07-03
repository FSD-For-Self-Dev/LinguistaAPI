"""Сериализаторы приложения vocabulary."""

from itertools import chain
from collections import OrderedDict

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet

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
    UpdateSerializerMixin,
)
from users.models import UserLearningLanguage
from users.serializers import (
    UserShortSerializer,
    LearningLanguageShortSerailizer,
)
from users.constants import UsersAmountLimits
from languages.models import LanguageImage
from languages.serializers import LanguageSerializer

from .constants import VocabularyAmountLimits
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
    WordDefinitions,
    WordTranslation,
    WordUsageExamples,
    WordTranslations,
    WordImageAssociations,
    WordQuoteAssociations,
    ImageAssociation,
    QuoteAssociation,
    clear_extra_objects,
)

User = get_user_model()


class CurrentWordDefault:
    """Текущее просматриваемое слово в качестве дефолтного значения для поля."""

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
    """Родной язык пользователя в качестве дефолтного значения для поля."""

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
    Миксин для валидации поля языка
    (принадлежит родным/изучаемым языкам пользователя).
    """

    def validate_language_is_native_or_learning(
        self, language: Language
    ) -> Language | None:
        """Язык является изучаемым или родным для пользователя."""
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
        """Язык является изучаемым для пользователя."""
        user = self.context.get('request').user
        if language not in user.learning_languages.all():
            raise serializers.ValidationError(
                _('Language must be in your learning languages.'),
                code='invalid_language',
            )
        return language

    def validate_language_is_native(self, language: Language) -> Language | None:
        """Язык является родным для пользователя."""
        user = self.context.get('request').user
        if language not in user.native_languages.all():
            raise serializers.ValidationError(
                _('Language must be in your native languages.'), code='invalid_language'
            )
        return language


class NoteInLineSerializer(AlreadyExistSerializerHandler, serializers.ModelSerializer):
    """Сериализатор заметок слова для использования в сериализаторе слова."""

    id = serializers.IntegerField(required=False)
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
    )
    word = serializers.HiddenField(default=None)

    already_exist_detail = _('Такая заметка у слова уже есть.')

    class Meta:
        model = Note
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
        list_serializer_class = ListUpdateSerializer
        foreign_key_field_name = 'word'


class WordTranslationInLineSerializer(
    AlreadyExistSerializerHandler, ValidateLanguageMixin, serializers.ModelSerializer
):
    """Сериализатор переводов слова для использования в сериализаторе слова."""

    id = serializers.IntegerField(required=False)
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
    )
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        default=NativeLanguageDefault(),
    )

    already_exist_detail = _('Такой перевод уже есть в вашем словаре. Обновить его?')

    class Meta:
        model = WordTranslation
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
        list_serializer_class = ListUpdateSerializer

    def validate_language(self, language: Language) -> Language | None:
        return self.validate_language_is_native_or_learning(language)


class UsageExampleInLineSerializer(
    AlreadyExistSerializerHandler, serializers.ModelSerializer
):
    """Сериализатор примеров для использования в сериализаторе слова."""

    id = serializers.IntegerField(required=False)
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
    )
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        required=True,
    )

    already_exist_detail = _('Такой пример уже есть в вашем словаре. Обновить его?')

    class Meta:
        model = UsageExample
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
        list_serializer_class = ListUpdateSerializer


class DefinitionInLineSerializer(
    AlreadyExistSerializerHandler, serializers.ModelSerializer
):
    """Сериализатор определений слова для использования в сериализаторе слова."""

    id = serializers.IntegerField(required=False)
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
    )
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        required=True,
    )

    already_exist_detail = _(
        'Такое определение уже есть в вашем словаре. Обновить его?'
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
            'created',
            'modified',
        )
        read_only_fields = (
            'id',
            'slug',
            'created',
            'modified',
        )
        list_serializer_class = ListUpdateSerializer


class CollectionShortSerializer(
    FavoriteSerializerMixin,
    AlreadyExistSerializerHandler,
    CountObjsSerializerMixin,
    serializers.ModelSerializer,
):
    """Сериализатор коллекций (короткая форма)."""

    id = serializers.IntegerField(required=False)
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
    )
    words_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='words',
    )
    last_3_words = serializers.SerializerMethodField('get_last_3_words')

    already_exist_detail = _('Такая коллекция уже есть в вашем словаре. Обновить её?')

    class Meta:
        model = Collection
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
        list_serializer_class = ListUpdateSerializer

    @extend_schema_field({'type': 'object'})
    def get_last_3_words(self, obj: Collection) -> QuerySet[Word]:
        return obj.words.order_by('-wordsincollections__created').values_list(
            'text', flat=True
        )[:3]


class FormsGroupInLineSerializer(
    AlreadyExistSerializerHandler, serializers.ModelSerializer
):
    """Сериализатор групп форм для использования в сериализаторе слова."""

    id = serializers.IntegerField(required=False)
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
    )
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        required=True,
    )

    already_exist_detail = _('Такая группа форм уже есть в вашем словаре. Обновить её?')

    class Meta:
        model = FormsGroup
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
        list_serializer_class = ListUpdateSerializer

    def validate_name(self, name: str) -> str:
        if name.capitalize() == 'Infinitive':
            raise serializers.ValidationError(
                _('The forms group `Infinitive` already exists.')
            )
        return name


class ImageInLineSerializer(serializers.ModelSerializer):
    """Сериализатор ассоциаций-картинок для использования в сериализаторе слова."""

    image = HybridImageField()
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
    )

    class Meta:
        model = ImageAssociation
        fields = (
            'id',
            'name',
            'author',
            'image',
            'created',
        )
        read_only_fields = (
            'id',
            'created',
        )
        list_serializer_class = ListUpdateSerializer


class QuoteInLineSerializer(serializers.ModelSerializer):
    """Сериализатор ассоциаций-цитат для использования в сериализаторе слова."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
    )

    class Meta:
        model = QuoteAssociation
        fields = (
            'id',
            'text',
            'quote_author',
            'author',
            'created',
        )
        read_only_fields = (
            'id',
            'created',
        )
        list_serializer_class = ListUpdateSerializer


class TagSerializer(AlreadyExistSerializerHandler, serializers.ModelSerializer):
    """Сериализатор тегов слов."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
        write_only=True,
    )
    name = serializers.CharField()

    already_exist_detail = _('Такой тег уже есть в вашем словаре. Обновить его?')

    class Meta:
        model = Tag
        fields = ('name', 'author')
        list_serializer_class = ListUpdateSerializer


class WordSuperShortSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения слов (минимальная форма)."""

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


class WordSuperShortWithTranslations(WordSuperShortSerializer):
    """Сериализатор для отображения слов (с последними переводами)."""

    last_4_translations = serializers.SerializerMethodField('get_last_4_translations')
    other_translations_count = serializers.SerializerMethodField(
        'get_other_translations_count'
    )

    class Meta(WordSuperShortSerializer.Meta):
        fields = WordSuperShortSerializer.Meta.fields + (
            'last_4_translations',
            'other_translations_count',
        )

    @extend_schema_field({'type': 'integer'})
    def get_other_translations_count(self, obj: Word) -> int:
        translations_count = obj.translations.count()
        return translations_count - 4 if translations_count > 4 else 0

    @extend_schema_field({'type': 'string'})
    def get_last_4_translations(self, obj: Word) -> QuerySet[WordTranslation]:
        return obj.translations.order_by('-wordtranslations__created').values('text')[
            :4
        ]


class WordShortCardSerializer(
    FavoriteSerializerMixin,
    WordSuperShortSerializer,
):
    """Сериализатор для отображения коротких карточек слов."""

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
        return obj.get_activity_status_display()


class GetImagesSerializerMixin(serializers.ModelSerializer):
    """Миксин для чтения ассоциаций-картинок."""

    images = serializers.SerializerMethodField('get_images')

    @extend_schema_field({'type': 'object'})
    def get_images(self, obj: Word) -> QuerySet[ImageAssociation]:
        return obj.images_associations.values_list('image', flat=True)


class WordLongCardSerializer(
    GetImagesSerializerMixin,
    CountObjsSerializerMixin,
    WordShortCardSerializer,
):
    """Сериализатор для отображения длинных карточек слов."""

    images_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='images_associations',
    )
    other_translations_count = serializers.SerializerMethodField(
        'get_other_translations_count'
    )
    last_6_translations = serializers.SerializerMethodField('get_last_6_translations')

    class Meta(WordShortCardSerializer.Meta):
        fields = WordShortCardSerializer.Meta.fields + (
            'last_6_translations',
            'other_translations_count',
            'images_count',
            'images',
        )

    @extend_schema_field({'type': 'integer'})
    def get_other_translations_count(self, obj: Word) -> int:
        translations_count = obj.translations.count()
        return translations_count - 6 if translations_count > 6 else 0

    @extend_schema_field({'type': 'string'})
    def get_last_6_translations(self, obj: Word) -> QuerySet[WordTranslation]:
        return obj.translations.order_by('-wordtranslations__created').values_list(
            'text', flat=True
        )[:6]


class WordStandartCardSerializer(
    GetImagesSerializerMixin,
    CountObjsSerializerMixin,
    WordShortCardSerializer,
):
    """Сериализатор для отображения стандартных карточек слов."""

    images_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='images_associations',
    )
    translations_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='translations',
    )
    translations = serializers.SerializerMethodField('get_translations')

    class Meta(WordShortCardSerializer.Meta):
        fields = WordShortCardSerializer.Meta.fields + (
            'translations_count',
            'translations',
            'images_count',
            'images',
        )

    @extend_schema_field({'type': 'string'})
    def get_translations(self, obj: Word) -> QuerySet[WordTranslation]:
        return obj.translations.order_by('-wordtranslations__created').values_list(
            'text', flat=True
        )


class WordShortCreateSerializer(
    ValidateLanguageMixin,
    FavoriteSerializerMixin,
    UpdateSerializerMixin,
    AlreadyExistSerializerHandler,
    NestedSerializerMixin,
    CountObjsSerializerMixin,
    GetImagesSerializerMixin,
    serializers.ModelSerializer,
):
    """Сериализатор для записи слов в короткой форме."""

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

    already_exist_detail = _('Такое слово уже есть в вашем словаре. Обновить его?')
    default_error_messages = {
        'examples_same_language_detail': {
            'examples': _(
                'Пример использования должен быть на том же языке, что и само слово.'
            )
        },
        'definitions_same_language_detail': {
            'definitions': _(
                'Определение должно быть на том же языке, что и само слово.'
            )
        },
        'forms_groups_same_language_detail': {
            'forms_groups': _(
                'Группа форм должна быть на том же языке, что и само слово.'
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
        # Связанные объекты, которые при создании объекта слова необходимо добавить
        # через related manager; используется в NestedSerializerMixin
        objs_related_names = {
            'translations': 'translations',
            'examples': 'examples',
            'definitions': 'definitions',
            'tags': 'tags',
            'forms_groups': 'forms_groups',
            'quotes_associations': 'quotes_associations',
        }
        # Ограничения по кол-ву связанных объектов
        amount_limit_fields = {
            'tags': VocabularyAmountLimits.MAX_TAGS_AMOUNT,
            'types': VocabularyAmountLimits.MAX_TYPES_AMOUNT,
            'forms_groups': VocabularyAmountLimits.MAX_FORMS_GROUPS_AMOUNT,
            'translations': VocabularyAmountLimits.MAX_TRANSLATIONS_AMOUNT,
            'examples': VocabularyAmountLimits.MAX_EXAMPLES_AMOUNT,
            'definitions': VocabularyAmountLimits.MAX_DEFINITIONS_AMOUNT,
            'notes': VocabularyAmountLimits.MAX_NOTES_AMOUNT,
            'images_associations': VocabularyAmountLimits.MAX_IMAGES_AMOUNT,
            'quotes_associations': VocabularyAmountLimits.MAX_QUOTES_AMOUNT,
        }
        # Связанные объекты, язык которых должен совпадать с языком самого слова
        objs_with_same_language = [
            'examples',
            'definitions',
            'forms_groups',
        ]

    def create(self, validated_data: OrderedDict, parent_first: bool = True) -> Word:
        return super().create(validated_data, parent_first)

    def update(self, instance: Word, validated_data: OrderedDict) -> Word:
        instance = super().update(instance, validated_data)
        # Удалить связанные объекты, если они больше не используются
        clear_extra_objects(sender=Word)
        return instance

    def validate(self, attrs: dict) -> OrderedDict:
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
        raise serializers.ValidationError(self.error_messages[key], code=key)

    @extend_schema_field({'type': 'integer'})
    def get_associations_count(self, obj: Word) -> int:
        return obj.images_associations.count() + obj.quotes_associations.count()

    @extend_schema_field({'type': 'object'})
    def get_associations(self, obj: Word) -> list:
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
        return obj.get_activity_status_display()

    def validate_language(self, language: Language) -> Language | None:
        return self.validate_language_is_learning(language)


class WordSelfRelatedSerializer(NestedSerializerMixin, serializers.ModelSerializer):
    """Общий сериализатор для слов с рекурсивной связью."""

    to_word = serializers.HiddenField(default=None)
    from_word = WordShortCreateSerializer(read_only=False, required=True, many=False)

    validate_same_language = True
    default_error_messages = {
        'same_language_detail': _('Validation error.'),
        'same_words_detail': _('Object can not be the same word.'),
    }

    class Meta:
        abstract = True

    def validate(self, attrs: dict) -> OrderedDict:
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
        return super().create(validated_data, parent_first)

    def fail(self, key: str, *args, **kwargs) -> None:
        raise serializers.ValidationError(self.error_messages[key], code=key)


class SynonymInLineSerializer(WordSelfRelatedSerializer):
    """Сериализатор синонимов для использования в сериализаторе слова."""

    default_error_messages = {
        'same_language_detail': {
            'synonyms': _('Синоним должен быть на том же языке, что и само слово.')
        },
        'same_words_detail': {
            'synonyms': _('Само слово не может быть своим синонимом.')
        },
    }

    class Meta:
        model = Synonym
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
        list_serializer_class = ListUpdateSerializer
        foreign_key_field_name = 'to_word'


class AntonymInLineSerializer(WordSelfRelatedSerializer):
    """Сериализатор антонимов для использования в сериализаторе слова."""

    default_error_messages = {
        'same_language_detail': {
            'antonyms': _('Антоним должен быть на том же языке, что и само слово.')
        },
        'same_words_detail': {
            'antonyms': _('Само слово не может быть своим антонимом.')
        },
    }

    class Meta:
        model = Antonym
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
        list_serializer_class = ListUpdateSerializer
        foreign_key_field_name = 'to_word'


class FormInLineSerializer(WordSelfRelatedSerializer):
    """Сериализатор форм слова для использования в сериализаторе слова."""

    default_error_messages = {
        'same_language_detail': {
            'forms': _('Форма должна быть на том же языке, что и само слово.')
        },
        'same_words_detail': {'forms': _('Само слово не может быть своей формой.')},
    }

    class Meta:
        model = Form
        fields = (
            'to_word',
            'from_word',
            'created',
        )
        read_only_fields = (
            'created',
            'to_word',
        )
        list_serializer_class = ListUpdateSerializer
        foreign_key_field_name = 'to_word'


class SimilarInLineSerializer(WordSelfRelatedSerializer):
    """Сериализатор похожих слов для использования в сериализаторе слова."""

    default_error_messages = {
        'same_language_detail': {
            'similars': _(
                'Похожее слово должно быть на том же языке, что и само слово.'
            )
        },
        'same_words_detail': {'similars': _('Само слово нельзя добавить в похожие.')},
    }

    class Meta:
        model = Similar
        fields = (
            'to_word',
            'from_word',
            'created',
        )
        read_only_fields = (
            'created',
            'to_word',
        )
        list_serializer_class = ListUpdateSerializer
        foreign_key_field_name = 'to_word'


class WordSerializer(WordShortCreateSerializer):
    """Расширенный (полный) сериализатор слова."""

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

    already_exist_detail = _('Такое слово уже есть в вашем словаре. Обновить его?')

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
        # Связанные объекты, которые при создании объекта слова необходимо добавить
        # через related manager; используется в NestedSerializerMixin
        objs_related_names = {
            'examples': 'examples',
            'definitions': 'definitions',
            'translations': 'translations',
            'tags': 'tags',
            'forms_groups': 'forms_groups',
            'collections': 'collections',
            'quotes_associations': 'quotes_associations',
        }
        # Ограничения по кол-ву связанных объектов
        amount_limit_fields = {
            'tags': VocabularyAmountLimits.MAX_TAGS_AMOUNT,
            'types': VocabularyAmountLimits.MAX_TYPES_AMOUNT,
            'forms_groups': VocabularyAmountLimits.MAX_FORMS_GROUPS_AMOUNT,
            'translations': VocabularyAmountLimits.MAX_TRANSLATIONS_AMOUNT,
            'examples': VocabularyAmountLimits.MAX_EXAMPLES_AMOUNT,
            'definitions': VocabularyAmountLimits.MAX_DEFINITIONS_AMOUNT,
            'synonym_to_words': VocabularyAmountLimits.MAX_SYNONYMS_AMOUNT,
            'antonym_to_words': VocabularyAmountLimits.MAX_ANTONYMS_AMOUNT,
            'form_to_words': VocabularyAmountLimits.MAX_FORMS_AMOUNT,
            'similar_to_words': VocabularyAmountLimits.MAX_SIMILARS_AMOUNT,
            'notes': VocabularyAmountLimits.MAX_NOTES_AMOUNT,
            'images_associations': VocabularyAmountLimits.MAX_IMAGES_AMOUNT,
            'quotes_associations': VocabularyAmountLimits.MAX_QUOTES_AMOUNT,
        }

    def validate(self, attrs: dict, *args, **kwargs) -> OrderedDict:
        return super().validate(attrs)


class MultipleWordsSerializer(serializers.Serializer):
    """Сериализатор для создания нескольких слов сразу и добавления их в коллекции."""

    words = WordShortCreateSerializer(many=True, required=True)
    collections = CollectionShortSerializer(many=True, required=False)

    def create(self, validated_data: OrderedDict) -> dict:
        _new_words = WordSerializer(
            many=True, context={'request': self.context['request']}
        ).create(validated_data['words'])
        _collections = CollectionShortSerializer(many=True).create(
            validated_data['collections']
        )

        for collection in _collections:
            collection.words.add(*_new_words)

        return {'words': _new_words, 'collections': _collections}


class OtherWordsSerializerMixin:
    """Миксин для просмотра других слов с этим дополнением."""

    @extend_schema_field(WordShortCardSerializer(many=True))
    def get_other_words(self, obj, related_attr: str, *args, **kwargs) -> ReturnDict:
        other_words = obj.__getattribute__(related_attr).words.exclude(pk=obj.word.id)
        return WordShortCardSerializer(
            other_words,
            many=True,
            context={'request': self.context.get('request')},
        ).data

    @extend_schema_field(WordShortCardSerializer(many=True))
    def get_other_self_related_words(
        self, obj, related_attr: str, *args, **kwargs
    ) -> ReturnDict:
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
        words_attr = kwargs.get('words_attr', 'words')
        if attr:
            return obj.__getattribute__(attr).__getattribute__(words_attr).count() - 1
        return obj.__getattribute__(words_attr).count() - 1


class WordTranslationForWordSerializer(
    NestedSerializerMixin, OtherWordsSerializerMixin, serializers.ModelSerializer
):
    """Сериализатор перевода слова (просмотр из профиля слова)."""

    translation = WordTranslationInLineSerializer(many=False, read_only=False)
    word = WordSuperShortWithTranslations(many=False, read_only=True)
    other_words = KwargsMethodField('get_other_words', related_attr='translation')
    other_words_count = KwargsMethodField('get_other_words_count', attr='translation')

    class Meta:
        model = WordTranslations
        fields = (
            'translation',
            'word',
            'other_words_count',
            'other_words',
            'created',
        )
        read_only_fields = (
            'word',
            'other_words_count',
            'other_words',
            'created',
        )


class UsageExampleForWordSerializer(
    NestedSerializerMixin, OtherWordsSerializerMixin, serializers.ModelSerializer
):
    """Сериализатор примера использования слова (просмотр из профиля слова)."""

    example = UsageExampleInLineSerializer(many=False, read_only=False)
    word = WordSuperShortWithTranslations(many=False, read_only=True)
    other_words = KwargsMethodField('get_other_words', related_attr='example')
    other_words_count = KwargsMethodField('get_other_words_count', attr='example')

    class Meta:
        model = WordUsageExamples
        fields = (
            'example',
            'word',
            'other_words_count',
            'other_words',
            'created',
        )
        read_only_fields = (
            'word',
            'other_words_count',
            'other_words',
            'created',
        )


class DefinitionForWordSerializer(
    NestedSerializerMixin, OtherWordsSerializerMixin, serializers.ModelSerializer
):
    """Сериализатор определения слова (просмотр из профиля слова)."""

    definition = DefinitionInLineSerializer(many=False, read_only=False)
    word = WordSuperShortWithTranslations(many=False, read_only=True)
    other_words = KwargsMethodField('get_other_words', related_attr='definition')
    other_words_count = KwargsMethodField('get_other_words_count', attr='definition')

    class Meta:
        model = WordDefinitions
        fields = (
            'definition',
            'word',
            'other_words_count',
            'other_words',
            'created',
        )
        read_only_fields = (
            'word',
            'other_words_count',
            'other_words',
            'created',
        )


class ImageForWordSerializer(
    NestedSerializerMixin, OtherWordsSerializerMixin, serializers.ModelSerializer
):
    """Сериализатор ассоциации-картинки слова (просмотр из профиля слова)."""

    image = ImageInLineSerializer(many=False, read_only=False)
    word = WordSuperShortWithTranslations(many=False, read_only=True)
    other_words = KwargsMethodField('get_other_words', related_attr='image')
    other_words_count = KwargsMethodField('get_other_words_count', attr='image')

    class Meta:
        model = WordImageAssociations
        fields = (
            'image',
            'word',
            'other_words_count',
            'other_words',
            'created',
        )
        read_only_fields = (
            'word',
            'other_words_count',
            'other_words',
            'created',
        )


class QuoteForWordSerializer(
    NestedSerializerMixin, OtherWordsSerializerMixin, serializers.ModelSerializer
):
    """Сериализатор ассоциаций-цитат слова (просмотр из профиля слова)."""

    quote = QuoteInLineSerializer(many=False, read_only=False)
    word = WordSuperShortWithTranslations(many=False, read_only=True)
    other_words = KwargsMethodField('get_other_words', related_attr='quote')
    other_words_count = KwargsMethodField('get_other_words_count', attr='quote')

    class Meta:
        model = WordQuoteAssociations
        fields = (
            'quote',
            'word',
            'other_words_count',
            'other_words',
            'created',
        )
        read_only_fields = (
            'word',
            'other_words_count',
            'other_words',
            'created',
        )


class AddSelfRelatedWordsThroughDefaultsMixin(NestedSerializerMixin):
    """Миксин для создания слов с рекурсивной связью через related manager."""

    def create(
        self,
        validated_data: OrderedDict,
        related_name: str,
        response_related_name: str,
        parent_first: bool = False,
        *args,
        **kwargs,
    ) -> Word:
        to_word = validated_data.pop('to_word')
        from_word_data = validated_data.pop('from_word')
        serializer = self.get_fields()['from_word']
        self.set_child_context(serializer, 'request', self.context.get('request', None))
        from_word = serializer.create(from_word_data)
        to_word.__getattribute__(related_name).add(
            from_word, through_defaults=validated_data
        )
        return to_word.__getattribute__(response_related_name).get(from_word=from_word)


class SynonymForWordListSerializer(
    AddSelfRelatedWordsThroughDefaultsMixin,
    SynonymInLineSerializer,
):
    """Сериализатор списка синонимов слова (просмотр из профиля слова)."""

    to_word = serializers.HiddenField(default=CurrentWordDefault())

    def create(
        self, validated_data: OrderedDict, parent_first: bool = False, *args, **kwargs
    ) -> Word:
        return super().create(validated_data, 'synonyms', 'synonym_to_words')


class SynonymForWordSerializer(
    NestedSerializerMixin, OtherWordsSerializerMixin, serializers.ModelSerializer
):
    """Сериализатор синонима слова (просмотр из профиля слова)."""

    synonym = WordShortCreateSerializer(many=False, read_only=False, source='from_word')
    word = WordSuperShortWithTranslations(many=False, read_only=True, source='to_word')
    other_words = KwargsMethodField(
        'get_other_self_related_words',
        related_attr='synonyms',
    )
    other_words_count = KwargsMethodField(
        'get_other_words_count',
        attr='from_word',
        words_attr='synonyms',
    )

    class Meta:
        model = Synonym
        fields = (
            'synonym',
            'word',
            'note',
            'other_words_count',
            'other_words',
            'created',
        )
        read_only_fields = (
            'word',
            'other_words_count',
            'other_words',
            'created',
        )


class AntonymForWordListSerializer(
    AddSelfRelatedWordsThroughDefaultsMixin,
    AntonymInLineSerializer,
):
    """Сериализатор списка антонимов слова (просмотр из профиля слова)."""

    to_word = serializers.HiddenField(default=CurrentWordDefault())

    def create(
        self, validated_data: OrderedDict, parent_first: bool = False, *args, **kwargs
    ) -> Word:
        return super().create(validated_data, 'antonyms', 'antonym_to_words')


class AntonymForWordSerializer(
    NestedSerializerMixin, OtherWordsSerializerMixin, serializers.ModelSerializer
):
    """Сериализатор антонима слова (просмотр из профиля слова)."""

    antonym = WordShortCreateSerializer(many=False, read_only=False, source='from_word')
    word = WordSuperShortWithTranslations(many=False, read_only=True, source='to_word')
    other_words = KwargsMethodField(
        'get_other_self_related_words',
        related_attr='antonyms',
    )
    other_words_count = KwargsMethodField(
        'get_other_words_count',
        attr='from_word',
        words_attr='antonyms',
    )

    class Meta:
        model = Antonym
        fields = (
            'antonym',
            'word',
            'note',
            'other_words_count',
            'other_words',
            'created',
        )
        read_only_fields = (
            'word',
            'other_words_count',
            'other_words',
            'created',
        )


class FormForWordListSerializer(
    AddSelfRelatedWordsThroughDefaultsMixin,
    FormInLineSerializer,
):
    """Сериализатор списка форм слова (просмотр из профиля слова)."""

    to_word = serializers.HiddenField(default=CurrentWordDefault())

    def create(
        self, validated_data: OrderedDict, parent_first: bool = False, *args, **kwargs
    ) -> Word:
        return super().create(validated_data, 'forms', 'form_to_words')


class FormForWordSerializer(
    NestedSerializerMixin, OtherWordsSerializerMixin, serializers.ModelSerializer
):
    """Сериализатор формы слова (просмотр из профиля слова)."""

    form = WordShortCreateSerializer(many=False, read_only=False, source='from_word')
    word = WordSuperShortWithTranslations(many=False, read_only=True, source='to_word')
    other_words = KwargsMethodField(
        'get_other_self_related_words',
        related_attr='forms',
    )
    other_words_count = KwargsMethodField(
        'get_other_words_count',
        attr='from_word',
        words_attr='forms',
    )

    class Meta:
        model = Form
        fields = (
            'form',
            'word',
            'other_words_count',
            'other_words',
            'created',
        )
        read_only_fields = (
            'word',
            'other_words_count',
            'other_words',
            'created',
        )


class SimilarForWordListSerializer(
    AddSelfRelatedWordsThroughDefaultsMixin,
    SimilarInLineSerializer,
):
    """Сериализатор списка похожих слов (просмотр из профиля слова)."""

    to_word = serializers.HiddenField(default=CurrentWordDefault())

    def create(
        self, validated_data: OrderedDict, parent_first: bool = False, *args, **kwargs
    ) -> Word:
        return super().create(validated_data, 'similars', 'similar_to_words')


class SimilarForWordSerailizer(
    NestedSerializerMixin, OtherWordsSerializerMixin, serializers.ModelSerializer
):
    """Сериализатор похожего слова (просмотр из профиля слова)."""

    similar = WordShortCreateSerializer(many=False, read_only=False, source='from_word')
    word = WordSuperShortWithTranslations(many=False, read_only=True, source='to_word')
    other_words = KwargsMethodField(
        'get_other_self_related_words',
        related_attr='similars',
    )
    other_words_count = KwargsMethodField(
        'get_other_words_count',
        attr='from_word',
        words_attr='similars',
    )

    class Meta:
        model = Similar
        fields = (
            'similar',
            'word',
            'other_words_count',
            'other_words',
            'created',
        )
        read_only_fields = (
            'word',
            'other_words_count',
            'other_words',
            'created',
        )


class NoteForWordSerializer(NoteInLineSerializer):
    """Сериализатор заметки слова (просмотр из профиля слова)."""

    word = ReadableHiddenField(
        default=CurrentWordDefault(),
        serializer_class=WordSuperShortSerializer,
    )


class WordTranslationSerializer(
    ValidateLanguageMixin,
    CountObjsSerializerMixin,
    AlreadyExistSerializerHandler,
    serializers.ModelSerializer,
):
    """Сериализатор перевода (полный)."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
    )
    language = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
    )

    already_exist_detail = _('Такой перевод уже есть в вашем словаре.')

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
        return self.validate_language_is_native_or_learning(language)


class WordTranslationCreateSerializer(
    UpdateSerializerMixin, NestedSerializerMixin, WordTranslationSerializer
):
    """Сериализатор создания переводов."""

    id = serializers.IntegerField(required=False)
    language = serializers.SlugRelatedField(
        slug_field='name',
        read_only=False,
        queryset=Language.objects.all(),
    )
    words = WordShortCreateSerializer(many=True, required=True, write_only=True)

    already_exist_detail = _('Такой перевод уже есть в вашем словаре. Обновить его?')

    class Meta(WordTranslationSerializer.Meta):
        fields = WordTranslationSerializer.Meta.fields + ('words',)
        read_only_fields = ('slug',)
        objs_related_names = {
            'words': 'words',
        }


class WordTranslationListSerializer(serializers.ModelSerializer):
    """Сериализатор списка переводов."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
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
        words_count = obj.__getattribute__(objs_related_name).count()
        return words_count - 4 if words_count > 4 else 0

    @extend_schema_field({'type': 'string'})
    def get_last_4_words(self, obj: WordTranslation) -> QuerySet[Word]:
        return obj.words.order_by('-wordtranslations__created').values(
            'text', 'language__name'
        )[:4]


class DefinitionSerializer(
    CountObjsSerializerMixin, AlreadyExistSerializerHandler, serializers.ModelSerializer
):
    """Сериализатор определения (полный)."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
    )
    language = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
    )

    already_exist_detail = _('Такое определение уже есть в вашем словаре.')

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
    """Сериализатор создания определений."""

    id = serializers.IntegerField(required=False)
    language = serializers.SlugRelatedField(
        slug_field='name',
        read_only=False,
        queryset=Language.objects.all(),
    )
    words = WordShortCreateSerializer(many=True, required=True, write_only=True)

    already_exist_detail = _(
        'Такое определение уже есть в вашем словаре. Обновить его?'
    )
    default_error_messages = {
        'words_same_language_detail': {
            'words': _('Слово должно быть на том же языке, что и определение.')
        },
    }

    class Meta(DefinitionSerializer.Meta):
        fields = DefinitionSerializer.Meta.fields + ('translation', 'words')
        read_only_fields = ('slug',)
        objs_related_names = {
            'words': 'words',
        }

    def validate(self, attrs: dict) -> OrderedDict:
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
        raise serializers.ValidationError(self.error_messages[key], code=key)

    def validate_language(self, language: Language) -> Language | None:
        return self.validate_language_is_learning(language)


class DefinitionListSerializer(serializers.ModelSerializer):
    """Сериализатор списка определений."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
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
        words_count = obj.__getattribute__(objs_related_name).count()
        return words_count - 4 if words_count > 4 else 0

    @extend_schema_field({'type': 'string'})
    def get_last_4_words(self, obj: Definition) -> QuerySet[Word]:
        return obj.words.order_by('-worddefinitions__created').values_list(
            'text', flat=True
        )[:4]


class UsageExampleSerializer(
    CountObjsSerializerMixin, AlreadyExistSerializerHandler, serializers.ModelSerializer
):
    """Сериализатор примера использования (полный)."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
    )
    language = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
    )

    already_exist_detail = _('Такой пример уже есть в вашем словаре.')

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
    """Сериализатор создания примеров использования."""

    id = serializers.IntegerField(required=False)
    language = serializers.SlugRelatedField(
        slug_field='name',
        read_only=False,
        queryset=Language.objects.all(),
    )
    words = WordShortCreateSerializer(many=True, required=True, write_only=True)

    already_exist_detail = _('Такой пример уже есть в вашем словаре. Обновить его?')
    default_error_messages = {
        'words_same_language_detail': {
            'words': _('Слово должно быть на том же языке, что и пример.')
        },
    }

    class Meta(UsageExampleSerializer.Meta):
        fields = UsageExampleSerializer.Meta.fields + ('translation', 'words')
        read_only_fields = ('slug',)
        objs_related_names = {
            'words': 'words',
        }

    def validate(self, attrs: dict) -> OrderedDict:
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
        raise serializers.ValidationError(self.error_messages[key], code=key)

    def validate_language(self, language: Language) -> Language | None:
        return self.validate_language_is_learning(language)


class UsageExampleListSerializer(serializers.ModelSerializer):
    """Сериализатор списка примеров использования."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
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
        words_count = obj.__getattribute__(objs_related_name).count()
        return words_count - 4 if words_count > 4 else 0

    @extend_schema_field({'type': 'string'})
    def get_last_4_words(self, obj: UsageExample) -> QuerySet[Word]:
        return obj.words.order_by('-wordusageexamples').values_list('text', flat=True)[
            :4
        ]


class ImageListSerializer(serializers.ModelSerializer):
    """Сериализатор списка ассоциаций-картинок."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
    )
    image = HybridImageField()
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
            'name',
            'other_words_count',
            'last_4_words',
        )
        read_only_fields = (
            'id',
            'other_words_count',
            'last_4_words',
        )

    @extend_schema_field({'type': 'integer'})
    def get_other_words_count(
        self,
        obj: ImageAssociation,
        objs_related_name: str = '',
    ) -> int:
        words_count = obj.__getattribute__(objs_related_name).count()
        return words_count - 4 if words_count > 4 else 0

    @extend_schema_field({'type': 'string'})
    def get_last_4_words(self, obj: ImageAssociation) -> QuerySet[Word]:
        return obj.words.order_by('-wordimageassociations').values_list(
            'text', flat=True
        )[:4]


class ImageShortSerailizer(serializers.ModelSerializer):
    """Сериализатор картинки изучаемого языка языка (короткий)."""

    language = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
    )

    class Meta:
        model = LanguageImage
        fields = (
            'id',
            'language',
            'image',
        )
        read_only_fields = fields


class AssociationsCreateSerializer(serializers.Serializer):
    """Сериализатор создания ассоциаций."""

    quotes_associations = QuoteInLineSerializer(
        many=True,
        required=False,
    )
    images_associations = PresentablePrimaryKeyRelatedField(
        queryset=ImageAssociation.objects.all(),
        required=False,
        many=True,
        write_only=True,
        presentation_serializer=ImageInLineSerializer,
    )

    def create(self, validated_data: OrderedDict) -> dict:
        _quotes_data = self.get_fields()['quotes_associations'].create(
            validated_data['quotes_associations']
        )

        return {
            'quotes': _quotes_data,
            'images': validated_data['images_associations'],
        }


class SynonymSerializer(
    ValidateLanguageMixin,
    CountObjsSerializerMixin,
    AlreadyExistSerializerHandler,
    GetImagesSerializerMixin,
    serializers.ModelSerializer,
):
    """Сериализатор синонима (полный)."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
    )
    language = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
    )
    images_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='images_associations',
    )

    already_exist_detail = _('Такое слово уже есть в вашем словаре.')

    class Meta:
        model = Word
        fields = (
            'id',
            'slug',
            'author',
            'language',
            'text',
            'images_count',
            'images',
        )
        read_only_fields = (
            'id',
            'slug',
            'images_count',
            'images',
        )

    def validate_language(self, language: Language) -> Language | None:
        return self.validate_language_is_learning(language)


class AntonymSerializer(SynonymSerializer):
    """Сериализатор антонима (полный)."""

    pass


class SimilarSerializer(SynonymSerializer):
    """Сериализатор похожего слова (полный)."""

    pass


class TagListSerializer(TagSerializer, CountObjsSerializerMixin):
    """Сериализатор списка тегов пользователя."""

    words_count = KwargsMethodField('get_objs_count', objs_related_name='words')

    class Meta:
        model = Tag
        fields = ('name', 'author', 'words_count')
        read_only_fields = ('words_count',)


class TypeSerializer(CountObjsSerializerMixin, serializers.ModelSerializer):
    """Сериализатор для просмотра всех возможных типов слов и фраз."""

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
    """Сериализатор групп форм (короткая форма)."""

    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
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
        return self.validate_language_is_learning(language)


class CollectionSerializer(CollectionShortSerializer):
    """Сериализатор коллекции (полный)."""

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
        return (
            obj.words.values('language__name').annotate(words_count=Count('language'))
        ).order_by('-words_count')

    @extend_schema_field({'type': 'integer'})
    def get_words_images_count(self, obj: Collection) -> int:
        return obj.words.filter(images_associations__isnull=False).count()

    @extend_schema_field({'type': 'object'})
    def get_words_images(self, obj: Collection) -> QuerySet[Word]:
        return obj.words.filter(images_associations__isnull=False).values_list(
            'images_associations__image', flat=True
        )


class LearningLanguageWithLastWordsSerailizer(LearningLanguageShortSerailizer):
    """
    Сериализатор изучаемых языков пользователя
    (короткая форма для отображения в списке).
    """

    last_10_words = serializers.SerializerMethodField('get_last_10_words')

    class Meta:
        model = UserLearningLanguage
        fields = (
            'id',
            'slug',
            'user',
            'language',
            'level',
            'image',
            'words_count',
            'inactive_words_count',
            'active_words_count',
            'mastered_words_count',
            'last_10_words',
        )
        read_only_fields = (
            'id',
            'slug',
            'image',
            'words_count',
            'inactive_words_count',
            'active_words_count',
            'mastered_words_count',
            'last_10_words',
        )

    @extend_schema_field(WordStandartCardSerializer(many=True))
    def get_last_10_words(self, obj: UserLearningLanguage) -> ReturnDict:
        words = obj.user.words.filter(language=obj.language)[:10]
        return WordStandartCardSerializer(
            words, many=True, context={'request': self.context['request']}
        ).data


class UserDetailsSerializer(
    CountObjsSerializerMixin,
    UserShortSerializer,
):
    """Сериализатор просмотра профиля пользователя."""

    native_languages = PresentablePrimaryKeyRelatedField(
        queryset=Language.objects.all(),
        required=False,
        many=True,
        presentation_serializer=LanguageSerializer,
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
    words_count = KwargsMethodField('get_objs_count', objs_related_name='words')
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
        if len(languages) > UsersAmountLimits.MAX_NATIVE_LANGUAGES_AMOUNT:
            raise serializers.ValidationError(
                UsersAmountLimits.get_error_message(
                    limit=UsersAmountLimits.MAX_NATIVE_LANGUAGES_AMOUNT
                ),
                code='native_languages_max_amount_exceeded',
            )
        return languages

    @extend_schema_field(WordStandartCardSerializer(many=True))
    def get_last_10_words(self, obj) -> ReturnDict:
        words = obj.words.all()[:10]
        return WordStandartCardSerializer(
            words, many=True, context={'request': self.context['request']}
        ).data


class MainPageSerailizer(UserDetailsSerializer):
    collections_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='collections',
    )
    last_10_collections = serializers.SerializerMethodField('get_last_10_collections')
    tags_count = KwargsMethodField('get_objs_count', objs_related_name='tags')
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
        return serializer_class(
            obj.__getattribute__(objs_related_name).all()[:10],
            many=True,
            context={'request': self.context['request']},
        ).data

    @extend_schema_field(CollectionShortSerializer(many=True))
    def get_last_10_collections(self, obj) -> ReturnDict:
        return self.get_last_10_objs(obj, 'collections', CollectionShortSerializer)

    @extend_schema_field(TagListSerializer(many=True))
    def get_last_10_tags(self, obj) -> ReturnDict:
        return self.get_last_10_objs(obj, 'tags', TagListSerializer)

    @extend_schema_field(ImageListSerializer(many=True))
    def get_last_10_images(self, obj) -> ReturnDict:
        return self.get_last_10_objs(obj, 'imageassociations', ImageListSerializer)

    @extend_schema_field(DefinitionListSerializer(many=True))
    def get_last_10_definitions(self, obj) -> ReturnDict:
        return self.get_last_10_objs(obj, 'definitions', DefinitionListSerializer)

    @extend_schema_field(UsageExampleListSerializer(many=True))
    def get_last_10_examples(self, obj) -> ReturnDict:
        return self.get_last_10_objs(obj, 'usageexamples', UsageExampleListSerializer)

    @extend_schema_field(WordTranslationListSerializer(many=True))
    def get_last_10_translations(self, obj) -> ReturnDict:
        return self.get_last_10_objs(
            obj, 'wordtranslations', WordTranslationListSerializer
        )
