import os

class Config:
    SECRET_KEY = 'una-clave-muy-secreta'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///casaprolink.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False