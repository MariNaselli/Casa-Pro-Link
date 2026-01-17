import os

class Config:
    SECRET_KEY = 'admin-secret'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///casaprolink.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False