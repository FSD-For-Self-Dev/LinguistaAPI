"""Сериализаторы приложения vocabulary."""

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.translation import gettext as _

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from users.serializers import UserSerializer

from .constants import AmountLimits
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
)
from .serializers_fields import (
    ReadableHiddenField,
    CurrentWordDefault,
    WordSameLanguageDefault,
    KwargsMethodField,
)
from .serializers_mixins import (
    ListUpdateSerializer,
    NestedSerializerMixin,
    FavoriteSerializerMixin,
    CountObjsSerializerMixin,
    AlreadyExistSerializerHandler,
    UpdateSerializerMixin,
)

User = get_user_model()


class NoteInLineSerializer(serializers.ModelSerializer):
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(), slug_field='username'
    )

    class Meta:
        model = Note
        fields = ('id', 'text', 'word', 'author', 'created', 'modified')
        read_only_fields = ('id', 'created', 'modified')
        list_serializer_class = ListUpdateSerializer
        foreign_key_field_name = 'word'


class NoteInLineUpdateSerializer(NoteInLineSerializer):
    id = serializers.IntegerField(required=False)


class TranslationSerializer(AlreadyExistSerializerHandler):
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(), slug_field='username'
    )
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        required=True,
        # нужно будет добавить inital на родной язык пользователя
    )

    already_exist_detail = _('Такой перевод уже есть в вашем словаре. Обновить его?')

    class Meta:
        model = WordTranslation
        fields = ('id', 'text', 'language', 'author', 'created', 'modified')
        read_only_fields = ('created', 'modified')
        list_serializer_class = ListUpdateSerializer

    # validate language in native or learning


class TranslationUpdateSerializer(TranslationSerializer):
    id = serializers.IntegerField(required=False)


class UsageExampleSerializer(serializers.ModelSerializer):
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(), slug_field='username'
    )

    class Meta:
        model = UsageExample
        fields = ('id', 'author', 'text', 'translation', 'created', 'modified')
        read_only_fields = ('created', 'modified')
        list_serializer_class = ListUpdateSerializer


class UsageExampleUpdateSerializer(UsageExampleSerializer):
    id = serializers.IntegerField(required=False)


class DefinitionSerializer(serializers.ModelSerializer):
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(), slug_field='username'
    )

    class Meta:
        model = Definition
        fields = ('id', 'author', 'text', 'translation', 'created', 'modified')
        read_only_fields = ('created', 'modified')
        list_serializer_class = ListUpdateSerializer


class DefinitionUpdateSerializer(DefinitionSerializer):
    id = serializers.IntegerField(required=False)


class CollectionShortSerializer(CountObjsSerializerMixin, FavoriteSerializerMixin):
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(), slug_field='username'
    )
    words_count = KwargsMethodField('get_objs_count', objs_related_name='words')
    last_3_words = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        favorite_model = FavoriteCollection
        favorite_model_field = 'collection'
        fields = (
            'id',
            'slug',
            'author',
            'title',
            'favorite',
            'description',
            'words_count',
            'last_3_words',
            'created',
            'modified',
        )
        read_only_fields = ('slug', 'words_count', 'created', 'modified')
        list_serializer_class = ListUpdateSerializer

    @extend_schema_field({'type': 'string'})
    def get_last_3_words(self, obj):
        if hasattr(obj, 'words'):
            return obj.words.order_by('-wordsincollections__created').values_list(
                'text', flat=True
            )[:3]
        return None


class CollectionShortUpdateSerializer(CollectionShortSerializer):
    id = serializers.IntegerField(required=False)


class FormsGroupSerializer(serializers.ModelSerializer):
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        slug_field='username',
        # source='forms_group.author'
    )
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(),
        slug_field='name',
        required=True,
        # source='forms_group.language'
    )
    # id = serializers.ReadOnlyField(source='forms_group.id')
    # slug = serializers.ReadOnlyField(source='forms_group.slug')
    # name = serializers.CharField(source='forms_group.name', required=True)
    # color = serializers.CharField(source='forms_group.color', required=False)
    # translation = serializers.CharField(source='forms_group.translation', required=False)

    class Meta:
        model = FormsGroup
        fields = (
            'id',
            'slug',
            'author',
            'language',
            'name',
            'color',
            'translation',
            # 'word',
        )
        read_only_fields = ('slug', 'author')  # 'word'
        list_serializer_class = ListUpdateSerializer
        # foreign_key_field_name = 'word'

    def validate_name(self, name):
        if name.capitalize() == 'Infinitive':
            raise serializers.ValidationError(
                'The forms group `Infinitive` already exists.'
            )
        return name


