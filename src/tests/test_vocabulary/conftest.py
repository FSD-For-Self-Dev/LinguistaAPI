import pytest

from model_bakery import baker

from apps.vocabulary.models import (
    Word,
    FormGroup,
    WordTranslation,
    UsageExample,
    Definition,
    WordType,
    Tag,
    Note,
    Collection,
    QuoteAssociation,
)
from apps.languages.models import Language, UserLearningLanguage, UserNativeLanguage


@pytest.fixture
def language(request):
    def get_language(data=False, **kwargs):
        language = baker.make(Language)
        return language.name if data else language

    return get_language


@pytest.fixture
def learning_language(request):
    def get_learning_language(user, data=False, **kwargs):
        language = baker.make(Language)
        UserLearningLanguage.objects.create(user=user, language=language)
        if data:
            return language.name
        return language

    return get_learning_language


@pytest.fixture
def native_language(request):
    def get_native_language(user, data=False, **kwargs):
        language = baker.make(Language)
        UserNativeLanguage.objects.create(user=user, language=language)
        if data:
            return language.name
        return language

    return get_native_language


@pytest.fixture
def languages(request):
    def get_languages(name=False, extra_data={}, _quantity=1, **kwargs):
        languages = baker.make(
            Language, **extra_data, _quantity=_quantity, _fill_optional=False
        )
        return [language.name for language in languages] if name else languages

    return get_languages


@pytest.fixture
def learning_languages(request):
    def get_learning_languages(user, data=False, _quantity=1, **kwargs):
        languages = baker.make(Language, _quantity=_quantity)
        learning_languages = [
            baker.make(UserLearningLanguage, language=language, user=user)
            for language in languages
        ]
        if data:
            source_data = [
                {
                    'name': language.name.capitalize(),
                    'flag_icon': language.flag_icon,
                }
                for language in languages
            ]
            expected_data = source_data
            return (learning_languages, source_data, expected_data)
        return learning_languages

    return get_learning_languages


@pytest.fixture
def native_languages(request):
    def get_native_languages(user, data=False, _quantity=1, **kwargs):
        languages = baker.make(Language, _quantity=_quantity)
        native_languages = [
            baker.make(UserNativeLanguage, language=language, user=user)
            for language in languages
        ]
        if data:
            source_data = [
                {
                    'name': language.name,
                    'flag_icon': language.flag_icon,
                }
                for language in languages
            ]
            expected_data = source_data
            return (native_languages, source_data, expected_data)
        return native_languages

    return get_native_languages


@pytest.fixture
def words_simple_data(request):
    def get_words_simple_data(user, data=False, make=False, _quantity=1, **kwargs):
        language = kwargs.get('language', None)
        if not language:
            language = baker.make(Language)
            UserLearningLanguage.objects.create(user=user, language=language)
        if make:
            objs = baker.make(
                Word,
                author=user,
                language=language,
                _quantity=_quantity,
                _fill_optional=True,
            )
        else:
            objs = baker.prepare(
                Word,
                author=user,
                language=language,
                _quantity=_quantity,
                _fill_optional=True,
            )
        if data:
            source = [
                {
                    'text': obj.text,
                    'language': obj.language.name,
                }
                for obj in objs
            ]
            expected = [
                {
                    'text': obj.text,
                    'language': obj.language.name,
                }
                for obj in objs
            ]
            return (objs, source, expected)
        return objs

    return get_words_simple_data


@pytest.fixture
def word_types(request):
    def get_word_types_data(
        user=None, data=False, source_only=False, _quantity=1, **kwargs
    ):
        objs = baker.make(WordType, _quantity=_quantity)
        if data:
            source_data = [obj.name for obj in objs]
            expected_data = source_data
            return source_data if source_only else (objs, source_data, expected_data)
        return objs

    return get_word_types_data


