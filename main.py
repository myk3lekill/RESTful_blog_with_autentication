from datetime import date
from functools import wraps

from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_gravatar import Gravatar

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

# U.1 Implement Gravatar for avatar
gravatar = Gravatar(app, size=50, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)


# G.2 Implement the Login Manager method
login_manager = LoginManager()
login_manager.init_app(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

##CONFIGURE TABLE IN DB
class BlogPost(db.Model):
    __tablename__ = "blog_post"
    id = db.Column(db.Integer, primary_key=True)

    # N.2 Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    title = db.Column(db.String(250), unique=True, nullable=False)

    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)

    # N.3 Create reference to the User object, the "posts" refers to the posts protperty in the User class.
    author = relationship("User", back_populates="posts")

    img_url = db.Column(db.String(250), nullable=False)

    # S.1 create a relationship with "parent_post" refers to the "comment_author" property in the Comment class.
    comments = relationship("Comment", back_populates="parent_post")

#Create all the tables in the database (run only first time to create users.db after comment it)
# with app.app_context():
#     db.create_all()

# F.1 Create the User Table to store user's data in DB
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

    # N.1 This will act like a List of BlogPost objects attached to each User. The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")

    # R.1 create a relationship with "comment_author" refers to the "comment_author" property in the Comment class.
    comments = relationship("Comment", back_populates="comment_author")


# F.2 Create all the tables in the database (run only first time to create users.db after comment it)
# with app.app_context():
#     db.create_all()

# Q.1 Create the Comments Table to store user's comments in DB
class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)

    # R.2 Create Foreign Key, "author.id" the users refers to the tablename of User.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # S.2 Create Foreign Key, "post.id" the users refers to the tablename of User.
    post_id = db.Column(db.Integer, db.ForeignKey("blog_post.id"))

    text = db.Column(db.Text, nullable=False)

    # R.3 create a relationship with "comments" witch refers to the "comments" property in the User class.
    comment_author = relationship("User", back_populates="comments")
    # S.3 Create a relationship with "comments" witch refers to the "comments" property in the BlogPost class.
    parent_post = relationship("BlogPost", back_populates="comments")
# S.4 Create all the tables in the database (run only first time to create users.db after comment it)
with app.app_context():
    db.create_all()

##WTForm (IMPORTED from forms.py)
# class CreatePostForm(FlaskForm):
#     title = StringField("Blog Post Title", validators=[DataRequired()])
#     subtitle = StringField("Subtitle", validators=[DataRequired()])
#     author = StringField("Your Name", validators=[DataRequired()])
#     img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
#     # B.9 implement CKEditor package to use the Flask CKEditor package to make Blog Content (body) input in the WTForm into a full CKEditor.
#     body = CKEditorField("Blog Content", validators=[DataRequired()])
#     submit = SubmitField("Submit Post")


# M.1 Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def get_all_posts():
    # A.1 READ ALL RECORDS FORM DATABASE posts.db AND RENDER THEM INTO THE INDEX TEMPLATE.
    posts = db.session.query(BlogPost).all()
    # I.2 Pass the current_user over to the template if it is authenticated. Current_user.is_authenticated will be True if they are logged in/authenticated after registering.
    return render_template("index.html", all_posts=posts, current_user=current_user)

# A.2 RENDER EACH POST FROM DATABASE posts.db IN NEW HTTP PAGES USING INDEX AS POST_ID.
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    # P.3 Set the form we are going to use with the show_post method for user's comments
    form = CommentForm()
    # A.3 Render posts based on id using "DB.query.get"
    requested_post = BlogPost.query.get(post_id)
    # T.1 Implement if statement for comment form's validation on submit and another if statement for check if current user is logged in
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for('login'))
        new_comment = Comment(
            text=form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        # T.2 Add comment to DB
        db.session.add(new_comment)
        db.session.commit()
    # P.3 Export comment_for as an external variable called form
    # T.3 return current_user as external variable
    return render_template("post.html", post=requested_post, form=form, current_user=current_user)

# B.1 CREATE POSTS. TO CREATE A NEW POST WE HAVE TO IMPLEMENT GET AND POST METHODS AND WE HAVE TO IMPLEMENT A WTF FORM "CreatePostForm" IN main.py
@app.route("/new-post", methods=["GET","POST"])
# M.2 Add Admin decorator
@admin_only
def make_post():
    # B.2 Set the form we are going to use with the make_post method
    form = CreatePostForm()
    # C.1 ADD NEW POST TO THE posts.db
    # C.2 Verify if user make a POST request and if the request is valid.
    if form.validate_on_submit():
        # C.3 Parameters to validate on submit
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            # M.4 set author as current user
            author=current_user,
            # C.4 Using date module catch today date in the format of month day year
            date=date.today().strftime("%B %d, %Y")
        )
        # C.5 Add new_post to posts.db
        db.session.add(new_post)
        db.session.commit()
        # C.6 after adding new post to posts.db redirect to get_all_posts url (index.html)
        return redirect(url_for("get_all_posts"))
    # B.3 export the form as a variable
    # I.3 Pass the current_user over to the template if it is authenticated. Current_user.is_authenticated will be True if they are logged in/authenticated after registering.
    return render_template("make-post.html", form=form, current_user=current_user)
