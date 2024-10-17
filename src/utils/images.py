"""Utils to do something with images."""

from typing import Any, Type

from io import BytesIO
from PIL import Image
from django.core.files import File


def compress(image: Any) -> Type[File]:
    """Returns compressed image as django-friendly File object."""
    img = Image.open(image)

    # create a BytesIO object
    thumb_io = BytesIO()
    # save image to BytesIO object
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img = img.save(thumb_io, 'JPEG', quality=70, optimize=True)

    # create a django-friendly Files object
    thumbnail = File(thumb_io, name=image.name)

    return thumbnail