class FormsGroupUpdateSerializer(FormsGroupSerializer):
    id = serializers.IntegerField(required=False)


class TagSerializer(AlreadyExistSerializerHandler):
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(), slug_field='username'
    )
    name = serializers.CharField()

    already_exist_detail = _('Такой тег уже есть в вашем словаре. Обновить его?')

    class Meta:
        model = Tag
        fields = ('name', 'author')
        list_serializer_class = ListUpdateSerializer


class WordShortSerializer(
    NestedSerializerMixin, AlreadyExistSerializerHandler, CountObjsSerializerMixin
):
    """Сериализатор для записи и чтения слов в короткой форме."""

    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(), slug_field='name', required=True
    )
    types = serializers.SlugRelatedField(
        slug_field='name', queryset=Type.objects.all(), many=True, required=False
    )
    tags = TagSerializer(many=True, required=False)
    notes = NoteInLineSerializer(many=True, required=False)
    translations = TranslationSerializer(many=True, required=False)
    translations_count = KwargsMethodField(
        'get_objs_count', objs_related_name='translations'
    )
    examples = UsageExampleSerializer(many=True, required=False)
    examples_count = KwargsMethodField('get_objs_count', objs_related_name='examples')
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        serializer_class=UserSerializer,
        many=False,
    )

    already_exist_detail = _('Такое слово уже есть в вашем словаре. Обновить его?')

    class Meta:
        model = Word
        fields = (
            'id',
            'slug',
            'language',
            'text',
            'author',
            'types',
            'tags',
            'is_problematic',
            'activity',
            'translations_count',
            'translations',
            'examples_count',
            'examples',
            'notes',
            'created',
            'modified',
        )
        read_only_fields = (
            'slug',
            'activity',
            'translations_count',
            'examples_count' 'created',
            'modified',
        )
        list_serializer_class = ListUpdateSerializer
        objs_related_names = {
            'examples': 'examples',
            'translations': 'translations',
        }
        amount_limit_fields = {
            'translations': AmountLimits.MAX_TRANSLATIONS_AMOUNT,
            'examples': AmountLimits.MAX_EXAMPLES_AMOUNT,
            'notes': AmountLimits.MAX_NOTES_AMOUNT,
        }


class WordShortUpdateSerializer(UpdateSerializerMixin, WordShortSerializer):
    id = serializers.IntegerField(required=False)
    translations = TranslationUpdateSerializer(many=True, required=False)
    examples = UsageExampleUpdateSerializer(many=True, required=False)


class WordSelfRelatedSerializer(NestedSerializerMixin):
    to_word = serializers.HiddenField(default=CurrentWordDefault())
    from_word = WordShortSerializer(read_only=False, required=True, many=False)

    validate_same_language = True
    default_error_messages = {
        'same_language_detail': _('Validation error.'),
        'same_words_detail': _('Object can not be the same word.'),
    }

    class Meta:
        abstract = True

    def validate(self, attrs):
        to_word = attrs.get('to_word', None)
        from_word = attrs.get('from_word', None)
        if to_word and from_word:
            if (
                self.validate_same_language
                and 'language' in from_word
                and to_word.language != from_word['language']
            ):
                self.fail('same_language_detail')
            from_word_slug = Word.get_slug(**from_word)
            if to_word.slug == from_word_slug:
                self.fail('same_words_detail')
        return super().validate(attrs)

    def create(self, validated_data, parent_first=False):
        return super().create(validated_data, parent_first)

    def fail(self, key, **kwargs):
        raise serializers.ValidationError(self.error_messages[key], code=key)


class SynonymInLineSerializer(WordSelfRelatedSerializer):
    to_word = serializers.PrimaryKeyRelatedField(read_only=True)

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
            'id',
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


class SynonymInLineUpdateSerializer(SynonymInLineSerializer):
    id = serializers.IntegerField(required=False)
    from_word = WordShortUpdateSerializer(read_only=False, required=True, many=False)


class AntonymInLineSerializer(WordSelfRelatedSerializer):
    to_word = serializers.PrimaryKeyRelatedField(read_only=True)

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
            'id',
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


