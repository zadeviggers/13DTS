from flask import Flask, render_template
from flask_bcrypt import Bcrypt
import sqlite3
from contextlib import contextmanager

server = Flask(__name__)
bcrypt = Bcrypt(server)


# Used to return databse query results as dictionaries.
# From the docs: https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.row_factory
def db_dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


# Custom context manager for getting a database connection,
# based on the example from the docs https://docs.python.org/3/library/contextlib.html#contextlib.contextmanager
# This means that the database connection is closed cleanly when it's no longer needed.e43
@contextmanager
def get_db(*args, **kwds):
    # Code to acquire resource.
    db_connection = sqlite3.connect("smile.sqlite")
    db_connection.row_factory = db_dict_factory
    db_cursor = db_connection.cursor()
    try:
        yield (db_connection, db_cursor)
    finally:
        # Code to release resource.
        db_connection.close()


@server.route("/")
def home_route():
    return render_template("home.jinja",)


@server.route("/menu")
@server.route("/menu/<category_id>")
def menu_route(category_id=None):
    with get_db() as (connection, cursor):
        if category_id is not None:
            query = """SELECT name, description, image_path, price FROM Products WHERE category_id=?"""
            cursor.execute(query, [category_id])
        else:
            query = """SELECT name, description, image_path, price FROM Products"""
            cursor.execute(query)
        products = cursor.fetchall()

        cursor.execute("""SELECT name, id FROM Categories""")
        categories = cursor.fetchall()

        return render_template("menu.jinja", products=products, current_category_id=category_id, categories=categories)


@server.route("/contact")
def contact_route():
    return render_template("contact.jinja")
