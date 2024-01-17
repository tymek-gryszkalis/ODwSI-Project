from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from .models import User, Code
from . import db, mail
from flask_mail import Message
import time, hashlib, json, random, string, os, re
from datetime import datetime
from datetime import timedelta

auth = Blueprint("auth", __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        pwd = request.form.get("pwd")
        if email == "" or pwd == "":
            flash("All fields must be filled in.", category = "error")
            return redirect(url_for("auth.login"))
        if not validateEmail(email):
            flash("Invalid input", category = "error")
            return redirect(url_for("auth.login"))
        user = User.query.filter_by(email = email).first()
        time.sleep(0.5)
        if user:
            if user.verified:
                if preparepwd(pwd, user.salt) == user.password:
                    login_user(user)
                    return redirect(url_for("views.home"))
            else:
                flash("User not verified", category = "error")
                return redirect(url_for("auth.login"))
        flash("Incorrect username or password.", category = "error")
        return redirect(url_for("auth.login"))
    return render_template("login.html")

@auth.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        pwd = request.form.get("pwd")
        rpwd = request.form.get("rpwd")
        name = request.form.get("usr")

        if email == "" or pwd == "" or rpwd == "" or name == "":
            flash("All fields must be filled in.", category = "error")
            return redirect(url_for("auth.signup"))
        if not validateEmail(email):
            flash("Invalid input", category = "error")
            return redirect(url_for("auth.signup"))
        if not validateName(name):
            flash("Invalid username. You can use only letters, numbers and '_' sign.", category = "error")
            return redirect(url_for("auth.signup"))
        
        emailCheck = User.query.filter_by(email = email).first()
        if emailCheck:
            flash("Email already exist", category = "error")
        elif handlepwd(pwd, rpwd):
            salt = ''.join(random.choices(string.ascii_uppercase + string.digits, k=65535))
            pwd_todb = preparepwd(pwd, salt)
            newUser = User(email = email, username = name, password = pwd_todb, debt = 0.0, salt = salt, verified = False)
            db.session.add(newUser)
            db.session.commit()

            sendVerificationEmail(newUser)
            flash("Registration successful. We sent an email in order to verify your account", category = "info")
            return redirect(url_for("auth.login"))    
        return redirect(url_for("auth.signup"))
    return render_template("signup.html")

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/pwd_recovery', methods=["GET", "POST"])
def pwd_recovery():
    if request.method == "POST":
        email = request.form.get("email")
        if email == "" or not validateEmail(email):
            flash("Invalid input", category = "error")
            return redirect(url_for('auth.pwd_recovery'))
        user = User.query.filter_by(email = email).first()
        if user:
            sendRecoveryEmail(user)
        flash("Email sent. The link will expire in 1 minute.", category = "info")   
        return redirect(url_for('auth.pwd_recovery'))
    return render_template("pwd_recovery.html")

@auth.route("change_pwd_logged", methods=["GET", "POST"])
@login_required
def change_pwd_logged():
    if request.method == "POST":
        opwd = request.form.get("opwd")
        pwd = request.form.get("pwd")
        rpwd = request.form.get("rpwd")
        if handlepwd(pwd, rpwd, opwd):
            current_user.password = preparepwd(pwd, current_user.salt)
            db.session.commit()
            flash("Password changed", category = "info")
            return redirect(url_for("views.home"))           
    return render_template("pwd_change_logged.html")

@auth.route("/recover/<inputVal>", methods=["GET", "POST"])
def recoverPassword(inputVal):
    code = Code.query.filter_by(value = inputVal).first()
    if request.method == "POST":
        pwd = request.form.get("pwd")
        rpwd = request.form.get("rpwd")
        if handlepwd(pwd, rpwd):
            code.used = True
            user = User.query.filter_by(id = code.for_user_id).first()
            user.pwd = preparepwd(pwd, user.salt)
            db.session.commit()
            flash("Password changed", category = "info")
            return redirect(url_for("auth.login"))
        return redirect(url_for("auth.recoverPassword", inputVal = inputVal))
    else:
        time.sleep(0.5)
        if code:
            if not code.used: 
                if datetime.now() < code.expires:
                    return render_template("pwd_change.html")
                else:
                    flash("Link expired!", category = "error")
                    return redirect(url_for("auth.pwd_recovery"))
        flash("Invalid link!", category = "error")
        return redirect(url_for("auth.pwd_recovery"))
    
@auth.route("/verify/<inputVal>", methods=["GET", "POST"])
def verifyAccount(inputVal):
    code = Code.query.filter_by(value = inputVal).first()
    if code:
        if not code.used:
            if datetime.now() < code.expires:
                code.used = True
                user = User.query.filter_by(id = code.for_user_id).first()
                user.verified = True
                db.session.commit()
                flash("User verified!", category = "info")
                return redirect(url_for("auth.login"))
            else:
                flash("Link expired!", category = "error")
    flash("Invalid link!", category = "error")
    return redirect(url_for("auth.login"))

emailRegex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
def validateEmail(email):
    if (re.fullmatch(emailRegex, email)):
        return True
    return False

def handlepwd(pwd, rpwd, opwd = ""):
    if opwd != "":
        if current_user.password != preparepwd(opwd, current_user.salt):
            flash("Current password is not correct!", category = "error")
            return False
    if not validatepwd(pwd):
        flash("""
        <b>Unacceptable password!</b><br><br>
        Password must:
        <ul>
            <li>Be at least 8 characters long</li>
            <li>Contain both upper and lowercase characters</li>
            <li>Contain at least 1 number</li>
            <li>Contain at least 1 special character (!@#$%^&*)</li>
        </ul>
        """, category = "error")
        return False
    elif pwd != rpwd:
        flash("Passwords don't match!", category = "error")
        return False
        
    return True

nameRegex = r'\b[A-Za-z0-9_]{1,20}\b'
def validateName(name):
    if (re.fullmatch(nameRegex, name)):
        return True
    return False

def validatepwd(plain):
    PWDLEN = 8
    SPECIALCHARS = "!@#$%^&*"
    NUMBERS = "1234567890"
    if len(plain) < PWDLEN:
        return False
    if plain.islower() or plain.isupper():
        return False
    if not [i for i in plain if i in SPECIALCHARS]:
        return False
    if not [i for i in plain if i in NUMBERS]:
        return False
    return True

def preparepwd(plain, salt):
    salt = salt.encode()
    plain = plain.encode()

    p = open(os.getcwd() + '\\website\\static\\config.json')
    data = json.load(p)
    pepper = data["pepper"]
    pepper = pepper.encode()

    hash = hashlib.sha256(salt + plain + pepper).hexdigest()

    return hash

def sendRecoveryEmail(user):
    msg = Message('Loanshark password recovery', sender = 'loanshark@gmail.com', recipients = [user.email])
    msg.body = "Link for the password recovery: http://127.0.0.1:5000/recover/" + generateRandomCode(user)
    mail.send(msg)

def sendVerificationEmail(user):
    msg = Message('Loanshark account verification', sender = 'loanshark@gmail.com', recipients = [user.email])
    msg.body = "Link to account verification: http://127.0.0.1:5000/verify/" + generateRandomCode(user)
    mail.send(msg)

def generateRandomCode(user):
    value = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    expires = datetime.now() + timedelta(minutes = 1)
    code = Code(value = value, expires = expires, for_user_id = user.id)
    db.session.add(code)
    db.session.commit()
    return value