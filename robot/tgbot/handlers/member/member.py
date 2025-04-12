from aiogram import Router, F, types, Bot

from robot.tgbot.handlers.member.start import member_router
from robot.tgbot.filters.member import ClubMemberFilter


member_router.message.filter(ClubMemberFilter())



