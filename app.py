from collections import UserDict
from models import db, connect_db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm
from flask import Flask, render_template, redirect, flash, session
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy import exc


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///aa'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = 'secret'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
debug = DebugToolbarExtension(app)

connect_db(app) 

@app.route('/')
def redirect_to_register():
    return redirect('/register')

@app.route('/register', methods=["GET","POST"])
def register_user():
    form = RegisterForm()
    if form.validate_on_submit():
        # Get form data
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
      
        # Try to instantiate user
        new_user = User.register_user(username, password)
        new_user.email = email
        new_user.first_name = first_name
        new_user.last_name = last_name

        db.session.add(new_user)
        try:
            db.session.commit()
            session["user_id"] = username
            return redirect(f'/users/{username}')
        except exc.IntegrityError:
            flash('Sorry, that username or email is taken. Please try again.')

    return render_template('register.html', form=form)

@app.route('/login', methods=["GET","POST"])
def log_in_user():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.authenticate(username, password)

        if user:
            session["user_id"] = username
            return redirect(f'/users/{user.username}')
        else:
            flash("Wrong username or password. Please try again.")
    return render_template('login.html', form=form)

@app.route('/logout')
def log_out():
    session.clear()
    return redirect("/login")

@app.route('/users/<username>')
def show_user_details(username):
    if "user_id" not in session:
        flash("You must be logged in to view.")
        return redirect("/login")
    else:
        user = User.query.filter_by(username=username).first()
        feedback = Feedback.query.filter_by(username=username).all()
        return render_template('user_detail.html', user=user, feedback=feedback)

@app.route('/users/<username>/feedback/add', methods=["GET","POST"])
def add_feedback(username):
    if "user_id" not in session:
        flash("You must be logged in to view.")
        return redirect('/login')
    form = FeedbackForm()
    user = User.query.get_or_404(username)
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        new_feedback = Feedback(title=title, content=content, username = user.username)
        db.session.add(new_feedback)
        db.session.commit()
        return redirect(f'/users/{user.username}')
    return render_template('add_feedback.html', form=form, user=user)

@app.route('/users/<username>/delete', methods=["POST"])
def delete_user(username):
    if "user_id" not in session:
        flash("Must be logged in to do this.")
        return redirect('/login')
    current_user = session.get("user_id")
    delete_user = User.query.filter_by(username=username).first()
    if current_user != delete_user.username:
        flash("You can only delete your own account, meanie")
        return redirect(f'/users/{current_user}')
    db.session.delete(delete_user)
    db.session.commit()
    session.clear()
    return redirect('/register')

@app.route('/feedback/<feedback_id>/update', methods=["GET","POST"])
def edit_feedback(feedback_id):
    if "user_id" not in session:
        flash("Must be logged in to do this.")
        return redirect('/login')
    feedback = Feedback.query.get_or_404(feedback_id)
    if feedback.username != session.get("user_id"):
        flash("You can't edit feedback that isn't yours!")
        return redirect(f'/users/{feedback.username}')
    form = FeedbackForm(obj=feedback)
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.add(feedback)
        db.session.commit()
        return redirect(f'/users/{feedback.username}')
    return render_template('edit_feedback.html', form=form, feedback=feedback)

@app.route('/feedback/<feedback_id>/delete', methods=["GET","POST"])
def delete_feedback(feedback_id):
    if "user_id" not in session:
        flash("Must be logged in to do this.")
        return redirect('/login')
    feedback = Feedback.query.get_or_404(feedback_id)
    if feedback.username != session.get("user_id"):
        flash("You can't delete feedback that isn't yours!")
        return redirect(f'/users/{feedback.username}')
    db.session.delete(feedback)
    db.session.commit()
    username = session.get("user_id")
    return redirect(f'/users/{username}')
    
    