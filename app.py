from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://ecombuddha_user:Naveen_EcomBuddha_Karthi@localhost/ecombuddha_db'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
   return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        return 'Invalid username or password'

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            return 'Username already exists, please login'

        password_hash = generate_password_hash(password)
        user = User(username=username, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
  logout_user()
  return redirect(url_for('login'))

@app.route("/")
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route("/create_content")
@login_required
def create_content():
  return "This is for creating content"

@app.route("/create_infographics")
@login_required
def create_infographics():
    return "This is for creating infographics"

@app.route("/create_all")
@login_required
def create_all():
    return "This is for creating content and infographics"

@app.route('/previous_listings', methods=['GET', 'POST'])
@login_required
def previous_listings():
    # add previous listing functionality in here
    return "This page contains previous listings."


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        user = current_user

        if user.check_password(current_password):
           user.password_hash = generate_password_hash(new_password)
           db.session.commit()
           flash("Password updated Successfully", "success")
           return redirect(url_for("dashboard"))
        else:
            flash("Current password is incorrect!", "error")

    return render_template('change_password.html',user=current_user)


with app.app_context():
    db.create_all()

if __name__ == "__main__":
   app.run(debug=True)