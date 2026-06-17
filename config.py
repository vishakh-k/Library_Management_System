"""Application configuration classes."""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration with shared settings."""

    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret-key-change-me')

    # MySQL settings
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'password')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'library_db')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_CURSORCLASS = 'DictCursor'

    # Flask-WTF
    WTF_CSRF_ENABLED = True

    # Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False


class TestingConfig(Config):
    """Testing environment configuration."""

    TESTING = True
    DEBUG = True
    MYSQL_DB = os.environ.get('MYSQL_TEST_DB', 'library_db_test')
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
