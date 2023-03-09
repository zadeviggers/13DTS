from functools import wraps
from flask import Flask, render_template, redirect, request, session, g
from flask_bcrypt import Bcrypt
import sqlite3
from contextlib import contextmanager
import os

server = Flask(__name__)
bcrypt = Bcrypt(server)

server.secret_key = os.urandom(69)

ADMIN_CODE = "password123"


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


def get_first_dict_item(thing: dict):
    # A helper function for getting out some
    # values returned in a weird way by SQLite
    return list(thing.values())[0]


def get_user():
    # Return the current user session,
    # or return False if there is none.

    # Avoid having to deal with an index error
    if ("username" in session) and ("display_name" in session):
        username = session["username"]
        display_name = session["display_name"]
        admin = session["admin"]

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
            return redirect(f"/auth?m=You+are+not+logged+in")
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
    req_admin_code = request.form["admin_code"]

    if not display_name or not username or not password:
        return False

    admin = req_admin_code == ADMIN_CODE

    encrypted_password = bcrypt.generate_password_hash(password)

    with get_db() as (connection, cursor):
        try:
            cursor.execute(
                "SELECT username FROM Users WHERE username=?", [username])
            res = cursor.fetchall()
            if len(res) > 0:
                return "Username already taken"

            cursor.execute(
                "INSERT INTO Users (admin, display_name, username, password) VALUES (?,?,?,?)",
                [1 if admin else 0, display_name, username, encrypted_password])
            connection.commit()
            session['username'] = username
            session['display_name'] = display_name
            session['admin'] = admin

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
    return render_template("pages/home.jinja", user=g.user)


@server.route("/contact", methods=["GET"])
def handle_contact():
    return render_template("pages/contact.jinja", user=g.user)


@server.route("/menu", methods=["GET"])
@server.route("/menu/<category_id>", methods=["GET"])
def handle_menu(category_id=None):
    with get_db() as (connection, cursor):
        if category_id is not None:
            query = "SELECT * FROM Products WHERE category_id=?"
            cursor.execute(query, [category_id])
        else:
            query = "SELECT * FROM Products"
            cursor.execute(query)
        products = cursor.fetchall()

        cursor.execute("SELECT name, id FROM Categories")
        categories = cursor.fetchall()

        return render_template("pages/menu.jinja", user=g.user, products=products, current_category_id=category_id, categories=categories)


@server.route("/auth", methods=["GET"])
def handle_auth():
    if g.user:
        return redirect("/")

    return render_template("pages/auth.jinja")


@server.route("/auth/login", methods=["POST"])
def handle_auth_log_in():
    if g.user:
        return redirect("/?m=Already%20logged%20in")

    result = try_log_in()

    if result == True:
        return redirect("/")

    return render_template("pages/auth.jinja", failed=result)


@server.route("/auth/register", methods=["POST"])
def handle_auth_register():
    if g.user:
        return redirect("/?m=Already+logged+in")

    res = try_create_account()

    if res == True:
        return redirect("/?m=Successfully+logged+in")

    return render_template("pages/auth.jinja", failed=res)


@server.route("/auth/logout", methods=["GET"])
def handle_auth_log_out():
    if not g.user:
        return render_template("pages/auth.jinja", logged_out=False)

    log_out()

    return render_template("pages/auth.jinja", logged_out=True)


@server.route("/admin", methods=["GET"])
@admin_only
def handle_admin():
    return render_template("pages/admin/admin.jinja", user=g.user)


@server.route("/admin/categories", methods=["GET"])
@admin_only
def handle_admin_categories():
    with get_db() as (connection, cursor):
        cursor.execute("SELECT id, name FROM Categories")
        categories = cursor.fetchall()
        return render_template("pages/admin/categories.jinja", user=g.user, categories=categories)


@server.route("/admin/create-category", methods=["GET", "POST"])
@admin_only
def handle_admin_create_category():
    if request.method == "GET":
        return render_template("pages/admin/create-category.jinja", user=g.user)
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
            category_id = get_first_dict_item(cursor.fetchone())
            return redirect(f"/admin/categories/{category_id}?m=Created+category+{name}")


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

        return render_template("pages/admin/category-info.jinja", user=g.user, category=category_res, products=products_res)