@pytest.fixture
def word_tags(request):
    def get_word_tags_data(user, data=False, _quantity=1, make=False, **kwargs):
        if make:
            objs = baker.make(
                Tag, author=user, _quantity=_quantity, _fill_optional=True
            )
        else:
            objs = baker.prepare(
                Tag, author=user, _quantity=_quantity, _fill_optional=True
            )
        if data:
            source = [{'name': obj.name} for obj in objs]
            expected = source
            return (objs, source, expected)
        return objs

    return get_word_tags_data


@pytest.fixture
def word_form_groups(request):
    def get_word_form_groups(user, data=False, _quantity=1, make=False, **kwargs):
        language = kwargs.get('language', None)
        if not language:
            language = baker.make(Language)
            UserLearningLanguage.objects.create(user=user, language=language)
        if make:
            objs = baker.make(
                FormGroup,
                author=user,
                language=language,
                _quantity=_quantity,
                _fill_optional=True,
            )
        else:
            objs = baker.prepare(
                FormGroup,
                author=user,
                language=language,
                _quantity=_quantity,
                _fill_optional=True,
            )
        if data:
            source = [
                {
                    'name': obj.name,
                    'language': obj.language.name,
                    'color': '#000000',
                    'translation': obj.translation,
                }
                for obj in objs
            ]
            expected = [
                {
                    'name': obj.name.capitalize(),
                    'language': obj.language.name,
                    'color': '#000000',
                    'translation': obj.translation,
                }
                for obj in objs
            ]
            return (objs, source, expected)
        return objs

    return get_word_form_groups


@pytest.fixture
def word_translations(request):
    def get_word_translation(user, data=False, _quantity=1, make=False, **kwargs):
        language = kwargs.get('language', None)
        if not language:
            language = baker.make(Language)
            UserNativeLanguage.objects.create(user=user, language=language)
        if make:
            objs = baker.make(
                WordTranslation,
                author=user,
                language=language,
                _quantity=_quantity,
                _fill_optional=True,
            )
        else:
            objs = baker.prepare(
                WordTranslation,
                author=user,
                language=language,
                _quantity=_quantity,
                _fill_optional=True,
            )
        if data:
            source = [
                {
                    'text': obj.text,
                    'language': obj.language.name,
                }
                for obj in objs
            ]
            expected = [
                {
                    'text': obj.text,
                    'language': obj.language.name,
                }
                for obj in objs
            ]
            return (objs, source, expected)
        return objs

    return get_word_translation


@pytest.fixture
def word_usage_examples(request):
    def get_word_usage_example(user, data=False, _quantity=1, make=False, **kwargs):
        language = kwargs.get('language', None)
        if not language:
            language = baker.make(Language)
            UserLearningLanguage.objects.create(user=user, language=language)
        if make:
            objs = baker.make(
                UsageExample,
                author=user,
                language=language,
                _quantity=_quantity,
                _fill_optional=True,
            )
        else:
            objs = baker.prepare(
                UsageExample,
                author=user,
                language=language,
                _quantity=_quantity,
                _fill_optional=True,
            )
        if data:
            source = [
                {
                    'text': obj.text,
                    'language': obj.language.name,
                    'translation': obj.translation,
                }
                for obj in objs
            ]
            expected = [
                {
                    'text': obj.text,
                    'language': obj.language.name,
                    'translation': obj.translation,
                }
                for obj in objs
            ]
            return (objs, source, expected)
        return objs

    return get_word_usage_example


@pytest.fixture
def word_definitions(request):
    def get_word_definition(user, data=False, _quantity=1, make=False, **kwargs):
        language = kwargs.get('language', None)
        if not language:
            language = baker.make(Language)
            UserLearningLanguage.objects.create(user=user, language=language)
        if make:
            objs = baker.make(
                Definition,
                author=user,
                language=language,
                _quantity=_quantity,
                _fill_optional=True,
            )
        else:
            objs = baker.prepare(
                Definition,
                author=user,
                language=language,
                _quantity=_quantity,
                _fill_optional=True,
            )
        if data:
            source = [
                {
                    'text': obj.text,
                    'language': obj.language.name,
                    'translation': obj.translation,
                }
                for obj in objs
            ]
            expected = [
                {
                    'text': obj.text,
                    'language': obj.language.name,
                    'translation': obj.translation,
                }
                for obj in objs
            ]
            return (objs, source, expected)
        return objs

    return get_word_definition


