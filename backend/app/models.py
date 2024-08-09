from app import db


class Tweet(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    text = db.Column(db.String, nullable=False)
    date = db.Column(db.Date, nullable=False)
    likes = db.Column(db.Integer, nullable=False)
    should_delete = db.Column(db.Boolean, nullable=False)


class Scout(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    company_id = db.Column(db.BigInteger, nullable=False)
    student_id = db.Column(db.BigInteger, nullable=False)
    date = db.Column(db.Date, nullable=False)
    accepted = db.Column(db.String, nullable=False)
    rejected = db.Column(db.Boolean, nullable=False)


class Profile(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String, nullable=False)
    university = db.Column(db.String, nullable=False)
    grade = db.Column(db.Integer, nullable=False)
    industory = db.Column(db.String, nullable=False)
    twitter_account = db.Column(db.String, nullable=False)


class Company(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String, nullable=False)
    industory = db.Column(db.String, nullable=False)
    details = db.Column(db.String, nullable=True)


class Account(db.Model):
    user_id = db.Column(db.String, primary_key=True)
    password = db.Column(db.String, nullable=False)
    student = db.Column(db.Boolean, nullable=False)
