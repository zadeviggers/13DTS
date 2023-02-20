from flask import Flask, render_template
import sqlite3


server = Flask(__name__)


def get_db():
    db_connection = sqlite3.connect("smile.sqlite")
    db_cursor = db_connection.cursor()

    return db_connection, db_cursor


@server.route("/")
def home_route():
    return render_template("home.jinja",)


@server.route("/menu")
def menu_route():
    connection, cursor = get_db()

    result = cursor.execute(
        """SELECT name, description, image_path, price FROM Products""")
    raw_products = result.fetchall()
    products = []
    for p in raw_products:
        name, description, image_path, price = p
        products.append({
            "name": name,
            "description": description,
            "image_path": image_path,
            "price": price
        })

    return render_template("menu.jinja", products=products)


@server.route("/contact")
def contact_route():
    return render_template("contact.jinja")
