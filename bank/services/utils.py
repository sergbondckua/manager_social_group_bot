import time

import monobank


def retry_on_many_requests(retries: int = 3, delay: int = 3):
    """
    Декоратор для повторного виклику функції у разі помилки.
        :param retries: Кількість спроб
        :param delay: Затримка між спробами
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except monobank.TooManyRequests:
                    if attempt < retries - 1:
                        time.sleep(delay)
                        continue
                    raise

        return wrapper

    return decorator
