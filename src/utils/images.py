"""Utils to do something with images."""

from typing import Type

from io import BytesIO
from PIL import Image
from django.core.files import File
from django.core.files.base import ContentFile


def compress(image: File) -> Type[File]:
    """Returns compressed image as django-friendly File object."""
    img = Image.open(image)

    img.resize((200, 300), Image.Resampling.LANCZOS)

    # create a BytesIO object
    img_bytes = BytesIO()

    # save image to BytesIO object
    if img.mode != 'RGB':
        img = img.convert('RGB')

    img.save(fp=img_bytes, format='JPEG', quality=25, optimize=True)
    image_content_file = ContentFile(content=img_bytes.getvalue())
    name = image.name.split('.')[0] + '.jpg'

    # create a django-friendly Files object
    thumbnail = File(image_content_file, name=name)

    return thumbnail
