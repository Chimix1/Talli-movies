from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SubmitField, TextAreaField, URLField, PasswordField
from wtforms.validators import InputRequired, NumberRange, Email, EqualTo, Length

class MovieForm(FlaskForm):
    title = StringField("Title", validators=[InputRequired()])
    director = StringField("Director", validators=[InputRequired()])

    year = IntegerField(
        "Year",
        validators=[
            InputRequired(),
            NumberRange(min=1878, message="Please enter a year in the format YYYY."),
        ],
    )

    submit = SubmitField("Add Movie")

class StringListField(TextAreaField):
    def _value(self):
        if self.data:
            return "\n".join(self.data)
        else:
            return ""

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            self.data = [line.strip() for line in valuelist[0].split("\n")]
        else:
            self.data = []

class ExtendedMovieForm(MovieForm):
    cast = StringListField("Cast")
    series = StringListField("Series")
    tags = StringListField("Tags")
    description = TextAreaField("Description")
    video_link = URLField("Video link")

    submit = SubmitField("Submit")

class RegisterForm(FlaskForm):
    name = StringField(
        "Name",
        validators=[
            InputRequired(message="Your name is required."),
            Length(
                min=2,
                max=50,
                message="Name must be between 2 and 50 characters long.",
            ),
        ],
    )
    address = TextAreaField(
        "Address",
        validators=[
            InputRequired(message="Your address is required."),
            Length(
                max=200,
                message="Address cannot exceed 200 characters.",
            ),
        ],
    )
    email = StringField("Email", validators=[InputRequired(), Email()])
    
    password = PasswordField(
        "Password",
        validators=[
            InputRequired(),
            Length(
                min=4,
                message="Your password must be minimum 4 characters long.",
            ),
        ],
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            InputRequired(),
            EqualTo(
                "password",
                message="This password did not match the one in the password field.",
            ),
        ],
    )

    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password", validators=[InputRequired()])
    submit = SubmitField("Login")

class ProfileForm(FlaskForm):
    name = StringField("Name", validators=[InputRequired()])
    email = StringField("Email", render_kw={"readonly": True}, validators=[InputRequired(), Email()])
    address = StringField("Address", validators=[InputRequired()])
    password = PasswordField(
        "New Password (Optional)",
        validators=[Length(min=4, message="Password must be at least 4 characters long.")],
    )
    submit = SubmitField("Save Changes")

    