import re
from typing import Callable, Pattern

from aiogram import types
from aiogram.filters import BaseFilter


class UnifiedFilterBase(BaseFilter):
    """Base filter that normalizes Message and CallbackQuery text access."""

    def get_event_text(self, event: types.Message | types.CallbackQuery) -> str:
        if isinstance(event, types.Message):
            message_text = event.text or event.caption or ""
            if message_text.startswith("/"):
                message_text = message_text[1:]
            return message_text

        if isinstance(event, types.CallbackQuery):
            return event.data or ""

        return ""

    async def __call__(self, event: types.Message | types.CallbackQuery) -> bool:
        raise NotImplementedError


class SmartTextFilter(UnifiedFilterBase):
    """Match exact message text, command text, or callback data."""

    def __init__(self, text: str):
        self.text = text.lower()

    async def __call__(self, event: types.Message | types.CallbackQuery) -> bool:
        event_text = self.get_event_text(event).lower()
        return event_text == self.text


class SmartFilter(UnifiedFilterBase):
    """Run a custom predicate against normalized event text."""

    def __init__(self, func: Callable[[str], bool]):
        self.func = func

    async def __call__(self, event: types.Message | types.CallbackQuery) -> bool:
        event_text = self.get_event_text(event)
        return self.func(event_text)


class RegexFilter(UnifiedFilterBase):
    """Match normalized event text with a regular expression."""

    def __init__(self, pattern: str | Pattern[str]):
        self.pattern = re.compile(pattern)

    async def __call__(self, event: types.Message | types.CallbackQuery) -> bool:
        event_text = self.get_event_text(event)
        return bool(self.pattern.match(event_text))
