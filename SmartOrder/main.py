
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
    context.user_data.clear()

    keyboard = [
        ["🛍 Каталог товаров"],
        ["📦 Мои заказы", "ℹ️ О боте"],
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "Привет! Я SmartOrder 👋\n\n"
        "Здесь ты можешь посмотреть товары "
        "и оформить заказ.\n\n"
        "Выбери нужное действие:",
        reply_markup=reply_markup
    )


# Показ каталога
async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "🛍 Наш каталог товаров:\n\n"

    for product, price in PRODUCTS.items():
        message += f"{product} — {price} ₸\n"

    keyboard = [[product] for product in PRODUCTS]
    keyboard.append(["⬅️ Главное меню"])

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
        context.user_data.clear()
        await show_catalog(update, context)

    # Выбор товара
    elif user_text in PRODUCTS:
        context.user_data["product"] = user_text
        context.user_data["price"] = PRODUCTS[user_text]
        context.user_data["step"] = "name"

        await update.message.reply_text(
            f"Ты выбрала: {user_text}\n"
            f"Цена: {PRODUCTS[user_text]} ₸\n\n"
            "Как тебя зовут?"
        )

    # Получение имени
    elif context.user_data.get("step") == "name":
        context.user_data["name"] = user_text
        context.user_data["step"] = "phone"

        await update.message.reply_text(
            "Отлично! Теперь напиши свой номер телефона:"
        )

    # Получение телефона и оформление заказа
    elif context.user_data.get("step") == "phone":
        name = context.user_data["name"]
        product = context.user_data["product"]
        price = context.user_data["price"]
        phone = user_text

        order_id = add_order(
            user_id,
            name,
            phone,
            product,
            price
        )

        await update.message.reply_text(
            "✅ Заказ оформлен!\n\n"
            f"Имя: {name}\n"
            f"Товар: {product}\n"
            f"Цена: {price} ₸\n"
            f"Телефон: {phone}\n\n"
            "Спасибо за заказ!"
        )

        context.user_data.clear()

    # Просмотр заказов
    elif user_text == "📦 Мои заказы":
        context.user_data.clear()
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
                    f"Товар: {product}\n"
                    f"Цена: {price} ₸\n"
                    f"Дата: {created_at}\n\n"
                )

            await update.message.reply_text(message)

    # Информация о боте
    elif user_text == "ℹ️ О боте":
        context.user_data.clear()

        await update.message.reply_text(
            "SmartOrder — демонстрационный Telegram-бот "
            "для автоматизации приёма заказов.\n\n"
            "Он помогает клиентам выбирать товары "
            "и оформлять покупки."
        )

    # Возврат в главное меню
    elif user_text == "⬅️ Главное меню":
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
