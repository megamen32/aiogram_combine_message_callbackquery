import asyncio
import os
import random
from dataclasses import dataclass
from typing import Sequence

from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram_unified import Menu, RegexFilter, SmartTextFilter


@dataclass
class Product:
    name: str
    price: float
    description: str


class StartMenu(Menu):
    def __init__(self, event=None):
        super().__init__(event=event, filters=[SmartTextFilter("start")])

    async def get_text_and_keyboard(self):
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Products", callback_data="products")
        keyboard.adjust(1)

        return "Welcome! Choose an action:", keyboard.as_markup()


class ProductMenu(Menu):
    def __init__(self, products: Sequence[Product], event=None, page: int = 1):
        super().__init__(
            event=event,
            filters=[
                SmartTextFilter("products"),
                RegexFilter(r"^page_(\d+)$"),
            ],
        )
        self.products = products
        self.page = page
        self.items_per_page = 5

    async def get_text_and_keyboard(self):
        event_text = self.get_event_text()

        if event_text.startswith("page_"):
            self.page = int(event_text.split("_", maxsplit=1)[1])

        start = (self.page - 1) * self.items_per_page
        end = start + self.items_per_page
        page_items = self.products[start:end]

        lines = [
            f"{index + 1}. {product.name} — ${product.price:.2f}"
            for index, product in enumerate(page_items, start=start)
        ]

        keyboard = InlineKeyboardBuilder()
        for index, product in enumerate(page_items, start=start):
            keyboard.button(text=product.name, callback_data=f"product_{index}")

        if self.page > 1:
            keyboard.button(text="Previous", callback_data=f"page_{self.page - 1}")

        if end < len(self.products):
            keyboard.button(text="Next", callback_data=f"page_{self.page + 1}")

        keyboard.button(text="Back", callback_data="start")
        keyboard.adjust(1)

        return "Available products:\n" + "\n".join(lines), keyboard.as_markup()


class ProductDetailMenu(Menu):
    def __init__(self, products: Sequence[Product], event=None):
        super().__init__(event=event, filters=[RegexFilter(r"^product_(\d+)$")])
        self.products = products

    async def get_text_and_keyboard(self):
        product_index = int(self.get_event_text().split("_", maxsplit=1)[1])
        product = self.products[product_index]

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Buy", callback_data=f"buy_{product.name}")
        keyboard.button(text="Back to Products", callback_data="products")
        keyboard.button(text="Back to Start", callback_data="start")
        keyboard.adjust(1)

        text = (
            f"<b>{product.name}</b>\n"
            f"Price: ${product.price:.2f}\n\n"
            f"{product.description}"
        )

        return text, keyboard.as_markup()


def build_products(count: int = 30) -> list[Product]:
    return [
        Product(
            name=f"Product {index}",
            price=index * random.uniform(0.5, 1.5),
            description=f"Description of Product {index}.",
        )
        for index in range(1, count + 1)
    ]


async def main():
    bot = Bot(token=os.environ["BOT_TOKEN"], parse_mode=ParseMode.HTML)
    dispatcher = Dispatcher()
    router = Router()

    products = build_products()

    StartMenu().register_handlers(router)
    ProductMenu(products).register_handlers(router)
    ProductDetailMenu(products).register_handlers(router)

    @router.callback_query(RegexFilter(r"^buy_(.+)$"))
    async def buy_handler(callback: types.CallbackQuery):
        product_name = callback.data.split("_", maxsplit=1)[1]
        await callback.answer(f"You have bought {product_name}!", show_alert=True)

    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
