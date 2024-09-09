"""API schema generator."""

import logging

from rest_framework.serializers import Serializer
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiExample,
)


from .data import data


logger = logging.getLogger(__name__)


class FromDataSchema(AutoSchema):
    """Custom schema generator to generate schema from common data dictionary."""

    def get_tags(self) -> list[str]:
        try:
            return data[self.view.__class__.__name__]['tags']
        except Exception:
            return data['default']['tags']

    def get_description(self) -> str | None:
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()][
                'description'
            ]
        except Exception:
            return super().get_description()

    def get_summary(self) -> str | None:
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()][
                'summary'
            ]
        except Exception:
            logger.warning(
                f'Информация об операции отсутствует в данных схемы (не передан `summary`) '
                f'[{self.view.__class__.__name__}: {self.get_operation_id().lower()}]'
            )
            return super().get_summary()

    def get_request_serializer(self) -> Serializer | None:
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()][
                'request'
            ]
        except Exception:
            return super().get_request_serializer()

    def get_response_serializers(self) -> dict[int, OpenApiResponse]:
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()][
                'responses'
            ]
        except Exception:
            return super().get_response_serializers()

    def get_examples(self) -> list[OpenApiExample]:
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()][
                'examples'
            ]
        except Exception:
            return super().get_examples()

    def get_override_parameters(self) -> list[OpenApiParameter]:
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()][
                'parameters'
            ]
        except Exception:
            return super().get_override_parameters()
