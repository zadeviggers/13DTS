from functools import wraps
from typing import Tuple
from flask import Flask, abort, render_template, redirect, request, session, g
from flask_bcrypt import Bcrypt
import sqlite3
from contextlib import contextmanager
from collections.abc import Generator
import os

# Set up flask and bcrypt
server = Flask(__name__)
bcrypt = Bcrypt(server)

# Generate a random key each time the server restarts.
server.secret_key = os.urandom(69)


def db_dict_factory(cursor, row):
    # Used to return database query results as dictionaries.
    # From the docs: https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.row_factory

    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_db() -> sqlite3.Connection:
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

    return db_connection


def get_first_dict_item(thing: dict):
    # A helper function for getting out some
    # values returned in a weird way by SQLite
    return list(thing.values())[0]


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


def get_user():
    # Return the current user session,
    # or return False if there is none.

    # Avoid having to deal with an index error
    if ("id" in session):
        id = session["id"]

        g.cursor.execute(
            "SELECT Name, Teacher FROM Users WHERE ID = ?", [id])
        result = g.cursor.fetchone()

        if result is None:
            return False

        return {
            "id": id,
            "name": result["name"],
            "teacher": result["teacher"]
        }

    return False


@server.before_request
def before_request():
    # This function runs before the request handler on each request.
    # Docs: https://flask.palletsprojects.com/en/2.2.x/api/#flask.Flask.before_request

    # Get a single db connection for the whole request to use
    # Docs: https://flask.palletsprojects.com/en/2.2.x/api/?highlight=g#flask.g
    g.db = get_db()
    # Also a cursor
    g.cursor = g.db.cursor()

    # Get the user and stick it on the globally available object

    g.user = get_user()

    # Also add the list of categories to the global object
    categories_query = "SELECT ID, EnglishName from Categories"
    g.cursor.execute(categories_query)
    categories = g.cursor.fetchall()
    g.categories = categories


@server.teardown_request
def teardown_request(error):
    # This function is always run after a request happens.
    # Docs: https://flask.palletsprojects.com/en/2.2.x/api/#flask.Flask.teardown_request

    # Close the database connection
    g.db.close()


@server.context_processor
def context_processor():
    # This function is called before rendering a template,
    # and can pass extra params to the template.
    return {
        'categories': g.categories,
        'user': g.user
    }


@server.route("/", methods=["GET"])
def home_page():
    # The main homepage, which shows all the words

    # Get all the words
    words_query = "SELECT * FROM Words"
    g.cursor.execute(words_query)
    words = g.cursor.fetchall()

    # Render the page
    return render_template("pages/home.jinja", words=words)


@server.route("/categories/<id>", methods=["GET"])
def specific_category_page(id):
    # Page for just showing words in one category

    # No need to re-query the database, when we already have a list of all the categories
    category = None
    for _category in g.categories:
        if str(_category["ID"]) == id:
            category = _category

    # If a category couldn't be found, 404 error
    if category == None:
        abort(404)

    # Get the words in that category
    category_words_query = "SELECT * FROM Words WHERE CategoryID = ?"
    g.cursor.execute(category_words_query, [category["ID"]])
    category_words = g.cursor.fetchall()

    # Render the page
    return render_template("pages/specific_category.jinja", category=category, words=category_words)


@server.route("/words/<id>", methods=["GET"])
def specific_word_page(id):
    # Page for just showing words in one category

    # Select the word from the database using the ID
    word_query = "SELECT * FROM Words WHERE ID = ?"
    g.cursor.execute(word_query, [id])
    word = g.cursor.fetchone()

    # If no word with that ID is found, 404 error
    if word == None:
        abort(404)

    # Get the category for that word
    category_query = "SELECT * FROM Categories WHERE ID = ?"
    g.cursor.execute(category_query, [word["CategoryID"]])
    category = g.cursor.fetchone()

    # Render the pages
    return render_template("pages/specific_word.jinja", category=category, word=word)


if __name__ == "__main__":
    server.run(port=6969, debug=True)
