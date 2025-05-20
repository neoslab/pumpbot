# Import packages
from flask_wtf import FlaskForm
from wtforms import PasswordField
from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import DataRequired


# Class 'BotForm'
class BotForm(FlaskForm):
    """
    This class defines a web form used for creating or updating bot configuration files in the application.
    It inherits from FlaskForm and provides a filename input and a submit button. The form ensures that
    the filename is always provided before submission using built-in validators. It is primarily used
    in the add and update views to handle user input and drive file persistence operations.

    Parameters:
    - filename (wtforms.StringField): Input field to receive the bot configuration filename. Required.
    - submit (wtforms.SubmitField): A standard submit button to send form data.

    Returns:
    - None
    """
    filename = StringField('Filename', validators=[DataRequired()])
    submit = SubmitField('Save')


# Class 'LoginForm'
class LoginForm(FlaskForm):
    """
    This class defines the login form used to authenticate users within the web application. It includes
    input fields for username and password, both of which are required via the `DataRequired` validator.
    The class inherits from FlaskForm, enabling CSRF protection and Flask-WTF integration. This form
    is used in the login route to verify user credentials and grant access to authenticated sessions.

    Parameters:
    - username (wtforms.StringField): Input field to capture the username. Required.
    - password (wtforms.PasswordField): Input field to capture the password securely. Required.
    - submit (wtforms.SubmitField): A button used to submit the login form.

    Returns:
    - None
    """
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')