# B.4 In make-post.html import the flask form using prebuilt bootstrap forms

# D.1 EDIT EACH POST. TO EDIT EACH POST WE HAVE TO IMPLEMENT GET AND POST METHODS
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
# I.8 Require login to edit posts
#@login_required
# M.3 Add Admin decorator
@admin_only
def edit_post(post_id):
    # D.2 Get correspondant post in the posts.db to the post_id params
    post = BlogPost.query.get(post_id)
    # D.3 Create a Form to edit each posts in post.db
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=current_user,
        body=post.body
    )
    # D.10 Validate on submit the edit_form to verify if user make a POST request and if the request is valid.
    if edit_form.validate_on_submit():
        # D.11 Parameters to validate on submit
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        # post.author = edit_form.author.data
        post.body = edit_form.body.data
        # D.12 Edit post to posts.db
        db.session.commit()
        # D.13 after edit post in posts.db redirect to show_post (post.html) based on the post_id
        return redirect(url_for("show_post", post_id=post.id))
    # I.4 Pass the current_user over to the template if it is authenticated. Current_user.is_authenticated will be True if they are logged in/authenticated after registering.
    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user)

# E.1 DELETE EACH POST SELECTED.
@app.route("/delete/<int:post_id>")
# M.4 Add Admin decorator
@admin_only
def delete_post(post_id):
    # E.2 Store post_id of selected post into a variable called post_to_delete
    post_to_delete = BlogPost.query.get(post_id)
    # E.3 Delete selected post from posts.db
    db.session.delete(post_to_delete)
    db.session.commit()
    # E.4 After deleting selected post redirect to all posts
    return redirect(url_for('get_all_posts'))

@app.route('/delete_comment/<int:comment_id>/<int:post_id>')
@login_required
@admin_only
def delete_comment(comment_id, post_id):
    comment_to_delete = Comment.query.get(comment_id)
    db.session.delete(comment_to_delete)
    db.session.commit()
    return redirect(url_for('show_post', post_id=post_id))

@app.route("/about")
def about():
    # I.5 Pass the current_user over to the template if it is authenticated. Current_user.is_authenticated will be True if they are logged in/authenticated after registering.
    return render_template("about.html", current_user=current_user)


@app.route("/contact")
def contact():
    # I.6 Pass the current_user over to the template if it is authenticated. Current_user.is_authenticated will be True if they are logged in/authenticated after registering.
    return render_template("contact.html", current_user=current_user)

# F.3 Register new users into User database
@app.route("/register", methods=["GET", "POST"])
def register():
    # F.4 Import Register Form to store user's data into database
    form = RegisterForm()
    # F.5 Use Validate data on submit method for the form
    if form.validate_on_submit():
        # F.6 Hash and salt the password imputed by user
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        # F.7 Create the nwe_user from User form
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        # F.8 Add the new user to the db
        db.session.add(new_user)
        db.session.commit()

        # F.9 Login and authenticate user after adding details to database. (This line will authenticate the user with Flask-Login)
        login_user(new_user)

        # F.10 redirect loggedin user to index.html
        return redirect(url_for("get_all_posts"))
    # F.11 Export RegisterForm form stored in the form variable as an external variable to use it in register.html
    # I.6 Pass the current_user over to the template if it is authenticated. Current_user.is_authenticated will be True if they are logged in/authenticated after registering.
    return render_template("register.html", form=form, current_user=current_user)


# G.3 Use the Flask load_manager.user_loader decorating function to check what userID is in the current session and will load the user object for that id.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# G.4 Login users
@app.route("/login", methods=["GET", "POST"])
def login():
    # G.5 Import Login Form to read user's data from database
    form = LoginForm()
    # G.6 Use Validate data on submit method for the form
    if form.validate_on_submit():
        # G.7 Validate email and password on submit
        email = form.email.data
        password = form.password.data

        # G.8 Search Filter and select user by email in database
        user = User.query.filter_by(email=email).first()

        # G.9 If user and password is checked login the user and redirect it to index.html
        # if user and check_password_hash(user.password, password):
        #     login_user(user)
        #     return redirect(url_for('get_all_posts'))

        # H.1 If email doesn't exist flash a message and redirect user to /login route
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # H.2 If Password is incorrect flash a message and redirect user to /login route
        elif not check_password_hash(user.password, password):
            flash("Password incorrect, please try again")
            return redirect(url_for('login'))
        # H.3 If User and password exist login the user and redirect user to /index route
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))
    # G.10 Export LoginForm form stored in the form variable as an external variable to use it in login.html
    # I.7 Pass the current_user over to the template if it is authenticated. Current_user.is_authenticated will be True if they are logged in/authenticated after registering.
    return render_template("login.html", form=form, current_user=current_user)

#H.4 Implement logout method
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))

if __name__ == "__main__":
    app.run(port=5000, debug=True)