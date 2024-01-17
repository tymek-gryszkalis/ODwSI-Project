from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from .models import User, Loan
from . import db
import re
from datetime import datetime, date

views = Blueprint('views', __name__)

@views.route('/', methods = ["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        lender_id = current_user.id
        borrower_id = request.form.get("lendto")
        name = request.form.get("name")
        value = request.form.get("value")
        dd = request.form.get("deadline")
        if not validateLoan(borrower_id, name, value, dd):
            flash("Invalid input", category = "error")
            return redirect(url_for("views.home"))
        value = float(value)
        deadline = date(int(dd.split("-")[0]), int(dd.split("-")[1]), int(dd.split("-")[2]))
        newLoan = Loan(lender_id = lender_id, borrower_id = borrower_id, name = name, value = value, deadline = deadline, confirmed = False)
        db.session.add(newLoan)
        db.session.commit()
        return redirect(url_for("views.home"))
    users = User.query
    loans = Loan.query
    return render_template("home.html", user = current_user, users = users, loans = loans)

def validateLoan(borrower_id, name, value, dd):
    if borrower_id == "" or name == "" or value == "" or dd == "":
        return False
    if not re.fullmatch(r'\b[A-Za-z0-9_]{1,20}\b', name):
        return False
    try:
        float(value)
    except ValueError:
        return False
    if float(value) < 0.0:
        return False
    try:
        deadline = date(int(dd.split("-")[0]), int(dd.split("-")[1]), int(dd.split("-")[2]))
    except ValueError:
        return False
    if date.today() > deadline:
        return False
    return True


@views.route('/drop_database')
@login_required
def drop_database():
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()
    flash("Dropped database", category = "info")
    return redirect(url_for("auth.login"))

@views.route('/pay_loan', methods=["GET", "POST"])
@login_required
def pay_loan():
    if request.method == "POST":
        loan_id = request.form.get("loan_id")
        method = request.form.get("button")
        if validatePayLoan:
            loan = Loan.query.filter_by(id = int(loan_id[:-1])).first()
            if method == "payed":
                manageDebt(loan.borrower_id, loan.value)
            Loan.query.filter_by(id = loan.id).delete()
            db.session.commit()
        else:
            flash("Invalid operation", category = "error")
    return redirect(url_for("views.home"))

def validatePayLoan(loan_id, method):
    try:
        int(loan_id[:-1])
    except ValueError:
        return False
    if not method == "payed" or not method == "withdrawn":
        return False
    return True

@views.route('/confirm_loan', methods=["GET", "POST"])
@login_required
def confirm_loan():
    if request.method == "POST":
        loan_id = request.form.get("loan_id")
        if validateConfirmLoan(loan_id):
            loan = Loan.query.filter_by(id = int(loan_id[:-1])).first()
            loan.confirmed = True
            manageDebt(loan.borrower_id, -loan.value)
        else:
            flash("Invalid operation", category = "error")
    return redirect(url_for("views.home"))

def validateConfirmLoan(loan_id):
    try:
        int(loan_id[:-1])
    except ValueError:
        return False
    return True

def manageDebt(user_id, value):
    user = User.query.filter_by(id = user_id).first()
    user.debt += value
    user.debt = round(user.debt, 2)
    db.session.commit()