# aiogram-unified

Build one menu flow for both Telegram messages and inline button callbacks in **aiogram 3**.

`aiogram-unified` removes the repetitive glue code that usually appears when the same screen must be opened by a `/command`, a typed message, and a `CallbackQuery`. Instead of writing two handlers for the same logical action, you create a `Menu`, attach unified filters, and let the library route both event types to the same handler.

## Why this exists

Telegram bots often have two parallel navigation paths:

- a user sends `/start`, `products`, `settings`, or another text command;
- a user presses an inline keyboard button with callback data such as `products`, `page_2`, or `settings`.

In plain aiogram, these are different event types and usually require separate handlers. This library gives you a small abstraction for building menu-based bots where the same screen can be opened from both text and callbacks.

Use it when you want:

- one class per screen/menu;
- the same filter logic for `Message` and `CallbackQuery`;
- automatic message reply for text events;
- automatic message editing for callback events;
- simple pagination and nested menu flows;
- less duplicated aiogram handler code.

## Minimal example

```python
from aiogram import Bot, Dispatcher, Router
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram_unified import Menu, SmartTextFilter


class StartMenu(Menu):
    def __init__(self, event=None):
        super().__init__(
            event=event,
            filters=[SmartTextFilter("start")],
        )

    async def get_text_and_keyboard(self):
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Products", callback_data="products")
        keyboard.button(text="Settings", callback_data="settings")

        return "Welcome! Choose an action:", keyboard.as_markup()


router = Router()
StartMenu().register_handlers(router)
```

Now `StartMenu` can be opened by both:

```text
/start
```

and an inline button with:

```text
callback_data="start"
```

## Product menu with pagination

```python
from dataclasses import dataclass
from typing import Sequence

from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram_unified import Menu, RegexFilter, SmartTextFilter


@dataclass
class Product:
    name: str
    price: float
    description: str


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
```

## Product detail screen

```python
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram_unified import Menu, RegexFilter


class ProductDetailMenu(Menu):
    def __init__(self, products, event=None):
        super().__init__(
            event=event,
            filters=[RegexFilter(r"^product_(\d+)$")],
        )
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
```

## Installation

### From PyPI

```bash
pip install aiogram-unified
```

### From source

```bash
git clone https://github.com/your-username/aiogram_combine_message_callbackquery.git
cd aiogram_combine_message_callbackquery
pip install -e .
```

## Full bot example

```python
import asyncio
import os

from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode

from aiogram_unified import RegexFilter

# Import your menu classes here.
# from your_project.menus import ProductMenu, ProductDetailMenu


async def main():
    bot = Bot(token=os.environ["BOT_TOKEN"], parse_mode=ParseMode.HTML)
    dispatcher = Dispatcher()
    router = Router()

    products = [...]  # Build your product list here.

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
```

A runnable version is available in [`examples/demo.py`](examples/demo.py).

## API overview

### `Menu`

Base class for reusable menu screens.

```python
class MyMenu(Menu):
    async def get_text_and_keyboard(self):
        return text, reply_markup
```

Important methods:

- `register_handlers(router)` registers the menu for both `router.message` and `router.callback_query`.
- `handle(event)` stores the current event, answers callback queries, builds content, and sends/edits the Telegram message.
- `answer(text, reply_markup)` replies to a `Message` or edits the original message for a `CallbackQuery`.
- `get_event_text()` returns message text, message caption, or callback data. For message commands, the leading `/` is removed.

### `SmartTextFilter`

Matches exact text or callback data case-insensitively.

```python
SmartTextFilter("start")
```

Matches:

```text
/start
start
callback_data="start"
```

### `SmartFilter`

Accepts a custom predicate that receives normalized event text.

```python
SmartFilter(lambda text: text.startswith("admin_"))
```

### `RegexFilter`

Matches event text or callback data with a regular expression.

```python
RegexFilter(r"^page_(\d+)$")
```

## Project structure

```text
src/aiogram_unified/
├── __init__.py
├── filters.py
└── menu.py

examples/
└── demo.py
```

## Requirements

- Python 3.10+
- aiogram 3.x

## Design notes

This package intentionally stays small. It does not try to replace aiogram routers, scenes, FSM, or middlewares. It only solves one practical problem: keeping menu screens unified when the same action can come from either a text message or an inline callback.

## License

Add your project license here before publishing the package.
