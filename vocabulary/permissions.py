from rest_framework import permissions
from rest_framework.permissions import BasePermission

from core.constants import MAX_DEFINITIONS_AMOUNT, MAX_USAGE_EXAMPLES_AMOUNT


class CanAddDefinitionPermission(BasePermission):
    message = f'You can add no more than {MAX_DEFINITIONS_AMOUNT} definitions to a word'

    def has_permission(self, request, view):
        word = view.get_object()
        if request.method == 'POST':
            return word.definitions.count() < MAX_DEFINITIONS_AMOUNT
        return True


class CanAddUsageExamplePermission(BasePermission):
    message = f'You can add no more than {MAX_USAGE_EXAMPLES_AMOUNT} usage examples to a word'

    def has_permission(self, request, view):
        word = view.get_object()
        if request.method == 'POST':
            return word.examples.count() < MAX_USAGE_EXAMPLES_AMOUNT
        return True


class IsAuthorOrReadOnly(permissions.BasePermission):
    message = f'Only author has permission to perform this action'

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)
