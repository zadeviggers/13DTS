from flask import Flask, render_template, redirect, request, session
from flask_bcrypt import Bcrypt
import sqlite3
from contextlib import contextmanager
import os

server = Flask(__name__)
bcrypt = Bcrypt(server)

server.secret_key = os.urandom(69)


def db_dict_factory(cursor, row):
    # Used to return database query results as dictionaries.
    # From the docs: https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.row_factory

    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


@contextmanager
def get_db(*args, **kwds):
    # Custom context manager for getting a database connection,
    # based on the example from the docs https://docs.python.org/3/library/contextlib.html#contextlib.contextmanager
    # This means that the database connection is closed cleanly when it's no longer needed.
    # Example usage:
    # ```
    # with get_db() as (connection, cursor):
    #   cursor.execute("SELECT * FROM Users")
    # ```

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

    # Avoid having to deal with an index error
    if ("username" in session) and ("display_name" in session):
        username = session["username"]
        display_name = session["display_name"]
        admin = session["admin"]

        print(session)

        if username is None or display_name is None or admin is None:
            return False

        return {
            "username": username,
            "display_name": display_name,
            "admin": admin
        }

    return False


def try_create_account() -> bool:
    # Try to create and account log the user in,
    # and return True if it works, or and error string if it doesn't.
    display_name = request.form["display_name"]
    username = request.form["username"]
    password = request.form["password"]

    if not display_name or not username or not password:
        return False

    encrypted_password = bcrypt.generate_password_hash(password)

    with get_db() as (connection, cursor):
        try:
            cursor.execute(
                "SELECT username FROM Users WHERE username=?", [username])
            res = cursor.fetchall()
            if len(res) > 0:
                return "Username already taken"

            cursor.execute(
                "INSERT INTO Users (admin, display_name, username, password) VALUES (0,?,?,?)",
                [display_name, username, encrypted_password])
            connection.commit()
            session['username'] = username
            session['display_name'] = display_name
            session['admin'] = False

            return True
        except Exception as e:
            print(f"Failed to create account: {e}")
            return str(e)


def try_log_in():
    # Try to log the user in, and return True if it works,
    # or and error message if it doesn't.
    username = request.form["username"]
    password = request.form["password"]

    with get_db() as (connection, cursor):
        try:
            cursor.execute(
                "SELECT username, display_name, admin, password FROM Users WHERE username=?", [username])
            res = cursor.fetchall()

            print(res)

            if len(res) == 0:
                return "User not found"

            user = res[0]

            matches = bcrypt.check_password_hash(user["password"], password)

            if not matches:
                return "Password is wrong"

            session['username'] = user["display_name"]
            session['display_name'] = user["username"]
            session['admin'] = user["admin"]
            return True
        except Exception as e:
            print(f"Failed to create account: {e}")
            return str(e)


def log_out():
    # Remove all keys from the user session thingy
    session.pop('username', None)
    session.pop('display_name', None)
    session.pop('admin', None)


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
            query = "SELECT name, description, image_path, price FROM Products WHERE category_id=?"
            cursor.execute(query, [category_id])
        else:
            query = "SELECT name, description, image_path, price FROM Products"
            cursor.execute(query)
        products = cursor.fetchall()

        cursor.execute("SELECT name, id FROM Categories")
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

    result = try_log_in()

    if result == True:
        return redirect("/")

    return render_template("auth.jinja", failed=result)


@server.route("/auth/register", methods=["POST"])
def handle_auth_register():
    if get_user():
        return redirect("/?m=Already%20logged%20in")

    res = try_create_account()

    if res == True:
        return redirect("/?m=Successfully%20logged%20in")

    return render_template("auth.jinja", failed=res)


@server.route("/auth/logout", methods=["GET"])
def handle_auth_log_out():
    if not get_user():
        return render_template("auth.jinja", logged_out=False)

    log_out()

    return render_template("auth.jinja", logged_out=True)


@server.route("/admin", methods=["GET"])
def handle_admin():
    user = get_user()
    if not user or (user["admin"] != True):
        return redirect("/")

    return render_template("admin.jinja", user=user)
