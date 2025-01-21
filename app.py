from flask import Flask
from extensions import db, login_manager
from main_app.app import main_bp, User
from content_generator.app import content_bp
from infographics_generator.app import infographic_bp

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a strong random key
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://ecombuddha_user:Naveen_EcomBuddha_Karthi@localhost/ecombuddha_db'

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(content_bp, url_prefix='/create_content')
    app.register_blueprint(infographic_bp, url_prefix='/create_infographics')


    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)