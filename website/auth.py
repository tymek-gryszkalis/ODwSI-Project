from flask import Blueprint, render_template, request

auth = Blueprint("auth", __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    return render_template("login.html")

@auth.route("/signup", methods=['GET', 'POST'])
def logout():
    if request.method == "POST":
        email = request.form.get("email")
        pwd = request.form.get("pwd")
    return render_template("signup.html")