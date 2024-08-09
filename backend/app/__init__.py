from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes.auth import auth_bp
    from app.routes.tweet import tweet_bp
    from app.routes.profile import profile_bp
    from app.routes.scout import scout_bp
    from app.routes.register import register_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tweet_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(scout_bp)
    app.register_blueprint(register_bp)

    return app
