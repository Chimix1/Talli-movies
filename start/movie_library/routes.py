import uuid
import datetime
import functools
import os
from flask import Blueprint, render_template, session, redirect, request, current_app, url_for, flash
from dataclasses import asdict
from movie_library.forms import MovieForm, ExtendedMovieForm, RegisterForm, LoginForm, ProfileForm
from movie_library.models import Movie, User
from werkzeug.utils import secure_filename
from passlib.hash import pbkdf2_sha256

pages = Blueprint(
    "pages", __name__, template_folder="templates", static_folder="static"
)


def login_required(route):
    @functools.wraps(route)
    def route_wrapper(*args, **kwargs):
        if session.get("email") is None:
            return redirect(url_for(".login"))

        return route(*args, **kwargs)

    return route_wrapper



@pages.route("/", methods=["GET", "POST"])
@login_required
def index():
    user_data = current_app.db.user.find_one({"email": session["email"]})
    user = User(**user_data)

    # Get the search term from the request (if any)
    search_query = request.args.get("search")

    # If there is a search term, filter movies based on it
    if search_query:
        # Search by title, director, or any other field you need to filter
        movie_data = current_app.db.movie.find({
            "$or": [
                {"title": {"$regex": search_query, "$options": "i"}},  # Case-insensitive search for title
                {"director": {"$regex": search_query, "$options": "i"}}  # Case-insensitive search for director
            ]
        })
    else:
        # No search term, just fetch all movies in the user's list
        movie_data = current_app.db.movie.find({"_id": {"$in": user.movies}})

    # Convert the movie data to Movie objects
    movies = [Movie(**movie) for movie in movie_data]

    return render_template(
        "index.html",
        title="Movies Watchlist",
        movies_data=movies,
    )


@pages.route("/register", methods=["POST", "GET"])
def register():
    if session.get("email"):
        return redirect(url_for(".index"))

    form = RegisterForm()

    if form.validate_on_submit():
        user = User(
            _id=uuid.uuid4().hex,
            name=form.name.data,
            address=form.address.data,
            email=form.email.data,
            password=pbkdf2_sha256.hash(form.password.data),
        )

        current_app.db.user.insert_one(asdict(user))

        flash("User registered successfully", "success")

        return redirect(url_for(".login"))

    return render_template(
        "register.html", title="Movies Watchlist - Register", form=form
    )


@pages.route("/login", methods=["GET", "POST"])
def login():
    if session.get("email"):
        return redirect(url_for(".index"))

    form = LoginForm()

    if form.validate_on_submit():
        user_data = current_app.db.user.find_one({"email": form.email.data})
        if not user_data:
            flash("Login credentials not correct", category="danger")
            return redirect(url_for(".login"))
        user = User(**user_data)

        if user and pbkdf2_sha256.verify(form.password.data, user.password):
            session["user_id"] = user._id
            session["email"] = user.email

            return redirect(url_for(".index"))

        flash("Login credentials not correct", category="danger")

    return render_template("login.html", title="Movies Watchlist - Login", form=form)


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@pages.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    # Fetch the user's data from the database
    user_data = current_app.db.user.find_one({"email": session["email"]})
    user = User(**user_data)
    
    # Initialize the profile form with the user's existing data
    form = ProfileForm(obj=user)

    if form.validate_on_submit():
        # Update user information
        user.name = form.name.data
        user.address = form.address.data
        
        # Update password only if a new password is provided
        if form.password.data:
            user.password = pbkdf2_sha256.hash(form.password.data)

        # Handle profile picture upload if there's a new one
        if "profile_picture" in request.files:
            file = request.files["profile_picture"]
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                
                # Generate a unique filename using UUID to avoid collisions
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)

                # Check if the user already has a profile picture
                if user.profile_picture:
                    # Delete the old profile picture file if it exists
                    old_picture_path = os.path.join(current_app.config["UPLOAD_FOLDER"], user.profile_picture)
                    if os.path.exists(old_picture_path):
                        os.remove(old_picture_path)

                # Ensure the upload folder exists
                if not os.path.exists(current_app.config["UPLOAD_FOLDER"]):
                    os.makedirs(current_app.config["UPLOAD_FOLDER"])

                # Save the new profile picture
                file.save(filepath)
                # Update the user's profile picture field with the new filename
                user.profile_picture = unique_filename

        # Save the updated user data in the database
        current_app.db.user.update_one({"_id": user._id}, {"$set": user.to_dict()})

        flash("Profile updated successfully", "success")
        return redirect(url_for(".profile"))
    
    return render_template("profile.html", form=form, title="Update Profile", user=user)


@pages.route("/logout")
def logout():
    current_theme = session.get("theme")
    session.clear()
    session["theme"] = current_theme

    return redirect(url_for(".index"))


@pages.route("/add", methods=["GET", "POST"])
@login_required
def add_movie():
    form = MovieForm()

    if form.validate_on_submit():
        movie = Movie(
            _id=uuid.uuid4().hex,
            title=form.title.data,
            director=form.director.data,
            year=form.year.data,
        )

        current_app.db.movie.insert_one(asdict(movie))
        current_app.db.user.update_one(
            {"_id": session["user_id"]}, {"$push": {"movies": movie._id}}
        )

        return redirect(url_for(".movie", _id=movie._id))

    return render_template(
        "new_movie.html", 
        title="Movies Watchlist - Add Movie", 
        form=form
    )


@pages.route("/edit/<string:_id>", methods=["GET", "POST"])
@login_required
def edit_movie(_id: str):
    movie = Movie(**current_app.db.movie.find_one({"_id": _id}))
    form = ExtendedMovieForm(obj=movie)
    if form.validate_on_submit():
        movie.title = form.title.data
        movie.director = form.director.data
        movie.year = form.year.data
        movie.cast = form.cast.data
        movie.series = form.series.data
        movie.tags = form.tags.data
        movie.description = form.description.data
        movie.video_link = form.video_link.data

        current_app.db.movie.update_one({"_id": movie._id}, {"$set": asdict(movie)})
        return redirect(url_for(".movie", _id=movie._id))
    return render_template("movie_form.html", movie=movie, form=form)


@pages.get("/movie/<string:_id>")
def movie(_id: str):
    movie = Movie(**current_app.db.movie.find_one({"_id": _id}))
    return render_template("movie_details.html", movie=movie)


@pages.get("/movie/<string:_id>/rate")
@login_required
def rate_movie(_id):
    rating = int(request.args.get("rating"))
    current_app.db.movie.update_one({"_id": _id}, {"$set": {"rating": rating}})

    return redirect(url_for(".movie", _id=_id))


@pages.get("/movie/<string:_id>/watch")
@login_required
def watch_today(_id):
    current_app.db.movie.update_one(
        {"_id": _id}, {"$set": {"last_watched": datetime.datetime.today()}}
    )

    return redirect(url_for(".movie", _id=_id))


@pages.get("/toggle-theme")
def toggle_theme():
    current_theme = session.get("theme")
    if current_theme == "dark":
        session["theme"] = "light"
    else : 
        session["theme"] = "dark"

    return redirect(request.args.get("current_page"))