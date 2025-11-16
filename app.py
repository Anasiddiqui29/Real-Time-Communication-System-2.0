from flask import Flask, render_template, request, url_for, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from encryption import encrypt_message, decrypt_message

# Initialize Flask app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "supersecretkey"

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Track online users
online_users = {}

# User model
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)

# Create database
with app.app_context():
    db.create_all()

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Home route
@app.route("/")
def home():
    return render_template("home.html")

# Register route
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if Users.query.filter_by(username=username).first():
            return render_template("sign_up.html", error="Username already taken!")

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        new_user = Users(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))
    
    return render_template("sign_up.html")

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = Users.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

# Protected dashboard route 
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("chat.html", username=current_user.username)

# API to get online users
@app.route("/api/users")
@login_required
def get_users():
    users = [{"username": username, "status": "online"} for username in online_users.keys()]
    return jsonify(users)

# Logout route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

# SocketIO Events
@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        online_users[current_user.username] = request.sid
        emit('user_list', list(online_users.keys()), broadcast=True)
        print(f"[CONNECTED] {current_user.username}")

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated and current_user.username in online_users:
        del online_users[current_user.username]
        emit('user_list', list(online_users.keys()), broadcast=True)
        print(f"[DISCONNECTED] {current_user.username}")

@socketio.on('send_message')
def handle_message(data):
    recipient = data.get('recipient')
    message = data.get('message')
    encrypted = data.get('encrypted', False)
    
    # If message is not already encrypted, encrypt it
    if not encrypted:
        try:
            encrypted_message = encrypt_message(message)
            print(f"[ENCRYPTION] Message encrypted for {recipient}")
        except Exception as e:
            print(f"[ENCRYPTION ERROR] {e}")
            encrypted_message = message
    else:
        encrypted_message = message
    
    if recipient in online_users:
        emit('receive_message', {
            'sender': current_user.username,
            'message': encrypted_message,
            'encrypted': True
        }, room=online_users[recipient])
    
    # Send confirmation back to sender
    emit('message_sent', {
        'recipient': recipient,
        'message': encrypted_message,
        'encrypted': True
    })

@socketio.on('call_user')
def handle_call(data):
    recipient = data.get('recipient')
    offer = data.get('offer')
    
    if recipient in online_users:
        emit('incoming_call', {
            'caller': current_user.username,
            'offer': offer
        }, room=online_users[recipient])

@socketio.on('answer_call')
def handle_answer(data):
    caller = data.get('caller')
    answer = data.get('answer')
    
    if caller in online_users:
        emit('call_answered', {
            'answerer': current_user.username,
            'answer': answer
        }, room=online_users[caller])

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    recipient = data.get('recipient')
    candidate = data.get('candidate')
    
    if recipient in online_users:
        emit('ice_candidate', {
            'sender': current_user.username,
            'candidate': candidate
        }, room=online_users[recipient])

@socketio.on('end_call')
def handle_end_call(data):
    recipient = data.get('recipient')
    
    if recipient in online_users:
        emit('call_ended', {
            'user': current_user.username
        }, room=online_users[recipient])

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)