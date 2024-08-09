import os


class Config:
    SECRET_KEY = "password"
    SQLALCHEMY_DATABASE_URI = "sqlite:///your_database.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
