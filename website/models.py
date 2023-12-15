from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(150), unique = True)
    username = db.Column(db.String(150))
    password = db.Column(db.String(150))
    loans = db.relationship("Loan")

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(150))
    amount = db.Column(db.Float)
    confirmed = db.Column(db.Boolean)
    payed = db.Column(db.Boolean)
    lender_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    borrower_id = db.Column(db.Integer, db.ForeignKey("user.id"))