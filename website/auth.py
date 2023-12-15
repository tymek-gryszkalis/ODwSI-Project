from flask import Blueprint, render_template, request, redirect, url_for
from .models import User
from . import db

auth = Blueprint("auth", __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    return render_template("login.html")

@auth.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        pwd = request.form.get("pwd")
        name = request.form.get("usr")
        newUser = User(email = email, username = name, password = pwd)
        db.session.add(newUser)
        db.session.commit()
        return redirect(url_for("auth.login"))
    return render_template("signup.html")