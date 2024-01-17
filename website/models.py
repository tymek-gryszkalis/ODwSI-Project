from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(150), unique = True)
    username = db.Column(db.String(150))
    password = db.Column(db.String(65535))
    debt = db.Column(db.Float)
    salt = db.Column(db.String(65535))
    verified = db.Column(db.Boolean)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(150))
    value = db.Column(db.Float)
    confirmed = db.Column(db.Boolean)
    payed = db.Column(db.Boolean)
    deadline = db.Column(db.Date)
    lender_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    borrower_id = db.Column(db.Integer, db.ForeignKey("user.id"))

class Code(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    value = db.Column(db.String(12))
    for_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    expires = db.Column(db.DateTime)
    used = db.Column(db.Boolean)