class AntonymInLineUpdateSerializer(AntonymInLineSerializer):
    id = serializers.IntegerField(required=False)
    from_word = WordShortUpdateSerializer(read_only=False, required=True, many=False)


class FormInLineSerializer(WordSelfRelatedSerializer):
    to_word = serializers.PrimaryKeyRelatedField(read_only=True)

    default_error_messages = {
        'same_language_detail': {
            'forms': _('Форма должна быть на том же языке, что и само слово.')
        },
        'same_words_detail': {'forms': _('Само слово не может быть своей формой.')},
    }

    class Meta:
        model = Form
        fields = (
            'id',
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


class FormInLineUpdateSerializer(FormInLineSerializer):
    id = serializers.IntegerField(required=False)
    from_word = WordShortUpdateSerializer(read_only=False, required=True, many=False)


class SimilarInLineSerializer(WordSelfRelatedSerializer):
    to_word = serializers.PrimaryKeyRelatedField(read_only=True)

    validate_same_language = False
    default_error_messages = {
        'same_words_detail': {'similars': _('Само слово нельзя добавить в похожие.')},
    }

    class Meta:
        model = Similar
        fields = (
            'id',
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


class SimilarInLineUpdateSerializer(SimilarInLineSerializer):
    id = serializers.IntegerField(required=False)
    from_word = WordShortUpdateSerializer(read_only=False, required=True, many=False)


class WordSerializer(
    NestedSerializerMixin,
    FavoriteSerializerMixin,
    CountObjsSerializerMixin,
    AlreadyExistSerializerHandler,
):
    """Расширенный (полный) сериализатор слова."""

    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(), slug_field='name', required=True
    )
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        serializer_class=UserSerializer,
        many=False,
    )
    types = serializers.SlugRelatedField(
        slug_field='name', queryset=Type.objects.all(), many=True, required=False
    )
    tags = TagSerializer(many=True, required=False)
    forms_groups = FormsGroupSerializer(many=True, required=False)
    translations_count = KwargsMethodField(
        'get_objs_count', objs_related_name='translations'
    )
    translations = TranslationSerializer(many=True, required=False)
    examples_count = KwargsMethodField('get_objs_count', objs_related_name='examples')
    examples = UsageExampleSerializer(many=True, required=False)
    definitions_count = KwargsMethodField(
        'get_objs_count', objs_related_name='definitions'
    )
    definitions = DefinitionSerializer(many=True, required=False)
    synonyms_count = KwargsMethodField('get_objs_count', objs_related_name='synonyms')
    synonyms = SynonymInLineSerializer(
        many=True, required=False, source='synonym_to_words'
    )
    antonyms_count = KwargsMethodField('get_objs_count', objs_related_name='antonyms')
    antonyms = AntonymInLineSerializer(
        many=True, required=False, source='antonym_to_words'
    )
    forms_count = KwargsMethodField('get_objs_count', objs_related_name='forms')
    forms = FormInLineSerializer(many=True, required=False, source='form_to_words')
    similars_count = KwargsMethodField('get_objs_count', objs_related_name='similars')
    similars = SimilarInLineSerializer(
        many=True, required=False, source='similar_to_words'
    )
    collections_count = KwargsMethodField(
        'get_objs_count', objs_related_name='collections'
    )
    collections = CollectionShortSerializer(many=True, required=False)
    notes = NoteInLineSerializer(many=True, required=False)

    already_exist_detail = _('Такое слово уже есть в вашем словаре. Обновить его?')

    class Meta:
        model = Word
        favorite_model = FavoriteWord
        favorite_model_field = 'word'
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
            'activity',
            'translations_count',
            'translations',
            'examples_count',
            'examples',
            'definitions_count',
            'definitions',
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
            'notes',
            'created',
            'modified',
        )
        read_only_fields = (
            'id',
            'slug',
            'translations_count',
            'examples_count' 'definitions_count',
            'synonyms_count',
            'antonyms_count',
            'forms_count',
            'similars_count',
            'collections_count',
            'activity',
            'created',
            'modified',
        )
        objs_related_names = {
            'examples': 'examples',
            'definitions': 'definitions',
            'translations': 'translations',
            'tags': 'tags',
            'forms_groups': 'forms_groups',
            'collections': 'collections',
        }
        amount_limit_fields = {
            'translations': AmountLimits.MAX_TRANSLATIONS_AMOUNT,
            'examples': AmountLimits.MAX_EXAMPLES_AMOUNT,
            'definitions': AmountLimits.MAX_DEFINITIONS_AMOUNT,
            'synonyms': AmountLimits.MAX_SYNONYMS_AMOUNT,
            'antonyms': AmountLimits.MAX_ANTONYMS_AMOUNT,
            'forms': AmountLimits.MAX_FORMS_AMOUNT,
            'similars': AmountLimits.MAX_SIMILARS_AMOUNT,
            'notes': AmountLimits.MAX_NOTES_AMOUNT,
        }

    def create(self, validated_data, parent_first=True):
        return super().create(validated_data, parent_first)

    def validate(self, attrs):
        forms_groups = attrs.get('forms_groups', None)
        for forms_group in forms_groups:
            if 'language' in forms_group and (
                self.instance
                and forms_group['language'] != self.instance.language
                or 'language' in attrs
                and forms_group['language'] != attrs['language']
            ):
                raise serializers.ValidationError(
                    {
                        'forms_groups': _(
                            'Группа форм должна быть на том же языке, что и само '
                            'слово.'
                        )
                    }
                )
        return super().validate(attrs)


