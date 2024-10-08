"""Authentication schema data."""

from rest_framework import status
from rest_framework.serializers import (
    CharField,
)
from drf_spectacular.utils import (
    OpenApiResponse,
    OpenApiExample,
    inline_serializer,
)

from api.v1.vocabulary.serializers import UserDetailsSerializer

from ..schema.utils import (
    get_detail_response,
    get_validation_error_response,
)
from ..schema.responses import (
    unauthorized_response,
    not_found_response,
    user_patch_validation_error_examples,
)


data = {
    'CustomLoginView': {
        'tags': ['authentication'],
        'auth_login': {
            'summary': 'Вход в аккаунт',
            'description': (
                'Передайте в теле запроса e-mail адрес или юзернейм и пароль, чтобы '
                'авторизироваться и получить токен. '
                'Возвращает токен или сообщение об ошибке.'
            ),
            'responses': {
                status.HTTP_200_OK: OpenApiResponse(
                    description='Успешная авторизация',
                    response=inline_serializer(
                        name='token_serializer',
                        fields={
                            'key': CharField(),
                        },
                    ),
                ),
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=[
                        OpenApiExample(
                            name='invalid_credentials',
                            description='Переданы некорректные учётные данные.',
                            value={
                                'non_field_errors': [
                                    'Невозможно войти в систему с указанными учётными данными.'
                                ],
                            },
                        ),
                        OpenApiExample(
                            name='no_login_field',
                            description='Передан только пароль.',
                            value={
                                'non_field_errors': [
                                    'Должно включать либо "username" либо "email" и "password".'
                                ]
                            },
                        ),
                    ]
                ),
            },
        },
        # other methods
    },
    'CustomLogoutView': {
        'auth_logout': {
            'summary': 'Выход из аккаунта',
            'description': (
                'Вызывает Django logout и удаляет токен назначенный текущему пользователю. '
                'Возвращает сообщение об успехе/ошибке.'
            ),
            'responses': {
                status.HTTP_200_OK: get_detail_response(
                    'Успешно вышли.', description='Успешный выход из аккаунта'
                ),
                status.HTTP_401_UNAUTHORIZED: get_detail_response(
                    'Недопустимый токен.', description='Передан некорректный токен'
                ),
            },
        },
        # other methods
    },
    'CustomPasswordResetView': {
        'auth_password_reset': {
            'summary': 'Восстановление пароля',
            'description': (
                'Передайте в теле запроса e-mail адрес, чтобы получить '
                'сообщение с ссылкой на сброс пароля. '
                'Возвращает сообщение об успехе/ошибке.'
            ),
            'responses': {
                status.HTTP_200_OK: get_detail_response(
                    'Письмо с инструкциями по восстановлению пароля выслано.',
                    description='Успешный запрос восстановления пароля',
                ),
            },
        },
        # other methods
    },
    'CustomPasswordResetConfirmView': {
        'auth_password_reset_confirm': {
            'summary': 'Подтверждение восстановления пароля',
            'description': (
                'Ссылка для сброса пароля по электронной почте. '
                'Принимает в теле запроса token, uid, new_password1, new_password2. '
                'Возвращает сообщение об успехе/ошибке.'
            ),
            'responses': {
                status.HTTP_200_OK: get_detail_response(
                    'Пароль изменён на новый.',
                    description='Успешное восстановление пароля',
                ),
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=[
                        OpenApiExample(
                            name='invalid_data',
                            description='Переданы некорректные токены.',
                            value={
                                'non_field_errors': [
                                    'Значение “string” не является верным UUID-ом.'
                                ],
                            },
                        ),
                        OpenApiExample(
                            name='invalid_password',
                            description='Ошибка валидации пароля.',
                            value={
                                'new_password2': [
                                    'Введённый пароль слишком короткий. Он должен содержать как минимум 8 символов.'
                                ]
                            },
                        ),
                        OpenApiExample(
                            name='password_mismatch',
                            description='Переданы разные пароли.',
                            value={'new_password2': ['Введенные пароли не совпадают.']},
                        ),
                    ]
                ),
            },
        },
        # other methods
    },
    'CustomPasswordChangeView': {
        'auth_password_change': {
            'summary': 'Изменение пароля',
            'description': (
                'Передайте в теле запроса новый пароль в полях new_password1 и new_password2, '
                'чтобы изменить текущий пароль. '
                'Возвращает сообщение об успехе/ошибке.'
                'Требуется авторизация. '
            ),
            'responses': {
                status.HTTP_200_OK: get_detail_response(
                    'Новый пароль сохранён.', description='Успешная смена пароля'
                ),
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=[
                        OpenApiExample(
                            name='invalid_password',
                            description='Ошибка валидации пароля.',
                            value={
                                'new_password2': [
                                    'Введённый пароль слишком короткий. Он должен содержать как минимум 8 символов.'
                                ]
                            },
                        ),
                        OpenApiExample(
                            name='password_mismatch',
                            description='Переданы разные пароли.',
                            value={'new_password2': ['Введенные пароли не совпадают.']},
                        ),
                    ]
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        # other methods
    },
    'CustomRegisterView': {
        'auth_registration': {
            'summary': 'Регистрация',
            'description': (
                'Передайте в теле необходимые данные, чтобы создать пользователя. '
                'Возвращает сообщение об успехе/ошибке.'
            ),
            'responses': {
                status.HTTP_200_OK: get_detail_response(
                    'Письмо с подтверждением выслано.',
                    description='Успешная регистрация с подтверждением через email',
                ),
                status.HTTP_204_NO_CONTENT: OpenApiResponse(
                    description='Успешная регистрация без подтверждения через email',
                    response=None,
                ),
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=[
                        OpenApiExample(
                            name='invalid_data',
                            description='Примеры ответов невалидных полей.',
                            value={
                                'username': [
                                    'Пользователь с таким именем уже существует.'
                                ],
                                'email': [
                                    'Введите правильный адрес электронной почты.'
                                ],
                                'password1': [
                                    'Введённый пароль слишком короткий. Он должен содержать как минимум 8 символов.',
                                    'Введённый пароль слишком широко распространён.',
                                    'Введённый пароль состоит только из цифр.',
                                ],
                            },
                        ),
                    ]
                ),
            },
        },
        # other methods
    },
    'CustomVerifyEmailView': {
        'auth_registration_verify_email': {
            'summary': 'Подтверждение e-mail адреса',
            'description': (
                'Передайте в теле запроса ключ подтверждения, чтобы подтвердить '
                'свой e-mail адрес. '
                'Возвращает сообщение об успехе/ошибке.'
            ),
            'responses': {
                status.HTTP_200_OK: get_detail_response(
                    'ок', description='Адрес почты подтвержден.'
                ),
                status.HTTP_404_NOT_FOUND: not_found_response,
            },
        },
        # other methods
    },
    'CustomResendEmailVerificationView': {
        'auth_registration_resend_email': {
            'summary': 'Повторная отправка сообщения с подтверждением e-mail адреса',
            'description': (
                'Передайте в теле запроса e-mail адрес, чтобы повторно получить '
                'сообщение с подтверждением. '
                'Возвращает сообщение об успехе/ошибке.'
            ),
            'responses': {
                status.HTTP_200_OK: get_detail_response(
                    'ок', description='Сообщение отправлено.'
                ),
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=[
                        OpenApiExample(
                            name='invalid_email',
                            description='Введён некорректный адрес почты.',
                            value={
                                'email': ['Введите правильный адрес электронной почты.']
                            },
                        ),
                    ]
                ),
            },
        },
        # other methods
    },
    'UserDetailsWithDestroyView': {
        'tags': ['user_profile'],
        'user_retrieve': {
            'summary': 'Просмотр профиля пользователя',
            'description': (
                'Возвращает данные текущего пользователя.\n ' 'Требуется авторизация.'
            ),
            'responses': {
                status.HTTP_200_OK: UserDetailsSerializer,
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'user_update': {
            'summary': 'Редактирование профиля пользователя',
            'description': (
                'Обновляет все данные текущего пользователя.\n '
                'Требуется авторизация.'
            ),
            'request': UserDetailsSerializer,
            'responses': {
                status.HTTP_200_OK: UserDetailsSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=user_patch_validation_error_examples
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'user_partial_update': {
            'summary': 'Редактирование профиля пользователя',
            'description': (
                'Обновляет переданные данные пользователя.\n ' 'Требуется авторизация.'
            ),
            'request': UserDetailsSerializer,
            'responses': {
                status.HTTP_200_OK: UserDetailsSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=user_patch_validation_error_examples
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'user_destroy': {
            'summary': 'Удаление аккаунта пользователя',
            'description': (
                'Удаляет аккаунт текущего пользователя без возможности '
                'восстановления.\n '
                'Требуется авторизация.'
            ),
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: None,
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        # other methods
    },
}
