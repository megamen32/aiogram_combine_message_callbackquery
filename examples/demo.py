import asyncio
import logging
import os
import random
import time

import aiogram
from aiogram import types, Router

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from src.aiogram_unified import Menu, SmartTextFilter, SmartFilter, RegexFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List
from dataclasses import dataclass


bot=aiogram.Bot(token=os.environ['BOT_TOKEN'])
dp=aiogram.Dispatcher()

@dataclass
class Product:
    name: str
    price: float
    description: str

class ProductMenu(Menu):
    def __init__(self, products: List[Product],event=None, page: int = 1):
        super().__init__(event)
        self.products = products
        self.page = page
        self.items_per_page = 5
        self.filters=[RegexFilter(r'^page_(\d+)$'),SmartTextFilter('start'),SmartTextFilter('products')]

    async def get_text_and_keyboard(self):
        text=self.get_event_text()
        if 'page' in text:
            self.page=int(text.split('page_')[-1])
        start = (self.page - 1) * self.items_per_page
        end = start + self.items_per_page
        page_items = self.products[start:end]

        text_lines = [f"{idx+1}. {item.name} - ${item.price}" for idx, item in enumerate(page_items, start=start)]
        text = "Available Products:\n" + "\n".join(text_lines)

        keyboard_builder = InlineKeyboardBuilder()
        keyboard_builder.max_width=4
        for idx, item in enumerate(page_items, start=start):
            keyboard_builder.button(text=item.name, callback_data=f"product_{idx}")


        # Pagination Buttons
        if self.page > 1:
            keyboard_builder.button(text="Previous", callback_data=f"page_{self.page - 1}")
        if end < len(self.products):
            keyboard_builder.button(text="Next", callback_data=f"page_{self.page + 1}")

        keyboard_builder.button(text="Back", callback_data="start")
        keyboard = keyboard_builder.as_markup()
        return text, keyboard


def __init__(self, event, product: Product):
    super().__init__(event)
    self.product = product


async def get_text_and_keyboard(self):
    text = (
        f"**{self.product.name}**\n"
        f"Price: ${self.product.price}\n"
        f"{self.product.description}"
    )

    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(text="Buy", callback_data=f"buy_{self.product.name}")
    keyboard_builder.button(text="Back to Products", callback_data="products")
    keyboard_builder.button(text="Back to Start", callback_data="start")
    keyboard = keyboard_builder.as_markup()
    return text, keyboard
class ProductDetailMenu(Menu):
    def __init__(self,  products: Product,event=None):
        super().__init__(event)
        self.products = products
        self.filters=[RegexFilter(r'^product_(\d+)$')]

    async def get_text_and_keyboard(self):
        data=self.get_event_text()
        product_index = int(data.split('_')[1])
        self.product = self.products[product_index]
        text = (
            f"**{self.product.name}**\n"
            f"Price: ${self.product.price}\n"
            f"{self.product.description}"
        )

        keyboard_builder = InlineKeyboardBuilder()
        keyboard_builder.button(text="Buy", callback_data=f"buy_{self.product.name}")
        keyboard_builder.button(text="Back to Products", callback_data="products")
        keyboard_builder.button(text="Back to Start", callback_data="start")
        keyboard = keyboard_builder.as_markup()
        return text, keyboard
router = Router()

# Sample product list
products = [
    Product(name=f"Product {i}", price=i*random.uniform(0.5,1.5), description=f"Description of Product {i}.") for i in range(100)
]

menu = ProductMenu(products=products, page=1).register_handlers(router)
menu2=ProductDetailMenu(products=products).register_handlers(router)



@router.callback_query(RegexFilter(r'^buy_(.+)$'))
async def buy_handler(callback: types.CallbackQuery):
    product_name = callback.data.split('_')[1]
    await callback.answer(f"You have bought {product_name}!", show_alert=True)

if __name__ == '__main__':
    dp.include_router(router)
    asyncio.run(dp.start_polling(bot))