class WordUpdateSerializer(WordSerializer):
    id = serializers.IntegerField(required=False)
    forms_groups = FormsGroupUpdateSerializer(many=True, required=False)
    translations = TranslationUpdateSerializer(many=True, required=False)
    examples = UsageExampleUpdateSerializer(many=True, required=False)
    definitions = DefinitionUpdateSerializer(many=True, required=False)
    synonyms = SynonymInLineUpdateSerializer(
        many=True, required=False, source='synonym_to_words'
    )
    antonyms = AntonymInLineUpdateSerializer(
        many=True, required=False, source='antonym_to_words'
    )
    forms = FormInLineUpdateSerializer(
        many=True, required=False, source='form_to_words'
    )
    similars = SimilarInLineUpdateSerializer(
        many=True, required=False, source='similar_to_words'
    )
    collections = CollectionShortUpdateSerializer(many=True, required=False)


class FormSerializer(serializers.ModelSerializer):
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(), slug_field='username'
    )
    language = serializers.HiddenField(
        default=WordSameLanguageDefault()
    )  # убрать HiddenField
    # forms_groups = CreatableSlugRelatedField(
    #     slug_field='name',
    #     many=True,
    #     read_only=False,
    #     required=False,
    #     need_author=True,
    #     capitalize=True,
    #     queryset=FormsGroup.objects.all(),
    # )  # убрать CreatableSlugRelatedField

    class Meta:
        model = Word
        fields = ('id', 'language', 'author', 'text', 'forms_groups')
        read_only_fields = ('id', 'author')


class TypeSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра всех возможных типов слов и фраз."""

    class Meta:
        model = Type
        fields = (
            'id',
            'name',
            'slug',
            'words_count',
        )
        read_only_fields = fields


class CollectionSerializer(CollectionShortSerializer):
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        serializer_class=UserSerializer,
        many=False,
    )
    words = WordShortSerializer(many=True, required=False)

    class Meta:
        model = Collection
        fields = (
            'id',
            'slug',
            'author',
            'title',
            'description',
            # 'favorite',
            'created',
            'modified',
            'words',
        )
        read_only_fields = ('id', 'slug', 'author', 'created', 'modified')


class NoteSerializer(serializers.ModelSerializer):
    word = ReadableHiddenField(default=CurrentWordDefault(), slug_field='slug')
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(), slug_field='username'
    )

    class Meta:
        model = Note
        fields = ('id', 'text', 'created', 'word', 'author')
        read_only_fields = ('id', 'created')


class SynonymSerializer(WordSelfRelatedSerializer):
    same_language_detail = 'Синоним должен быть на том же языке, что и само слово.'

    class Meta:
        model = Synonym
        fields = (
            'to_word',
            'from_word',
            'note',
            'created',
        )
        read_only_fields = ('created',)


class SynonymDetailSerializer(SynonymSerializer):
    to_word = WordSerializer(read_only=True, many=False)
    from_word = WordSerializer(read_only=True, many=False)

    class Meta(SynonymSerializer.Meta):
        read_only_fields = (
            'to_word',
            'from_word',
            'created',
        )


class AntonymSerializer(WordSelfRelatedSerializer):
    same_language_detail = 'Антоним должен быть на том же языке, что и само слово.'

    class Meta:
        model = Antonym
        fields = (
            'to_word',
            'from_word',
            'note',
            'created',
        )
        read_only_fields = ('created',)


class AntonymDetailSerializer(AntonymSerializer):
    to_word = WordSerializer(read_only=True, many=False)
    from_word = WordSerializer(read_only=True, many=False)

    class Meta(AntonymSerializer.Meta):
        read_only_fields = (
            'to_word',
            'from_word',
            'created',
        )


class SimilarSerializer(WordSelfRelatedSerializer):
    validate_same_language = False

    class Meta:
        model = Similar
        fields = (
            'to_word',
            'from_word',
            'created',
        )
        read_only_fields = ('created',)


class SimilarDetailSerializer(SimilarSerializer):
    to_word = WordSerializer(many=False, required=True)
    from_word = WordSerializer(many=False, required=True)

    class Meta(SimilarSerializer.Meta):
        read_only_fields = (
            'to_word',
            'from_word',
            'created',
        )


class CollectionsListSerializer(serializers.Serializer):
    collections = serializers.SlugRelatedField(
        slug_field='slug',
        many=True,
        queryset=Collection.objects.all(),
        read_only=False,
        required=True,
    )


class WordsListSerializer(serializers.Serializer):  # *
    words = serializers.SlugRelatedField(
        slug_field='slug',
        many=True,
        queryset=Word.objects.all(),
        read_only=False,
        required=True,
    )


class WordRelatedSerializer(serializers.ModelSerializer):
    word = serializers.HiddenField(default=CurrentWordDefault())

    @transaction.atomic
    def create(self, validated_data):
        word = validated_data.pop('word', [])
        _objs = validated_data.pop(self.objs_source_name, [])
        word.__getattribute__(self.objs_related_name).add(*_objs)
        return _objs


class ExamplesListSerializer(WordRelatedSerializer):  # use hyperlinks
    # examples = serializers.SlugRelatedField(
    #     slug_field='slug',
    #     many=True,
    #     queryset=UsageExample.objects.all(),
    #     read_only=False,
    #     required=True,
    # )
    examples = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=UsageExample.objects.all(),
        read_only=False,
        required=True,
        source='example',
    )

    objs_related_name = 'examples'
    objs_source_name = 'example'

    class Meta:
        model = WordUsageExamples
        fields = ('word', 'examples')


class DefinitionsListSerializer(WordRelatedSerializer):
    definitions = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Definition.objects.all(),
        read_only=False,
        required=True,
        source='definition',
    )

    objs_related_name = 'definitions'
    objs_source_name = 'definition'

    class Meta:
        model = WordDefinitions
        fields = ('word', 'definitions')


class TranslationsListSerializer(WordRelatedSerializer):
    translations = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=WordTranslation.objects.all(),
        read_only=False,
        required=True,
        source='translation',
    )

    objs_related_name = 'translations'
    objs_source_name = 'translation'

    class Meta:
        model = WordTranslations
        fields = ('word', 'translations')


class WordSelfRelatedListSerializerMixin(serializers.ModelSerializer):
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(), slug_field='username'
    )
    to_word = serializers.HiddenField(default=CurrentWordDefault())
    words = serializers.SlugRelatedField(
        slug_field='slug',
        many=True,
        queryset=Word.objects.all(),
        read_only=False,
        required=True,
        source='from_word',
    )

    @transaction.atomic
    def create(self, validated_data):
        word = validated_data.pop('to_word', [])
        _objs = validated_data.pop('from_word', [])
        word.__getattribute__(self.objs_related_name).add(
            *_objs, through_defaults=validated_data
        )
        return _objs


class SynonymsListSerializer(WordSelfRelatedListSerializerMixin):
    objs_related_name = 'synonyms'

    class Meta:
        model = Synonym
        fields = ('author', 'to_word', 'words')


class AntonymsListSerializer(WordSelfRelatedListSerializerMixin):
    objs_related_name = 'antonyms'

    class Meta:
        model = Antonym
        fields = ('author', 'to_word', 'words')


class SimilarsListSerializer(WordSelfRelatedListSerializerMixin):
    objs_related_name = 'similars'

    class Meta:
        model = Similar
        fields = ('author', 'to_word', 'words')
