import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost/mytodolist'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 使用与SECRET_KEY相同的值确保一致性
    JWT_SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'