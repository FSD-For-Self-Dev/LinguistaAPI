"""Utils to fill instance fields."""


def slug_filler(sender, instance, *args, **kwargs) -> None:
    """
    Fills instance slug field generated from `slugify_func`.
    `slugify_func` and `slugify_fields` class attributes must be set for Model.
    """
    slugify_data = [
        (
            instance.__getattribute__(field[0]).__getattribute__(field[1])
            if type(field) is tuple
            else instance.__getattribute__(field)
        )
        for field in sender.slugify_fields
    ]

    instance.slug = sender.slugify_func(*slugify_data, allow_unicode=True)

    return instance.slug
