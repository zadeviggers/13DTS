from functools import wraps
from flask import Flask, abort, render_template, redirect, request, session, g, url_for
from flask_bcrypt import Bcrypt
import sqlite3
from time import time
import math
from datetime import datetime

# Set up flask and bcrypt
server = Flask(__name__)
bcrypt = Bcrypt(server)

server.secret_key = "top-secrete"


# Note on variable capitalisation:
# When I get values from the database columns,
# I'm naming them the same as they're named
# in the database, which is PascalCase,
# but all other variables (and of course functions)
# are in snake_case.


def time_in_ms():
    # Used to get the current time as an integer of milliseconds
    return math.floor(time() * 1000)


def get_last_inserted_row_id() -> int:
    # Get the ID of the most recently created row
    # This is a special SQLite function: https://www.sqlite.org/lang_corefunc.html#last_insert_rowid
    g.cursor.execute("SELECT last_insert_rowid()")
    id = g.cursor.fetchone()["last_insert_rowid()"]
    return id


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
        # Make sure they're logged in
        if not g.user:
            return redirect(url_for("home_page", m="You are not logged in"))
        # Make sure they're a teacher
        if g.user["teacher"] != True:
            return redirect(url_for("home_page", m="You are not a teacher"))
        return func(*args, **kwargs)

    return wrapper


def get_user():
    # Return the current user session,
    # or return False if there is none.

    # Avoid having to deal with an index error
    if "id" in session:
        id = session["id"]

        g.cursor.execute("SELECT Username, Teacher FROM Users WHERE ID = ?", [id])
        result = g.cursor.fetchone()

        if result is None:
            return False

        return {"id": id, "username": result["Username"], "teacher": result["Teacher"]}

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
    categories_query = "SELECT ID, EnglishName from Categories ORDER BY EnglishName"
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
    return {"categories": g.categories, "user": g.user}


# Handling error 404 and displaying relevant web page
@server.errorhandler(404)
def not_found_error(error):
    return render_template("error.jinja", error_code="404", error=error), 404


# Handling error 500 and displaying relevant web page
@server.errorhandler(500)
def internal_error(error):
    return render_template("error.jinja", error_code="500", error=error), 500


@server.route("/", methods=["GET"])
def home_page():
    # The main homepage, which shows all the words

    # Get all the words
    g.cursor.execute("SELECT * FROM Words ORDER BY MaoriSpelling")
    words = g.cursor.fetchall()

    # Render the page
    return render_template("pages/home.jinja", words=words)


@server.route("/categories/<id>", methods=["GET"])
def category_page(id):
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
    g.cursor.execute(
        "SELECT * FROM Words WHERE CategoryID = ? ORDER BY MaoriSpelling",
        [category["ID"]],
    )
    category_words = g.cursor.fetchall()

    # Render the page
    return render_template(
        "pages/specific_category.jinja", category=category, words=category_words
    )


@server.route("/words/<id>", methods=["GET"])
def word_page(id):
    # Page for just showing words in one category

    # Select the word from the database using the ID
    word_query = "SELECT * FROM Words WHERE ID = ?"
    g.cursor.execute(word_query, [id])
    word = g.cursor.fetchone()

    # If no word with that ID is found, 404 error
    if word == None:
        abort(404)

    # Get the category for that word
    g.cursor.execute("SELECT * FROM Categories WHERE ID = ?", [word["CategoryID"]])
    category = g.cursor.fetchone()

    # Get the creation date
    CreatedAt = datetime.fromtimestamp(word["CreatedAt"] / 1000)

    # Get the user that created the word
    g.cursor.execute(
        "SELECT Username FROM Users WHERE ID = ?", (str(word["CreatedBy"]))
    )
    CreatedBy = g.cursor.fetchone()["Username"]

    # Render the pages
    return render_template(
        "pages/specific_word.jinja",
        category=category,
        word=word,
        created_at=CreatedAt,
        created_by=CreatedBy,
    )


@server.route("/login", methods=["POST"])
def handle_log_in():
    if g.user:
        return redirect(url_for("home_page", m="Already logged in"))

    # Try to log the user in, and return True if it works,
    # or and error message if it doesn't.
    username = request.form["log-in-username"]
    password = request.form["log-in-password"]

    try:
        # Get the user data that matches this username
        g.cursor.execute(
            "SELECT Username, Teacher, PasswordHash, ID FROM Users WHERE Username=?",
            [username],
        )
        res = g.cursor.fetchall()

        # Error if user not found
        if len(res) == 0:
            return redirect(url_for("home_page", m="Username or password is wrong"))

        user = res[0]

        # Check password
        matches = bcrypt.check_password_hash(user["PasswordHash"], password)
        if not matches:
            return redirect(url_for("home_page", m="Username or password is wrong"))

        # Log the user in
        session["id"] = user["ID"]
        return redirect(url_for("home_page"))
    except Exception as e:
        return redirect(url_for("home_page", m=f"Error logging in {str(e)}"))


