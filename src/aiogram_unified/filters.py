from typing import Callable

from aiogram.filters import BaseFilter
from aiogram import types
import re
from typing import Callable, Pattern
class UnifiedFilterBase(BaseFilter):
    def get_event_text(self, event) -> str:
        if isinstance(event, types.Message):
            message_text = event.text or event.caption or ""
            if message_text.startswith('/'):
                message_text = message_text[1:]
            return message_text
        elif isinstance(event, types.CallbackQuery):
            return event.data or ""
        return ""

    async def __call__(self, event: types.Message | types.CallbackQuery) -> bool:
        raise NotImplementedError


class SmartTextFilter(UnifiedFilterBase):
    def __init__(self, text: str):
        self.text = text.lower()

    async def __call__(self, event: types.Message | types.CallbackQuery) -> bool:
        event_text = self.get_event_text(event).lower()
        return event_text == self.text

class SmartFilter(UnifiedFilterBase):
    def __init__(self, func: Callable[[str], bool]):
        self.func = func

    async def __call__(self, event: types.Message | types.CallbackQuery) -> bool:
        event_text = self.get_event_text(event)
        return self.func(event_text)

class RegexFilter(UnifiedFilterBase):
    def __init__(self, pattern: str | Pattern):
        self.pattern = re.compile(pattern)

    async def __call__(self, event: types.Message | types.CallbackQuery) -> bool:
        event_text = self.get_event_text(event)
        return bool(self.pattern.match(event_text))
