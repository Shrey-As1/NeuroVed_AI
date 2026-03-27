import os
from datetime import datetime
from flask import Flask, render_template
from flask_login import LoginManager, login_required, current_user
from config import Config
from database import db
from auth import auth_bp, User
from chatbot.routes import chat_bp
from storage_bot.routes import storage_bp
from hospitals.routes import hosp_bp
from analyzer.routes import analyzer_bp
from utils.quotes import get_daily_quote


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure upload directories exist
    for key in ["UPLOAD_PRESCRIPTIONS", "UPLOAD_MEDICINES", "UPLOAD_ANALYZER"]:
        os.makedirs(app.config[key], exist_ok=True)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please login to access this page."
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(storage_bp)
    app.register_blueprint(hosp_bp)
    app.register_blueprint(analyzer_bp)

    @app.route("/")
    def landing():
        return render_template("landing.html")

    @app.route("/dashboard")
    @login_required
    def dashboard():
        quote = get_daily_quote()
        return render_template("dashboard.html", quote=quote, now=datetime.now())

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)



    