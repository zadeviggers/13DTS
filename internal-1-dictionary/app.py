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
    #   cursor.execute("SELECT * FROM Words")
    # ```

    # Code to acquire resource.
    db_connection = sqlite3.connect("dictionary.db")
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
    if ("id" in session):
        with get_db() as (connection, cursor):
            id = session["id"]

            cursor.execute(
                "SELECT Name, Teacher FROM Users WHERE ID = ?", [id])
            result = cursor.fetchone()

            if result is None:
                return False

            return {
                "id": id,
                "name": result["name"],
                "teacher": result["teacher"]
            }

    return False


def teacher_only(func):
    # A custom decorator to make pages require the user to be logged in as a teacher
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not g.user:
            return redirect(f"/auth?m=You+are+not+logged+in")
        if (g.user["teacher"] != True):
            return redirect("/?m=You+are+not+a+teacher")
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


@server.route("/", methods=["GET"])
def handle_home():
    return render_template("pages/home.jinja",  user=g.user)


if __name__ == "__main__":
    server.run(port=6969, debug=True)
