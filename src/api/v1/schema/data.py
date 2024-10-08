"""API schema core data."""

from ..auth.schema import data as authentication_data
from ..exercises.schema import data as exercises_data
from ..languages.schema import data as languages_data
from ..users.schema import data as users_data
from ..vocabulary.schema import data as vocabulary_data


default_data = {
    'default': {
        'tags': ['default'],
    },
}

data = (
    default_data
    | authentication_data
    | exercises_data
    | languages_data
    | users_data
    | vocabulary_data
)
