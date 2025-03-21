from django.core.validators import URLValidator, ValidationError
from django.utils.deconstruct import deconstructible
import re

@deconstructible
class CustomURLValidator:
    def __init__(self):
        # Регулярний вираз для tg://
        self.tg_pattern = re.compile(r'^tg://\S+')
        # Стандартний валідатор URL (можна розширити списком схем)
        self.url_validator = URLValidator(schemes=['http', 'https', 'ftp', 'ftps', 'tel', 'mailto'])

    def __call__(self, value):
        # Перевірка для tg://
        if value.startswith('tg://'):
            if not self.tg_pattern.match(value):
                raise ValidationError(
                    "Неправильний формат посилання Telegram. Приклад: tg://resolve?domain=example",
                    code="invalid_tg_url"
                )
        # Перевірка для стандартних URL
        else:
            try:
                self.url_validator(value)
            except ValidationError:
                raise ValidationError(
                    "Невірний URL. Приклад: https://example.com або mailto:user@example.com",
                    code="invalid_generic_url"
                )