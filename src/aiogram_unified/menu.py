from abc import ABC, abstractmethod
from typing import List

from aiogram import types, Router
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .filters import UnifiedFilterBase


class Menu(ABC):
    def __init__(self, event: types.Message | types.CallbackQuery=None,filters:List[UnifiedFilterBase]=None):
        if event:
            self.set_event(event)
        self.filters=filters

    def set_event(self, event):
        self.event = event
        self.chat_id = event.from_user.id
        self.message_id = (
            event.message.message_id if isinstance(event, types.CallbackQuery) else None
        )

    @abstractmethod
    async def get_text_and_keyboard(self):
        """Should be overridden to return the text and keyboard markup."""
        pass

    async def handle(self, event=None):
        if event:
            self.set_event(event)

        if isinstance(self.event, types.CallbackQuery):
            await self.event.answer()
        text, reply_markup = await self.get_text_and_keyboard()
        await self.answer(text, reply_markup)

    async def answer(self, text, reply_markup, *args, **kwargs):
        if isinstance(self.event, types.Message):
            await self.event.reply(text, reply_markup=reply_markup, *args, **kwargs)
        elif isinstance(self.event, types.CallbackQuery):
            await self.event.message.edit_text(
                text, reply_markup=reply_markup, *args, **kwargs
            )

    def get_event_text(self) -> str:
        """Extracts text from the event, ignoring leading '/' in commands."""
        if isinstance(self.event, types.Message):
            message_text = self.event.text or self.event.caption or ""
            if message_text.startswith('/'):
                message_text = message_text[1:]
            return message_text
        elif isinstance(self.event, types.CallbackQuery):
            return self.event.data or ""
        return ""


    def register_handlers(self,router:Router):
        for filter in self.filters:
            router.callback_query.register(self.handle,filter)
            router.message.register(self.handle,filter)
        return self
