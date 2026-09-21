from aiogram import Router
from bot.handlers.admin import router as admin_router
from bot.handlers.common import router as common_router
from bot.handlers.student import router as student_router

main_router = Router()
main_router.include_router(common_router)
main_router.include_router(admin_router)
main_router.include_router(student_router)
