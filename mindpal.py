from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Database configurations
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mindpal_user:mindpal@localhost/mindpal_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    phone_no = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(255), nullable=False)


    def __repr__(self):
        return f'<User {self.username}>'
   
# Create tables
with app.app_context():
    db.create_all()

@app.route("/signup", methods=['POST'])
def signup():
    data = request.get_json()
    print(data)

    # Validate signup data
    if not data or not all(k in data for k in ("name", "username", "email", "phone_no", "password")):
        return jsonfiy({"error": "Missing data"}), 400

    existing_username = User.query.filter(User.username == data['username']).first()
    if existing_username:
        return jsonify({"error": "username already exists"})

    # Check if the user already exists
    existing_email = User.query.filter(User.email == data['email']).first()
    if existing_email:
        return jsonify({"error": "Email already exists"})

    # Hash the password for security
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256', salt_length=16)
    print(hashed_password)

    new_user = User(
            name = request.json['name'],
            username = request.json['username'],
            email = request.json['email'],
            phone_no = request.json['phone_no'],
            password = hashed_password 
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": f"User {request.json['name']} created successfully!"}), 201

@app.route("/login", methods=['POST'])
def login():
    data = request.get_json()
    print(data)

    if not data or not all(k in data for k in ("username", "password")):
        return jsonfiy({"error": "Missing data"}), 400

    username = request.json['username']
    password = request.json['password']

    # Fetch user from the database
    user = User.query.filter_by(username=username).first()
    print(user, user.password)

    if user and check_password_hash(user.password, password):
        print("Correct creds")
        return jsonify({"message": "User logined"}), 201 
    
    return jsonify({"message": "User login unsuccessful!"}), 401


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