@server.route("/admin/categories/<category_id>/delete", methods=["GET"])
@admin_only
def handle_admin_delete_category(category_id=None):
    if not category_id:
        return redirect("/admin/categories")

    with get_db() as (connection, cursor):
        try:
            # Make sure that the category is empty before deleting it
            number_of_items_query = "SELECT COUNT(*) FROM Products WHERE category_id=?"
            cursor.execute(number_of_items_query, [category_id])
            number_of_items = get_first_dict_item(cursor.fetchone())
            if number_of_items != 0:
                return redirect(f"/admin/categories/{category_id}?m=There+are+still+{number_of_items}+product(s)+in+this+category")

            # Delete the category
            delete_query = "DELETE FROM Categories WHERE id=?"
            cursor.execute(delete_query, [category_id])
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
            category_query = "UPDATE Categories SET name=?  WHERE id=?"
            cursor.execute(category_query, [
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

        return render_template("pages/admin/products.jinja", user=g.user, products=res)


@server.route("/admin/create-product", methods=["GET", "POST"])
@admin_only
def handle_admin_create_product():
    with get_db() as (connection, cursor):
        if request.method == "GET":
            query = "SELECT id, name FROM Categories"
            cursor.execute(query)
            res = cursor.fetchall()
            return render_template("pages/admin/create-product.jinja", user=g.user, categories=res)
        elif request.method == "POST":
            name = request.form["name"]
            description = request.form["description"]
            price = request.form["price"]
            size = request.form["size"]
            category = request.form["category"]
            image_path = request.form["image_path"]

            create_query = "INSERT INTO Products (name, description, price, size, category_id, image_path) VALUES (?, ?, ?, ?, ?, ?)"
            cursor.execute(
                create_query, [name, description, price, size, category, image_path])
            # This is a special SQLite function that gives the ID of the last inserted row
            id_query = "SELECT last_insert_rowid()"
            cursor.execute(id_query)
            connection.commit()
            # Get the returned category ID out
            category_id = get_first_dict_item(cursor.fetchone())
            return redirect(f"/admin/products/{category_id}?m=Created+product+{name}")


@server.route("/admin/delete-random-product", methods=["GET"])
@admin_only
def handle_admin_delete_random_product():
    with get_db() as (connection, cursor):
        try:
            id_query = "SELECT id FROM Products ORDER BY RANDOM() LIMIT 1"
            cursor.execute(id_query)
            product_id = cursor.fetchone()["id"]

            delete_query = "DELETE FROM Products WHERE id=?"
            cursor.execute(delete_query, [product_id])
            connection.commit()
            return redirect(f"/admin/products?m=Successfully+deleted+product+{product_id}")
        except Exception as e:
            print(e)
            return redirect(f"/admin/products/{product_id}?m=Failed+to+delete+product")


@server.route("/admin/products/<product_id>", methods=["GET"])
@admin_only
def handle_admin_product_info(product_id=None):
    if not product_id:
        return redirect("/admin/products")

    with get_db() as (connection, cursor):
        product_query = "SELECT * FROM Products WHERE id=?"
        cursor.execute(product_query, [product_id])
        product_res = cursor.fetchone()

        category_query = "SELECT id, name FROM Categories WHERE id=?"
        cursor.execute(category_query, [product_res["category_id"]])
        category_res = cursor.fetchone()

        categories_query = "SELECT id, name FROM Categories"
        cursor.execute(categories_query)
        categories_res = cursor.fetchall()

        return render_template("pages/admin/product-info.jinja", user=g.user, product=product_res, product_category=category_res, categories=categories_res)


@server.route("/admin/products/<product_id>/delete", methods=["GET"])
@admin_only
def handle_admin_delete_product(product_id=None):
    if not product_id:
        return redirect("/admin/products")

    with get_db() as (connection, cursor):
        try:
            delete_query = "DELETE FROM Products WHERE id=?"
            cursor.execute(delete_query, [product_id])
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
            name = request.form["name"]
            description = request.form["description"]
            price = request.form["price"]
            size = request.form["size"]
            category = request.form["category"]
            image_path = request.form["image_path"]

            product_query = "UPDATE Products SET name=?, description=?, price=?, size=?, category_id=?, image_path=?  WHERE id=?"
            cursor.execute(product_query, [
                           name, description, price, size, category, image_path, product_id])
            connection.commit()
            return redirect(f"/admin/products/{product_id}?m=Successfully+updated+product+{product_id}")
        except Exception as e:
            print(e)
            return redirect(f"/admin/products/{product_id}?m=Failed+to+update+product")
