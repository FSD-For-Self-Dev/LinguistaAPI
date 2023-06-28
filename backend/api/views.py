from django.contrib.auth import get_user_model

# from djoser.views import UserViewSet
from rest_framework import viewsets  # filters, status
# from rest_framework.decorators import action
# from rest_framework.exceptions import ValidationError
# from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
# from rest_framework.response import Response

from words.models import Word

from .serializers import WordSerializer

User = get_user_model()


class WordViewSet(viewsets.ModelViewSet):
    queryset = Word.objects.all()
    serializer_class = WordSerializer
    http_method_names = ['get', 'post', 'head', 'patch', 'delete']
    permission_classes = [
        # IsAuthorOrReadOnly,
        AllowAny,
    ]
    # pagination_class = CursorSetPagination
    # filter_backends = (RQLFilterBackend, filters.OrderingFilter)
    # rql_filter_class = RecipeFilters
    # ordering_fields = ['created']
    # ordering = ('-created',)
    # filter_backends = [
    #     filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend
    # ]
    # filterset_class = RecipeFilter

    # @action(methods=['get'], detail=False)
    # def random(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     recipe = random.choice(queryset)
    #     serializer = RecipeListSerializer(
    #         recipe, context={'request': request}
    #     )
    #     return Response(serializer.data, status=status.HTTP_200_OK)

    # @action(methods=['get'], detail=True)
    # def ingredients(self, request, *args, **kwargs):
    #     recipe = get_object_or_404(Recipe, pk=kwargs.get('pk'))
    #     ingredients = recipe.ingredients_info.all()
    #     serializer = RecipeIngredientReprSerializer(
    #         ingredients, many=True, context={'request': request}
    #     )
    #     return Response(serializer.data, status=status.HTTP_200_OK)
