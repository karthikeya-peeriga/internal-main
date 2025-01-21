from flask import Flask, render_template, redirect, url_for, request, flash, Blueprint, current_app
from flask_login import  UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from extensions import db, login_manager
from sqlalchemy import DateTime
from datetime import datetime

main_bp = Blueprint('main_app', __name__, template_folder='templates')

class User(UserMixin, db.Model):
   id = db.Column(db.Integer, primary_key=True)
   username = db.Column(db.String(100), unique=True, nullable=False)
   password_hash = db.Column(db.String(200), nullable=False)
   submissions = db.relationship('ProductSubmission', backref='user', lazy=True)
   infographic_submissions = db.relationship('InfographicSubmission', backref='user', lazy=True)
   def check_password(self, password):
       return check_password_hash(self.password_hash, password)

class ProductSubmission(db.Model):
 id = db.Column(db.Integer, primary_key=True)
 user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
 timestamp = db.Column(DateTime(timezone=True), default=datetime.utcnow)
 product_data = db.Column(db.JSON)
 claude_response = db.Column(db.JSON)
 download_time = db.Column(db.DateTime(timezone=True), nullable=True)

class InfographicSubmission(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
   timestamp = db.Column(DateTime(timezone=True), default=datetime.utcnow)
   input_type = db.Column(db.String(50))
   product_image = db.Column(db.String(200))
   product_data = db.Column(db.JSON)
   claude_response = db.Column(db.JSON)
   download_time = db.Column(db.DateTime(timezone=True), nullable=True)

@login_manager.user_loader
def load_user(user_id):
  with current_app.app_context():
      return db.session.get(User, int(user_id))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
   if request.method == 'POST':
       username = request.form['username']
       password = request.form['password']
       
       with current_app.app_context():
          user = User.query.filter_by(username=username).first()
       
       if user and user.check_password(password):
           login_user(user)
           return redirect(url_for('main_app.dashboard'))
       return 'Invalid username or password'
   return render_template('login.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
   if request.method == 'POST':
       username = request.form['username']
       password = request.form['password']

       if User.query.filter_by(username=username).first():
           return 'Username already exists, please login'
       
       password_hash = generate_password_hash(password)
       with current_app.app_context():
         user = User(username=username, password_hash=password_hash)
         db.session.add(user)
         db.session.commit()
       return redirect(url_for('main_app.login'))
   
   return render_template('register.html')

@main_bp.route('/logout')
@login_required
def logout():
 logout_user()
 return redirect(url_for('main_app.login'))

@main_bp.route("/")
@login_required
def dashboard():
   return render_template('dashboard.html', user=current_user)

@main_bp.route('/previous_listings', methods=['GET', 'POST'])
@login_required
def previous_listings():
   # add previous listing functionality in here
   return "This page contains previous listings."

@main_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
   if request.method == 'POST':
       current_password = request.form['current_password']
       new_password = request.form['new_password']
       user = current_user

       if user.check_password(current_password):
         user.password_hash = generate_password_hash(new_password)
         with current_app.app_context():
            db.session.commit()
         flash("Password updated Successfully", "success")
         return redirect(url_for("main_app.dashboard"))
       else:
           flash("Current password is incorrect!", "error")
   
   return render_template('change_password.html',user=current_user)