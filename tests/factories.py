from django.contrib.auth import get_user_model

import factory

from vocabulary.models import (Collection, Tag, Translation, UsageExample,
                               Word, WordCollection)

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        # django_get_or_create = ('email',)
    email = factory.faker.Faker('email')
    username = factory.faker.Faker('name')


class WordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Word
        django_get_or_create = ('text',)

    text = factory.faker.Faker('word')
    author = factory.SubFactory(UserFactory)
    language = factory.faker.Faker('language_code')

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tag in extracted:
                self.tags.add(tag)

    @factory.post_generation
    def collections(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for collection in extracted:
                WordCollection.objects.create(
                    word=self, collection=collection
                )


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag
        django_get_or_create = ('name',)

    name = factory.faker.Faker('word')
    author = factory.SubFactory(UserFactory)


class CollectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Collection

    title = factory.faker.Faker('text', max_nb_chars=20)
    author = factory.SubFactory(UserFactory)


class TranslationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Translation

    word = factory.SubFactory(WordFactory)


class ExampleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UsageExample

    word = factory.SubFactory(WordFactory)