@server.route("/sign-up", methods=["POST"])
def handle_sign_up():
    if g.user:
        return redirect(url_for("home_page", m="Already logged in"))

    # Try to create and account log the user in.
    # Get the username and password form the form, and validate them
    username = request.form["sign-up-username"].strip()
    if not (3 <= len(username) <= 20):
        return redirect(
            url_for("home_page", m="Choose a username between 3 & 20 characters long")
        )
    if " " in username:
        return redirect(url_for("home_page", m="Usernames can't have spaces in them"))
    password = request.form["sign-up-password"]
    if len(password) < 8:
        return redirect(
            url_for("home_page", m="Passwords should be at least 8 characters long")
        )
    # Checkboxes only send their value if they're checked
    is_teacher = "is-teacher" in request.form

    # Make sure they provided a username & password
    if not username or not password:
        return False

    # Encrypt password
    encrypted_password = bcrypt.generate_password_hash(password)

    try:
        # Check that the username hasn't been used already
        g.cursor.execute("SELECT Username FROM Users WHERE Username=?", [username])
        res = g.cursor.fetchall()

        if len(res) > 0:
            return redirect(url_for("home_page", m="Username already taken"))

        # Create the user
        g.cursor.execute(
            "INSERT INTO Users (Teacher, Username, PasswordHash) VALUES (?,?,?)",
            [1 if is_teacher else 0, username, encrypted_password.decode("utf8")],
        )
        g.db.commit()

        # Get the user ID
        id = get_last_inserted_row_id()
        session["id"] = id

        return redirect(url_for("home_page", m="Successfully registered"))
    except Exception as e:
        return redirect(url_for("home_page", m=f"Error creating account {str(e)}"))


@server.route("/logout", methods=["DELETE", "GET"])
def handle_log_out():
    if g.user == False:
        return redirect(url_for("home_page", m="Not logged in"))

    # Log user out by popping id from session
    session.pop("id")

    return redirect(url_for("home_page", m="Logged out"))


@server.route("/delete-word/<id>", methods=["DELETE", "GET"])
@teacher_only
def delete_word_action(id):
    try:
        # Get the ID of the category it's in to redirect to before deleting it
        g.cursor.execute("SELECT CategoryID FROM Words WHERE ID=?", [id])
        category_id = g.cursor.fetchone()["CategoryID"]

        # Delete the word
        g.cursor.execute("DELETE FROM Words WHERE ID=?", [id])
        g.db.commit()

        # Redirect to the page for the category the word was in
        return redirect(url_for("category_page", id=category_id, m="Deleted word"))

    except Exception as e:
        return redirect(url_for("home_page", m=f"Error deleting word {str(e)}"))


@server.route("/create-word", methods=["POST"])
@teacher_only
def create_word_action():
    try:
        # Get the word's parameters the form

        CategoryID = request.form["category-id"]

        EnglishSpelling = request.form["english-spelling"].strip()
        if len(EnglishSpelling) == 0:
            return redirect(
                url_for(
                    "category_page",
                    id=CategoryID,
                    m="Make sure to add an English spelling",
                )
            )
        MaoriSpelling = request.form["maori-spelling"].strip()
        if len(MaoriSpelling) == 0:
            return redirect(
                url_for(
                    "category_page",
                    id=CategoryID,
                    m="Make sure to add an Maori spelling",
                )
            )
        EnglishDefinition = request.form["english-definition"].strip()
        if len(EnglishDefinition) == 0:
            return redirect(
                url_for(
                    "category_page",
                    id=CategoryID,
                    m="Make sure to add a definition in English",
                )
            )
        YearLevelFirstEncountered = request.form["year-level"]
        if len(YearLevelFirstEncountered) == 0:
            return redirect(
                url_for(
                    "category_page",
                    id=CategoryID,
                    m="Make sure to add a year level",
                )
            )

        if not (0 <= int(YearLevelFirstEncountered) <= 13):
            return redirect(
                url_for(
                    "category_page",
                    id=CategoryID,
                    m="Enter a year level between 0 and 13",
                )
            )
        ImageFilename = request.form["image-filename"]
        # Handle empty strings
        if len(ImageFilename) == 0:
            ImageFilename = None

        # Create the word
        g.cursor.execute(
            "INSERT INTO Words (MaoriSpelling, EnglishSpelling, EnglishDefinition, CategoryID, YearLevelFirstEncountered, ImageFilename, CreatedBy, CreatedAt) VALUES (?,?,?,?,?,?,?,?)",
            [
                MaoriSpelling,
                EnglishSpelling,
                EnglishDefinition,
                CategoryID,
                YearLevelFirstEncountered,
                ImageFilename,
                g.user["id"],
                time_in_ms(),
            ],
        )
        g.db.commit()

        # Redirect to the page for the created word
        id = get_last_inserted_row_id()
        return redirect(url_for("word_page", id=id))

    except Exception as e:
        return redirect(url_for("home_page", m=f"Error creating word {str(e)}"))


@server.route("/delete-category/<id>", methods=["DELETE", "GET"])
@teacher_only
def delete_category_action(id):
    try:
        # Don't let the category be deleted if it has words in it
        g.cursor.execute("SELECT ID from Words WHERE CategoryID=?", [id])
        words = g.cursor.fetchall()
        if len(words) > 0:
            return redirect(
                url_for(
                    "category_page",
                    id=id,
                    m="You need to delete all words in the category first",
                )
            )

        # Delete the category
        g.cursor.execute("DELETE FROM Categories WHERE ID=?", [id])
        g.db.commit()

        # Redirect to the home page
        return redirect(url_for("home_page", m="Deleted category"))

    except Exception as e:
        return redirect(url_for("home_page", m=f"Error deleting category {str(e)}"))


@server.route("/create-category", methods=["POST"])
@teacher_only
def create_category_action():
    # Get the word's parameters the form
    EnglishName = request.form["english-name"].strip()
    if len(EnglishName) == 0:
        return redirect(
            url_for(
                "home_page",
                m="Make sure to add a name in English",
            )
        )

    try:
        # Create the category
        g.cursor.execute(
            "INSERT INTO Categories (EnglishName) VALUES (?)",
            [EnglishName],
        )
        g.db.commit()

        # Redirect to the newly created category page
        id = get_last_inserted_row_id()
        return redirect(url_for("category_page", id=id))

    except Exception as e:
        return redirect(url_for("home_page", m=f"Error creating word {str(e)}"))


if __name__ == "__main__":
    # Start the server
    # debug=True makes it so that the server automatically restarts when you save files
    server.run(port=6969, debug=True)
