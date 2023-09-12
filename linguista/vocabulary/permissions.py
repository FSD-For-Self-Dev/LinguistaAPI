from rest_framework.permissions import BasePermission


class CanAddDefinitionPermission(BasePermission):
    message = 'You can add no more than 10 definitions to a word'

    def has_permission(self, request, view):
        word = view.get_object()
        if request.method == 'POST':
            return word.definitions.count() < 10
        return True
