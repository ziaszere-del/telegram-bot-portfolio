
import os

from dotenv import load_dotenv
from database import create_database, add_order, get_user_orders

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# Каталог товаров
PRODUCTS = {
    "💄 Помада": 3500,
    "🧴 Крем для лица": 5000,
    "✨ Тушь для ресниц": 4200,
    "🤎 Бронзер": 4500,
}


# Главное меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("step", None)

    keyboard = [
        ["🛍 Каталог товаров"],
        ["🛒 Корзина", "📦 Мои заказы"],
        ["ℹ️ О боте"],
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "Привет! Я SmartOrder 👋\n\n"
        "Здесь ты можешь выбрать товары, "
        "добавить их в корзину и оформить заказ.\n\n"
        "Выбери нужное действие:",
        reply_markup=reply_markup
    )


# Показ каталога
async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "🛍 Наш каталог товаров:\n\n"

    for product, price in PRODUCTS.items():
        message += f"{product} — {price} ₸\n"

    keyboard = [[product] for product in PRODUCTS]
    keyboard.append(["🛒 Корзина"])
    keyboard.append(["⬅️ Главное меню"])

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        message,
        reply_markup=reply_markup
    )


# Показ корзины
async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cart = context.user_data.get("cart", {})

    if not cart:
        await update.message.reply_text(
            "🛒 Твоя корзина пока пуста."
        )
        return

    message = "🛒 Твоя корзина:\n\n"
    total = 0

    for product, quantity in cart.items():
        price = PRODUCTS[product]
        subtotal = price * quantity
        total += subtotal

        message += (
            f"{product}\n"
            f"Количество: {quantity}\n"
            f"Стоимость: {subtotal} ₸\n\n"
        )

    message += f"💰 Итого: {total} ₸"

    keyboard = [
        ["🧾 Оформить заказ"],
        ["🧹 Очистить корзину"],
        ["🛍 Каталог товаров"],
        ["⬅️ Главное меню"],
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        message,
        reply_markup=reply_markup
    )


# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.effective_user.id

    # Открытие каталога
    if user_text == "🛍 Каталог товаров":
        context.user_data.pop("step", None)
        await show_catalog(update, context)

    # Просмотр корзины
    elif user_text == "🛒 Корзина":
        context.user_data.pop("step", None)
        await show_cart(update, context)

    # Добавление товара
    elif user_text in PRODUCTS:
        cart = context.user_data.setdefault("cart", {})
        cart[user_text] = cart.get(user_text, 0) + 1

        await update.message.reply_text(
            f"✅ {user_text} добавлен в корзину!\n"
            f"Количество: {cart[user_text]}\n\n"
            "Можешь выбрать ещё товары или открыть корзину."
        )

    # Очистка корзины
    elif user_text == "🧹 Очистить корзину":
        context.user_data["cart"] = {}

        await update.message.reply_text(
            "🧹 Корзина очищена!"
        )

    # Начало оформления заказа
    elif user_text == "🧾 Оформить заказ":
        cart = context.user_data.get("cart", {})

        if not cart:
            await update.message.reply_text(
                "Твоя корзина пуста. Сначала добавь товары."
            )
        else:
            context.user_data["step"] = "name"

            await update.message.reply_text(
                "Для оформления заказа напиши своё имя:"
            )

    # Получение имени
    elif context.user_data.get("step") == "name":
        name = user_text.strip()

        if not name or len(name) > 100:
            await update.message.reply_text(
                "Пожалуйста, введи корректное имя."
            )
            return

        context.user_data["name"] = name
        context.user_data["step"] = "phone"

        await update.message.reply_text(
            "Отлично! Теперь напиши свой номер телефона:"
        )

    # Получение телефона и оформление заказа
    elif context.user_data.get("step") == "phone":
        phone = user_text.strip()

        if len(phone) < 7 or len(phone) > 20:
            await update.message.reply_text(
                "Пожалуйста, проверь номер телефона и введи его ещё раз."
            )
            return

        name = context.user_data["name"]
        cart = context.user_data.get("cart", {})

        total = 0
        products_list = []

        for product, quantity in cart.items():
            price = PRODUCTS[product]
            subtotal = price * quantity
            total += subtotal

            products_list.append(
                f"{product} × {quantity} — {subtotal} ₸"
            )

        product_summary = "\n".join(products_list)

        order_id = add_order(
            user_id,
            name,
            phone,
            product_summary,
            total
        )

        await update.message.reply_text(
            "✅ Заказ успешно оформлен!\n\n"
            f"Номер заказа: №{order_id}\n"
            f"Имя: {name}\n\n"
            f"Товары:\n{product_summary}\n\n"
            f"💰 Общая сумма: {total} ₸\n"
            f"Телефон: {phone}\n\n"
            "Спасибо за заказ!"
        )

        context.user_data.clear()

    # Просмотр заказов
    elif user_text == "📦 Мои заказы":
        context.user_data.pop("step", None)
        user_orders = get_user_orders(user_id)

        if not user_orders:
            await update.message.reply_text(
                "У тебя пока нет заказов."
            )
        else:
            message = "📦 Твои заказы:\n\n"

            for order in user_orders:
                order_id, product, price, created_at = order

                message += (
                    f"Заказ №{order_id}\n"
                    f"Товары:\n{product}\n"
                    f"Общая сумма: {price} ₸\n"
                    f"Дата: {created_at}\n\n"
                )

            await update.message.reply_text(message)

    # Информация о боте
    elif user_text == "ℹ️ О боте":
        context.user_data.pop("step", None)

        await update.message.reply_text(
            "SmartOrder — демонстрационный Telegram-бот "
            "для автоматизации приёма заказов.\n\n"
            "Он помогает клиентам выбирать товары, "
            "собирать корзину и оформлять покупки."
        )

    # Возврат в главное меню
    elif user_text == "⬅️ Главное меню":
        context.user_data.pop("step", None)
        await start(update, context)

    else:
        await update.message.reply_text(
            "Пожалуйста, выбери действие в меню."
        )


# Запуск бота
def main():
    create_database()

    if not TOKEN:
        raise ValueError(
            "Токен не найден! Проверь файл .env"
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("SmartOrder успешно запущен!")

    app.run_polling()


if __name__ == "__main__":
    main()
