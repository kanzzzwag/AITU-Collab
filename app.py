import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import uuid

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL').replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Change these lines near the top of app.py
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)

# --- LOGIN MANAGER SETUP ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- DATABASE MODELS ---

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_picture = db.Column(db.String(255), nullable=True, default='default.png')
    
    # Profile Info
    course_year = db.Column(db.String(20), nullable=True)
    major = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    skills = db.Column(db.String(255), nullable=True)

    # Relationships
    projects = db.relationship('Project', backref='author', lazy=True)
    requests_sent = db.relationship('JoinRequest', foreign_keys='JoinRequest.sender_id', backref='sender', lazy=True)
    reviews_received = db.relationship('Review', foreign_keys='Review.reviewee_id', backref='reviewee', lazy=True)

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    required_skills = db.Column(db.String(255), nullable=False)
    partners_needed = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Open') # Open or Closed
    
    # Foreign Key linking to the user
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship
    requests = db.relationship('JoinRequest', backref='project', lazy=True, cascade="all, delete-orphan")

class JoinRequest(db.Model):
    __tablename__ = 'join_requests'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default='Pending') # Pending, Accepted, Declined
    
    # Foreign Keys
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    stars = db.Column(db.Integer, nullable=False) # 1 to 5
    
    # Foreign Keys
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    
    # Relationships
    sender = db.relationship('User', backref='messages_sent')
    project = db.relationship('Project', backref='messages')


# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('register'))
        
        # Create new user with hashed password
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password, method='pbkdf2:sha256')
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()

        # Verify password
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    projects = Project.query.filter(Project.status == 'Open', Project.partners_needed > 0).order_by(Project.id.desc()).all()
    return render_template('dashboard.html', projects=projects)

@app.route('/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    if request.method == 'POST':
        title = request.form.get('title')
        course_name = request.form.get('course_name')
        description = request.form.get('description')
        required_skills = request.form.get('required_skills')
        partners_needed = request.form.get('partners_needed')
        
        new_project = Project(
            title=title,
            course_name=course_name,
            description=description,
            required_skills=required_skills,
            partners_needed=int(partners_needed),
            author_id=current_user.id
        )
        # Save to the postgres
        db.session.add(new_project)
        db.session.commit()
        
        flash('Project created successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('new_project.html')

@app.route('/project/<int:project_id>')
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    existing_request = JoinRequest.query.filter_by(sender_id=current_user.id, project_id=project_id).first()
    return render_template('project_detail.html', project=project, existing_request=existing_request)

@app.route('/project/<int:project_id>/join', methods=['POST'])
@login_required
def join_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    if project.author_id == current_user.id:
        flash('You cannot join your own project.', 'danger')
        return redirect(url_for('project_detail', project_id=project_id))
    
    existing_request = JoinRequest.query.filter_by(sender_id=current_user.id, project_id=project_id).first()

    if not existing_request:
        new_request = JoinRequest(sender_id=current_user.id, project_id=project_id)
        db.session.add(new_request)
        db.session.commit()
        flash('Join request sent successfully! The author will review your request.', 'success')
    
    return redirect(url_for('project_detail', project_id=project_id))


@app.route('/notifications')
@login_required
def notifications():
    incoming_requests = JoinRequest.query.join(Project).filter(
        Project.author_id == current_user.id,
        JoinRequest.status == 'Pending'
    ).all()

    return render_template('notifications.html', requests = incoming_requests)

@app.route('/request/<int:request_id>/<action>', methods=['POST'])
@login_required
def manage_request(request_id, action):
    join_request = JoinRequest.query.get_or_404(request_id)

    if join_request.project.author_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('dashboard'))

    if action == 'accept':
        join_request.status = 'Accepted'
        if join_request.project.partners_needed > 0:
            join_request.project.partners_needed -= 1
        flash(f"You accepted {join_request.sender.username}'s request to join '{join_request.project.title}'.", 'success')

    elif action == 'decline':
        join_request.status = 'Declined'
        flash(f"You declined {join_request.sender.username}'s request to join '{join_request.project.title}'.", 'info')

    db.session.commit()
    return redirect(url_for('notifications'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.username = request.form.get('username')
        current_user.major = request.form.get('major')
        current_user.course_year = request.form.get('course_year')
        current_user.skills = request.form.get('skills')
        current_user.bio = request.form.get('bio')
        
        # uuid
        pic = request.files.get('profile_pic')
        if pic and pic.filename != '':
            ext = os.path.splitext(pic.filename)[1]
            unique_filename = str(uuid.uuid4()) + ext
            
            pic.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            current_user.profile_pic = unique_filename
            
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile'))
        
    return render_template('profile.html')

@app.route('/chat/<int:project_id>', methods=['GET', 'POST'])
@login_required
def chat_room(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Only author or accepted members can view the chat
    is_author = project.author_id == current_user.id
    is_member = JoinRequest.query.filter_by(sender_id=current_user.id, project_id=project.id, status='Accepted').first()
    
    if not (is_author or is_member):
        flash("You don't have permission to view this chat.", "danger")
        return redirect(url_for('chats'))

    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            new_msg = Message(content=content, sender_id=current_user.id, project_id=project.id)
            db.session.add(new_msg)
            db.session.commit()
            return redirect(url_for('chat_room', project_id=project.id))

    messages = Message.query.filter_by(project_id=project.id).order_by(Message.timestamp.asc()).all()
    return render_template('chat_room.html', project=project, messages=messages)

@app.route('/chats')
@login_required
def chats():
    my_projects = Project.query.filter_by(author_id=current_user.id).all()
    accepted_requests = JoinRequest.query.filter_by(sender_id=current_user.id, status='Accepted').all()
    joined_projects = [req.project for req in accepted_requests]
    chat_rooms = list(set(my_projects + joined_projects))
    return render_template('chats.html', chat_rooms=chat_rooms)

@app.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def public_profile(user_id):
    # get the user we are looking at
    target_user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # make sure users can't review themselves
        if target_user.id == current_user.id:
            flash("You cannot review yourself!", "danger")
            return redirect(url_for('public_profile', user_id=target_user.id))
            
        # get the star rating from the form
        stars = int(request.form.get('stars'))
        
        # save to database
        new_review = Review(stars=stars, reviewer_id=current_user.id, reviewee_id=target_user.id)
        db.session.add(new_review)
        db.session.commit()
        
        flash(f"You left a {stars}-star review for {target_user.username}!", "success")
        return redirect(url_for('public_profile', user_id=target_user.id))
        
    # calculate their average rating to display
    reviews = Review.query.filter_by(reviewee_id=target_user.id).all()
    avg_rating = round(sum(r.stars for r in reviews) / len(reviews), 1) if reviews else "No reviews yet"
    
    return render_template('public_profile.html', target_user=target_user, reviews=reviews, avg_rating=avg_rating)

# initialize the database tables
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)