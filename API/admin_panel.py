import asyncio
import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
import asyncpg

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '../templates')
)

DATABASE_URL = os.getenv('DATABASE_URL')
app.secret_key = os.getenv('SECRET_KEY')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# -- User class --

class AdminUser(UserMixin):
    def __init__(self, id_):
        self.id = id_

admin_username = "admin"  # Change this
admin_password = "password"  # Store securely, for demo only plaintext here

# -- Async db pool: --

pool = None

async def create_db_pool():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return AdminUser(user_id)
    return None

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == admin_username and password == admin_password:
            user = AdminUser("admin")
            login_user(user)
            flash("Logged in successfully.")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials", "error")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    return redirect(url_for("users"))

@app.route("/users")
@login_required
def users():
    async def fetch_users():
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT user_id, referrals, balance, joined_at FROM users ORDER BY joined_at DESC LIMIT 100"
            )
            return rows
    users = asyncio.run(fetch_users())
    return render_template("users.html", users=users)

@app.route("/investments")
@login_required
def investments():
    async def fetch_investments():
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT ui.investment_id, ui.user_id, ip.name, ui.amount, ui.start_date, ui.maturity_date, ui.withdrawn
                FROM user_investments ui
                JOIN investment_plans ip ON ui.plan_id = ip.plan_id
                ORDER BY ui.start_date DESC LIMIT 100
                """
            )
            return rows
    investments = asyncio.run(fetch_investments())
    return render_template("investments.html", investments=investments)

# Run database pool on app startup
@app.before_first_request
def startup():
    asyncio.run(create_db_pool())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
