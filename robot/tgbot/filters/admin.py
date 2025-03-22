from aiogram.filters import Filter
from aiogram.types import Message

from core.settings import ADMINS_BOT


class AdminFilter(Filter):
    """Фільтр для перевірки, чи є користувач адміністратором."""

    def __init__(
        self, admins: list[int] | None = ADMINS_BOT, is_admin: bool = True
    ):
        """
        :param admins: Список ID адміністраторів.
        :param is_admin: Визначає, чи користувач має бути адміністратором.
        """
        self.admins = admins or []
        self.is_admin = is_admin

    async def __call__(self, obj: Message) -> bool:
        """Виконує перевірку, чи користувач є адміністратором."""
        if not obj.from_user or not obj.from_user.id:
            return False
        return (obj.from_user.id in self.admins) == self.is_admin
