from django.core.exceptions import ValidationError
from django.utils import timezone


def year_validator(value):
    now = timezone.now()
    if value > now.year:
        raise ValidationError(
            message='Укажите корректный год публикации произведения'
        )
    return value
