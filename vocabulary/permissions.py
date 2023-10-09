from rest_framework.permissions import BasePermission

from core.constants import MAX_DEFINITIONS_AMOUNT, MAX_USAGE_EXAMPLES_AMOUNT


class CanAddDefinitionPermission(BasePermission):
    message = (
        f'You can add no more than '
        f'{MAX_DEFINITIONS_AMOUNT} definitions to a word'
    )

    def has_permission(self, request, view):
        word = view.get_object()
        if request.method == 'POST':
            return word.definitions.count() < MAX_DEFINITIONS_AMOUNT
        return True


class CanAddUsageExamplePermission(BasePermission):
    message = (
        f'You can add no more than '
        f'{MAX_USAGE_EXAMPLES_AMOUNT} usage examples to a word'
    )

    def has_permission(self, request, view):
        word = view.get_object()
        if request.method == 'POST':
            return word.examples.count() < MAX_USAGE_EXAMPLES_AMOUNT
        return True
