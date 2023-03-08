from functools import wraps
from flask import Flask, render_template, redirect, request, session, g
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


def admin_only(func):
    # A custom decorator to make pages require the user to be logged in as an admin
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not g.user:
            return redirect("/auth?m=You+are+not+logged+in")
        if (g.user["admin"] != True):
            return redirect("/?m=You+are+not+an+admin")
        return func(*args, **kwargs)
    return wrapper


@server.before_request
def load_user():
    # This function runs before the request handler on each request.
    # Docs: https://flask.palletsprojects.com/en/2.2.x/api/#flask.Flask.before_request

    # Get the user and stick it ona globally available object
    # Docs: https://flask.palletsprojects.com/en/2.2.x/api/?highlight=g#flask.g
    user = get_user()
    g.user = user


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
    return render_template("home.jinja", user=g.user)


@server.route("/contact", methods=["GET"])
def handle_contact():
    return render_template("contact.jinja", user=g.user)


@server.route("/menu", methods=["GET"])
@server.route("/menu/<category_id>", methods=["GET"])
def handle_menu(category_id=None):
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

        return render_template("menu.jinja", user=g.user, products=products, current_category_id=category_id, categories=categories)


@server.route("/auth", methods=["GET"])
def handle_auth():
    if g.user:
        return redirect("/")

    return render_template("auth.jinja")


@server.route("/auth/login", methods=["POST"])
def handle_auth_log_in():
    if g.user:
        return redirect("/?m=Already%20logged%20in")

    result = try_log_in()

    if result == True:
        return redirect("/")

    return render_template("auth.jinja", failed=result)


@server.route("/auth/register", methods=["POST"])
def handle_auth_register():
    if g.user:
        return redirect("/?m=Already+logged+in")

    res = try_create_account()

    if res == True:
        return redirect("/?m=Successfully+logged+in")

    return render_template("auth.jinja", failed=res)


@server.route("/auth/logout", methods=["GET"])
def handle_auth_log_out():
    if not g.user:
        return render_template("auth.jinja", logged_out=False)

    log_out()

    return render_template("auth.jinja", logged_out=True)


@server.route("/admin", methods=["GET"])
@admin_only
def handle_admin():
    return render_template("admin/admin.jinja", user=g.user)


@server.route("/admin/categories", methods=["GET"])
@admin_only
def handle_admin_categories():
    with get_db() as (connection, cursor):
        cursor.execute("SELECT id, name FROM Categories")
        categories = cursor.fetchall()
        return render_template("admin/categories.jinja", user=g.user, categories=categories)


@server.route("/admin/create-category", methods=["GET", "POST"])
@admin_only
def handle_admin_create_category():
    if request.method == "GET":
        return render_template("admin/create-category.jinja", user=g.user)
    elif request.method == "POST":
        with get_db() as (connection, cursor):
            name = request.form["name"]
            create_query = "INSERT INTO Categories (name) VALUES (?)"
            cursor.execute(create_query, [name])
            # This is a special SQLite function that gives the ID of the last inserted row
            id_query = "SELECT last_insert_rowid()"
            cursor.execute(id_query)
            connection.commit()
            # Get the returned category ID out
            category_id = list(cursor.fetchone().values())[0]
            return redirect(f"/admin/categories/{category_id}")


@server.route("/admin/categories/<category_id>", methods=["GET"])
@admin_only
def handle_admin_category_info(category_id=None):
    if not category_id:
        return redirect("/admin/categories")

    with get_db() as (connection, cursor):
        category_query = "SELECT id, name FROM Categories WHERE id=?"
        cursor.execute(category_query, [category_id])
        category_res = cursor.fetchone()

        products_query = "SELECT id, name FROM Products WHERE category_id=?"
        cursor.execute(products_query, [category_id])
        products_res = cursor.fetchall()

        return render_template("admin/category-info.jinja", user=g.user, category=category_res, products=products_res)


@server.route("/admin/categories/<category_id>/delete", methods=["GET"])
@admin_only
def handle_admin_delete_category(category_id=None):
    if not category_id:
        return redirect("/admin/categories")

    with get_db() as (connection, cursor):
        try:
            product_query = "DELETE FROM Categories WHERE id=?"
            cursor.execute(product_query, [category_id])
            connection.commit()
            return redirect(f"/admin/categories?m=Successfully+deleted+category+{category_id}")
        except Exception as e:
            print(e)
            return redirect(f"/admin/categories/{category_id}?m=Failed+to+delete+category")


@server.route("/admin/categories/<category_id>/update", methods=["POST"])
@admin_only
def handle_admin_update_category(category_id=None):
    if not category_id:
        return redirect("/admin/categories")

    with get_db() as (connection, cursor):
        try:
            product_query = "UPDATE Categories SET name=?  WHERE id=?"
            cursor.execute(product_query, [
                           request.form["name"], category_id])
            connection.commit()
            return redirect(f"/admin/categories/{category_id}?m=Successfully+updated+category+{category_id}")
        except Exception as e:
            print(e)
            return redirect(f"/admin/categories/{category_id}?m=Failed+to+update+category")


@server.route("/admin/products", methods=["GET"])
@admin_only
def handle_admin_products():
    with get_db() as (connection, cursor):
        query = "SELECT id, name FROM Products"
        cursor.execute(query)
        res = cursor.fetchall()

        return render_template("admin/products.jinja", user=g.user, products=res)


@server.route("/admin/products/<product_id>", methods=["GET"])
@admin_only
def handle_admin_product_info(product_id=None):
    if not product_id:
        return redirect("/admin/products")

    with get_db() as (connection, cursor):
        product_query = "SELECT id, name, description, image_path, price, category_id FROM Products WHERE id=?"
        cursor.execute(product_query, [product_id])
        product_res = cursor.fetchone()

        category_query = "SELECT id, name FROM Categories WHERE id=?"
        cursor.execute(category_query, [product_res["category_id"]])
        category_res = cursor.fetchone()

        categories_query = "SELECT id, name FROM Categories"
        cursor.execute(categories_query)
        categories_res = cursor.fetchall()

        return render_template("admin/product-info.jinja", user=g.user, product=product_res, product_category=category_res, categories=categories_res)


@server.route("/admin/products/<product_id>/delete", methods=["GET"])
@admin_only
def handle_admin_delete_product(product_id=None):
    if not product_id:
        return redirect("/admin/products")

    with get_db() as (connection, cursor):
        try:
            product_query = "DELETE FROM Products WHERE id=?"
            cursor.execute(product_query, [product_id])
            connection.commit()
            return redirect(f"/admin/products?m=Successfully+deleted+product+{product_id}")
        except Exception as e:
            print(e)
            return redirect(f"/admin/products/{product_id}?m=Failed+to+delete+product")


@server.route("/admin/products/<product_id>/update", methods=["POST"])
@admin_only
def handle_admin_update_product(product_id=None):
    if not product_id:
        return redirect("/admin/products")

    with get_db() as (connection, cursor):
        try:
            product_query = "UPDATE Products SET name=?, description=?, price=?, category_id=?  WHERE id=?"
            cursor.execute(product_query, [
                           request.form["name"], request.form["description"], request.form["price"], request.form["category"], product_id])
            connection.commit()
            return redirect(f"/admin/products/{product_id}?m=Successfully+updated+product+{product_id}")
        except Exception as e:
            print(e)
            return redirect(f"/admin/products/{product_id}?m=Failed+to+update+product")
