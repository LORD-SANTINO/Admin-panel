import os
import psycopg2
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# Database connection function
def get_db_connection():
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    return conn

# Setup Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class AdminUser(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return AdminUser(user_id)
    return None

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Get credentials from environment variables
        admin_user = 'admin'
        admin_pass = 'password'
        
        if username == admin_user and password == admin_pass:
            user = AdminUser("admin")
            login_user(user)
            flash('Logged in successfully!')
            return redirect(url_for('users'))
        else:
            flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    return redirect(url_for('users'))

@app.route('/users')
@login_required
def users():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT user_id, referrals, balance, joined_at FROM users ORDER BY joined_at DESC LIMIT 100')
        users = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('users.html', users=users)
    except Exception as e:
        flash(f'Error loading users: {str(e)}')
        return render_template('users.html', users=[])

@app.route('/investments')
@login_required
def investments():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT ui.investment_id, ui.user_id, ip.name, ui.amount, ui.start_date, ui.maturity_date, ui.withdrawn
            FROM user_investments ui
            JOIN investment_plans ip ON ui.plan_id = ip.plan_id
            ORDER BY ui.start_date DESC LIMIT 100
        ''')
        investments = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('investments.html', investments=investments)
    except Exception as e:
        flash(f'Error loading investments: {str(e)}')
        return render_template('investments.html', investments=[])

if __name__ == '__main__':
    app.run(debug=True)
