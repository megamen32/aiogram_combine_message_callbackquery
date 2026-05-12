from abc import ABC, abstractmethod
from typing import Sequence

from aiogram import Router, types

from .filters import UnifiedFilterBase


class Menu(ABC):
    """Base class for aiogram menu screens shared by messages and callbacks."""

    def __init__(
        self,
        event: types.Message | types.CallbackQuery | None = None,
        filters: Sequence[UnifiedFilterBase] | None = None,
    ):
        self.filters = list(filters or [])

        if event is not None:
            self.set_event(event)

    def set_event(self, event: types.Message | types.CallbackQuery) -> None:
        self.event = event
        self.chat_id = event.from_user.id
        self.message_id = (
            event.message.message_id if isinstance(event, types.CallbackQuery) else None
        )

    @abstractmethod
    async def get_text_and_keyboard(self):
        """Return a tuple of (text, reply_markup)."""
        raise NotImplementedError

    async def handle(self, event: types.Message | types.CallbackQuery | None = None):
        if event is not None:
            self.set_event(event)

        if isinstance(self.event, types.CallbackQuery):
            await self.event.answer()

        text, reply_markup = await self.get_text_and_keyboard()
        await self.answer(text, reply_markup)

    async def answer(self, text, reply_markup, *args, **kwargs):
        if isinstance(self.event, types.Message):
            await self.event.reply(text, reply_markup=reply_markup, *args, **kwargs)
            return

        if isinstance(self.event, types.CallbackQuery):
            await self.event.message.edit_text(
                text,
                reply_markup=reply_markup,
                *args,
                **kwargs,
            )

    def get_event_text(self) -> str:
        """Return message text, message caption, or callback data.

        For commands, the leading slash is removed, so `/start` becomes `start`.
        """
        if isinstance(self.event, types.Message):
            message_text = self.event.text or self.event.caption or ""
            if message_text.startswith("/"):
                message_text = message_text[1:]
            return message_text

        if isinstance(self.event, types.CallbackQuery):
            return self.event.data or ""

        return ""

    def register_handlers(self, router: Router):
        for unified_filter in self.filters:
            router.callback_query.register(self.handle, unified_filter)
            router.message.register(self.handle, unified_filter)

        return self
