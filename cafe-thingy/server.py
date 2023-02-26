from flask import Flask, render_template, redirect
from flask_bcrypt import Bcrypt
import sqlite3
from contextlib import contextmanager

server = Flask(__name__)
bcrypt = Bcrypt(server)


# Used to return database query results as dictionaries.
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


def get_user():
    # Return the current user session,
    # or return False if there is none.
    return False


def try_create_account() -> bool:
    # Try to create and account log the user in,
    # and return True if it works, or False if it doesn't.
    return False


def try_log_in() -> bool:
    # Try to log the user in, and return True if it works,
    # or False if it doesn't.
    return False


def try_log_out() -> bool:
    # Try to log the user out, and return True if it works,
    # or False if it doesn't.
    return False


@server.route("/", methods=["GET"])
def handle_home():
    user = get_user()

    return render_template("home.jinja", user=user)


@server.route("/contact", methods=["GET"])
def handle_contact():
    user = get_user()

    return render_template("contact.jinja", user=user)


@server.route("/menu", methods=["GET"])
@server.route("/menu/<category_id>", methods=["GET"])
def handle_menu(category_id=None):
    user = get_user()
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

        return render_template("menu.jinja", user=user, products=products, current_category_id=category_id, categories=categories)


@server.route("/auth", methods=["GET"])
def handle_auth():
    if get_user():
        return redirect("/")

    return render_template("auth.jinja")


@server.route("/auth/login", methods=["POST"])
def handle_auth_log_in():
    if get_user():
        return redirect("/?m=Already%20logged%20in")

    success = try_log_in()

    if success:
        return redirect("/")

    return render_template("auth.jinja", failed="log in")


@server.route("/auth/register", methods=["POST"])
def handle_auth_register():
    if get_user():
        return redirect("/?m=Already%20logged%20in")

    success = try_create_account()

    if success:
        return redirect("/?m=Successfully%20logged%20in")

    return render_template("auth.jinja", failed="register")


@server.route("/auth/logout", methods=["GET"])
def handle_auth_log_out():
    if not get_user():
        return redirect("/auth")

    success = try_log_out()

    return render_template("auth.jinja", logged_out=success)
