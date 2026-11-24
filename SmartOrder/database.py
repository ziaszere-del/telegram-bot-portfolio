
import sqlite3

DB_NAME = "orders.db"


def create_database():
    """Создаёт таблицу заказов, если её ещё нет."""
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            product TEXT NOT NULL,
            price INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


def add_order(user_id, customer_name, phone, product, price):
    """Сохраняет новый заказ."""
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO orders (
            user_id, customer_name, phone, product, price
        )
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, customer_name, phone, product, price))

    connection.commit()
    order_id = cursor.lastrowid
    connection.close()

    return order_id


def get_user_orders(user_id):
    """Возвращает заказы конкретного пользователя."""
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, product, price, created_at
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))

    orders = cursor.fetchall()
    connection.close()

    return orders
