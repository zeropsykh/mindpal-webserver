import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')  # Provided by Render
    SQLALCHEMY_TRACK_MODIFICATIONS = False