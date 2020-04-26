from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length
from app.models import User, Post
from flask_login import current_user
from app import login

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email')#, validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    user_type = SelectField('What Type of User Are You?',
        choices=[('student', 'Student'), ('school', 'School'), ('company', 'Company')])
    display_name = StringField('Display Name')
    affiliation = StringField('Affiliation')

    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')


class EditProfileForm(FlaskForm):
    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))
    if current_user:
        username = StringField('Username', default=current_user.username, validators=[DataRequired()])
        user_type = SelectField('Who are you?', default=current_user.user_type,
        choices=[('student', 'Student'), ('school', 'University'), 
                ('company', 'Company'), ('pair', 'Paired Univesity-Company')])
        display_name = StringField('Display Name', default=current_user.display_name, validators=[DataRequired()])
        affiliation = TextAreaField('Affiliation', default=current_user.affiliation, validators=[Length(min=0, max=140)])
        about_me = TextAreaField('About me', default=current_user.about_me, validators=[Length(min=0, max=140)])
        submit = SubmitField('Submit')
    else:
        username = StringField('Username', validators=[DataRequired()])
        user_type = SelectField('Which user type fits your current needs?',
        choices=[('student', 'Student'), ('school', 'University'), 
                ('company', 'Company'), ('pair', 'Paired Univesity-Company')])
        display_name = StringField('Display Name', validators=[DataRequired()])
        affiliation = StringField('Affiliation')
        about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])


        submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username. Your original name of {current_user.username} is still available.')


class PostForm(FlaskForm):
    post_title = StringField('Post Title', validators=[DataRequired()])
    body = TextAreaField('Say something', validators=[DataRequired()])
    post_target_type = SelectField('Who is this post for?',
        choices=[('student', 'Students'), ('school', 'Universities'), 
                ('company', 'Companies'), ('pair', 'Paired Univesity-Companies')])
    submit = SubmitField('Submit')


class EditPostForm(FlaskForm):
    post_title = StringField('Post Title',  validators=[DataRequired()])
    body = TextAreaField('Say something',  validators=[DataRequired()])
    post_target_type = SelectField('Who is this post for?', 
        choices=[('student', 'Students'), ('school', 'Universities'), 
                ('company', 'Companies'), ('pair', 'Paired Univesity-Companies')])
    submit = SubmitField('Submit')