@pytest.fixture
def word_quote_associations(request):
    def get_word_quote_associations(
        user, data=False, _quantity=1, make=False, **kwargs
    ):
        if make:
            objs = baker.make(
                QuoteAssociation, author=user, _quantity=_quantity, _fill_optional=True
            )
        else:
            objs = baker.prepare(
                QuoteAssociation, author=user, _quantity=_quantity, _fill_optional=True
            )
        if data:
            source = [
                {
                    'text': obj.text,
                    'quote_author': obj.quote_author,
                }
                for obj in objs
            ]
            expected = [
                {
                    'text': obj.text,
                    'quote_author': obj.quote_author,
                }
                for obj in objs
            ]
            return (objs, source, expected)
        return objs

    return get_word_quote_associations


@pytest.fixture
def word_notes(request):
    def get_word_notes(user, data=False, _quantity=1, make=False, **kwargs):
        if make:
            objs = baker.make(
                Note,
                author=user,
                word=kwargs.get('word', None),
                _quantity=_quantity,
                _fill_optional=True,
            )
        else:
            objs = baker.prepare(
                Note,
                author=user,
                word=kwargs.get('word', None),
                _quantity=_quantity,
                _fill_optional=True,
            )
        if data:
            source = [
                {
                    'text': obj.text,
                }
                for obj in objs
            ]
            expected = [
                {
                    'text': obj.text,
                }
                for obj in objs
            ]
            return (objs, source, expected)
        return objs

    return get_word_notes


@pytest.fixture
def collections(request):
    def get_collections(user, data=False, _quantity=1, make=False, **kwargs):
        if make:
            objs = baker.make(
                Collection, author=user, _quantity=_quantity, _fill_optional=True
            )
        else:
            objs = baker.prepare(
                Collection, author=user, _quantity=_quantity, _fill_optional=True
            )
        if data:
            source = [
                {
                    'title': obj.title,
                    'description': obj.description,
                }
                for obj in objs
            ]
            expected = [
                {
                    'title': obj.title,
                    'description': obj.description,
                }
                for obj in objs
            ]
            return (objs, source, expected)
        return objs

    return get_collections


@pytest.fixture
def related_words_data(request):
    def get_related_words_data(user, data=False, _quantity=1, make=False, **kwargs):
        language = kwargs.get('language', None)
        if not language:
            language = baker.make(Language)
            UserLearningLanguage.objects.create(user=user, language=language)
        if make:
            objs = baker.make(
                Word,
                author=user,
                language=language,
                _quantity=_quantity,
                _fill_optional=True,
            )
        else:
            objs = baker.prepare(
                Word,
                author=user,
                language=language,
                _quantity=_quantity,
                _fill_optional=True,
            )
        if data:
            source = [
                {
                    'from_word': {
                        'language': obj.language.name,
                        'text': obj.text,
                    },
                    'note': 'test_note',
                }
                for obj in objs
            ]
            expected = [
                {
                    'from_word': {
                        'language': obj.language.name,
                        'text': obj.text,
                    },
                    'note': 'test_note',
                }
                for obj in objs
            ]
            return (objs, source, expected)
        return objs

    return get_related_words_data


@pytest.fixture
def word(request):
    def get_word(user, data=False, _quantity=1, make=False, fields={}, **kwargs):
        language = baker.make(Language)
        UserLearningLanguage.objects.create(user=user, language=language)
        if make:
            word = baker.make(
                Word, author=user, language=language, **fields, _fill_optional=True
            )
        else:
            word = baker.prepare(
                Word, author=user, language=language, **fields, _fill_optional=True
            )
        return word

    return get_word
