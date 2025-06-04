import re

from django.core.exceptions import ValidationError


def validate_no_spaces_and_alnum(value):
    if not re.match(r"^[A-Za-z0-9]+$", value):
        raise ValidationError(
            f"'{value}' має містити тільки літери та цифри без пробілів.",
            params={"value": value},
        )
