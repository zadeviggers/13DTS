from flask import Flask, render_template


server = Flask(__name__)


@server.route("/")
def home_route():
    return render_template("home.jinja",)


@server.route("/menu")
def menu_route():
    return render_template("menu.jinja")


@server.route("/contact")
def contact_route():
    return render_template("contact.jinja")
