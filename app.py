# Import libraries
import os
import uuid
import yaml

# Import packages
from flask import flash
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask_wtf import CSRFProtect
from functools import wraps

# Import local packages
from meta import fields
from utils.forms import BotForm
from utils.forms import LoginForm
from utils.yaml import SaveYAML

# Define 'app'
app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Define 'csrf'
csrf = CSRFProtect(app)

# Define 'botsdir'
botsdir = 'bots'
os.makedirs(botsdir, exist_ok=True)

# Define 'userfile'
userfile = 'user.yaml'


# Function 'injectglobals'
@app.context_processor
def injectglobals():
    """
    This function is a Flask context processor that injects global variables into the Jinja2 template context.
    It is automatically called during the rendering of each template and ensures that all templates have access
    to predefined global variables without requiring explicit passage through render_template. This is particularly
    useful for values such as the application name, global branding identifiers, or reusable constants.

    Parameters:
    - None

    Returns:
    - dict: A dictionary of key-value pairs where each key becomes a global variable in all templates.
            In this implementation, it returns {'projectname': 'PumpBot'}, making 'projectname' available
            for direct use in any rendered template, including base layouts or partials.
    """
    return {
        'projectname': 'PumpBot',
        'projectvers': '4.0',
    }


# Function 'loaduser'
def loaduser():
    """
    Loads user credentials from a local YAML file and returns them as a Python dictionary.
    This function is typically used in authentication workflows to validate login input
    against predefined values stored in the `user.yaml` configuration file. It reads the
    file using PyYAML and is expected to return keys such as 'username' and 'password'.

    Parameters:
    - None

    Returns:
    - dict: A dictionary containing user credentials loaded from the YAML file.
    """
    with open(userfile, 'r') as f:
        return yaml.safe_load(f)


# Function 'login_required'
def loadsession(f):
    """
    A Flask decorator used to enforce user authentication on protected routes.
    It wraps route functions and checks if a valid session exists for the user.
    If no session is detected (i.e., the user is not logged in), the decorator
    will redirect to the login page, ensuring security across the application.

    Parameters:
    - f (function): The Flask route handler being protected by the session check.

    Returns:
    - function: A wrapped version of the input function that performs session validation.
    """
    @wraps(f)
    # Function 'decorated'
    def decorated(*args, **kwargs):
        """
        Internal function used within the authentication decorator to verify access.
        It examines whether the current session contains a 'user' key, which indicates
        a valid login. If not, it triggers a redirect to the login page; otherwise,
        it allows the route logic to continue normally as expected.

        Parameters:
        - *args: Positional arguments passed to the wrapped route.
        - **kwargs: Keyword arguments passed to the wrapped route.

        Returns:
        - Response: A Flask redirect response or the result of the wrapped function.
        """
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# Function 'add'
@app.route('/add', methods=['GET', 'POST'], endpoint='add')
@loadsession
def add():
    """
    This function handles the creation of new bot configurations via a web form interface.
    It renders a form for user input, processes the submitted data, converts it to a nested
    dictionary structure suitable for YAML, and then saves it to the bots directory with a
    `.yaml` extension. If the submission is valid, the user is redirected with a success message.

    Parameters:
    - None (Inputs are handled via Flask's request context and a predefined form instance)

    Returns:
    - Response object (Flask `redirect` or `render_template`) that either redirects to the
      bots page after saving the file or re-renders the form page with a sample template.
    """
    form = BotForm()
    if form.validate_on_submit():
        filename = form.filename.data
        data = request.form.to_dict(flat=False)
        cleandata = datanested(data)
        path = os.path.join(botsdir, filename if filename.endswith('.yaml') else filename + '.yaml')
        with open(path, 'w') as f:
            SaveYAML(path, cleandata)
        flash('Bot successfully created', 'success')
        return redirect(url_for('bots'))
    with open('model.yaml', 'r') as f:
        content = yaml.safe_load(f)
    return render_template('edit.html', form=form, data=content, filename='', metadata=fields, title='Add Bot', mode='add')


# Function 'bots'
@app.route('/bots')
@loadsession
def bots():
    """
    Displays a list of YAML bot configuration files available in the application.
    This route is protected by session authentication and is only accessible to
    logged-in users. It filters files in the 'bots' directory ending in '.yaml'
    and renders them in a visual list on the homepage for easy selection.

    Parameters:
    - None

    Returns:
    - Response: Renders 'bots.html' with a list of YAML configuration files.
    """
    files = [f for f in os.listdir(botsdir) if f.endswith('.yaml')]
    return render_template('bots.html', files=files, title='Bots')


# Function 'changelog'
@app.route('/changelog')
@loadsession
def changelog():
    """
    This function defines a protected Flask route responsible for rendering the changelog page of the application.
    It is only accessible to authenticated users, as enforced by the `@loadsession` decorator. The primary purpose
    of this route is to present a view displaying recent updates, version changes, new features, or fixes applied
    to the platform. This helps users track the evolution of the system and remain informed about important changes.

    Parameters:
    - None

    Returns:
    - Response (flask.Response): Returns the rendered HTML content of the 'changelog.html' template, including
      a contextual variable 'title' set to 'Changelog' which can be used in the template to dynamically set the page title.
    """
    return render_template('changelog.html', title='Changelog')


# Function 'delete'
@app.route('/delete/<filename>', methods=['GET', 'POST'], endpoint='delete')
@loadsession
def delete(filename):
    """
    Deletes a specific YAML file from the bots configuration directory. Before
    deletion, it checks if the file exists to avoid runtime errors. This action
    is protected and only available to logged-in users. It ensures data cleanup
    when users no longer need a particular bot configuration.

    Parameters:
    - filename (str): Name of the YAML file to be deleted from the bots folder.

    Returns:
    - Response: Redirect to home page after deletion or if file doesn’t exist.
    """
    path = os.path.join(botsdir, filename)
    if os.path.exists(path):
        os.remove(path)
        flash('Bot successfully deleted', 'success')
    return redirect(url_for('bots'))


# Function 'home'
@app.route('/home')
@loadsession
def home():
    """
    This function serves as the main dashboard view for the application, displaying all available
    bot configuration files stored in the bots directory. It scans the directory for `.yaml` files,
    loads each file safely, extracts whether the bot is enabled, and generates a unique identifier
    for each entry to support frontend interactivity. The collected data is then passed to a template
    for rendering the dashboard view.

    Parameters:
    - None (All inputs are derived from the server environment and internal file system scanning)

    Returns:
    - Response object (Flask `render_template`) that renders the 'home.html' template with a list
      of bot file summaries, each including the filename, enabled status, and a unique DOM element ID.
    """
    botfiles = []
    for filename in os.listdir(botsdir):
        if filename.endswith('.yaml'):
            filepath = os.path.join(botsdir, filename)
            try:
                with open(filepath, 'r') as f:
                    config = yaml.safe_load(f)
                    enabled = config.get('main', {}).get('enabled', False)
            except Exception as e:
                enabled = False
            botfiles.append({'filename': filename, 'enabled': enabled, 'id': f"switch_{uuid.uuid4().hex[:8]}"})
    return render_template('home.html', files=botfiles, title='Dashboard')


# Function 'login'
@app.route('/', methods=['GET', 'POST'])
def login():
    """
    This function handles user authentication by rendering and processing the login form located
    at the root URL. It loads credentials from a secure storage mechanism, validates user input
    from the `LoginForm`, and checks the submitted credentials against the stored ones. Upon
    successful authentication, it stores the user in the session and redirects to the dashboard.
    If authentication fails, an error message is displayed and the form is re-rendered.

    Parameters:
    - None (The function uses Flask’s `request.form` and a predefined `LoginForm` instance to gather inputs)

    Returns:
    - Response object (Flask `redirect` or `render_template`) that either redirects the authenticated
      user to the home dashboard or displays the login form with error messages.
    """
    form = LoginForm()
    creds = loaduser()
    if form.validate_on_submit():
        if form.username.data == creds['username'] and form.password.data == creds['password']:
            session['user'] = form.username.data
            return redirect(url_for('home'))
        flash('Invalid username and/or password', 'danger')
    return render_template('login.html', form=form, title='Login')


# Function 'logout'
@app.route('/logout')
def logout():
    """
    Logs out the current user by clearing all session data and redirecting to login.
    This function ensures that any sensitive data stored in the session is deleted
    and that the user must re-authenticate before accessing protected routes again.
    It is typically linked from a "Logout" button or link in the user interface.

    Parameters:
    - None

    Returns:
    - Response: Redirect to the login page after clearing session data.
    """
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))


# Function 'logs'
@app.route('/logs')
@loadsession
def logs():
    """
    Displays the logging dashboard for the application, providing insights
    into internal events, debugging messages, or bot activity if integrated.
    Only authenticated users can view logs. The logs are expected to provide
    operational transparency and help during development or monitoring.

    Parameters:
    - None

    Returns:
    - Response: Rendered 'logs.html' template with optional dynamic log data.
    """
    return render_template('logs.html', title='Logs')


# Function 'switch'
@app.route('/switch', methods=['POST'])
@loadsession
def switch():
    """
    This function is responsible for toggling the enabled status of a bot configuration file
    based on user input received via a JSON POST request. It identifies the YAML file by name,
    checks its existence, loads its current configuration, and updates the `enabled` field
    within the `main` section. The updated configuration is then saved back to the file system.
    Errors in reading, parsing, or saving the file result in an appropriate HTTP error response.

    Parameters:
    - None (The function extracts data from a JSON payload using Flask's `request.get_json()`.
      Expected keys include 'filename' (str) and 'enabled' (bool/int))

    Returns:
    - Flask `jsonify` response (dict): A JSON object with either a success status or an error message.
      Returns HTTP 200 on success, 404 if the file is not found, or 500 in case of other exceptions.
    """
    data = request.get_json()
    filename = data.get('filename')
    enabled = data.get('enabled')
    filepath = os.path.join(botsdir, filename)
    if not os.path.isfile(filepath):
        return jsonify({'error': 'File not found'}), 404
    try:
        with open(filepath, 'r') as f:
            config = yaml.safe_load(f) or {}
        if 'main' not in config:
            config['main'] = {}
        config['main']['enabled'] = bool(enabled)
        with open(filepath, 'w') as f:
            yaml.dump(config, f, sort_keys=False)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Function 'trades'
@app.route('/trades')
@loadsession
def trades():
    """
    Displays a basic page for trade-related operations or monitoring.
    This route is a placeholder for any logic or interface elements tied
    to live or historical trades. It is accessible only to authenticated
    users, ensuring data visibility is controlled through session state.

    Parameters:
    - None

    Returns:
    - Response: Rendered 'trades.html' template.
    """
    return render_template('trades.html', title='Trades')


# Function 'update'
@app.route('/update/<filename>', methods=['GET', 'POST'], endpoint='update')
@loadsession
def update(filename):
    """
    This function enables users to update the configuration of an existing bot by modifying its
    associated YAML file. It loads the current content of the specified file, presents it in a
    pre-filled form, and upon submission, processes the input into a nested structure suitable
    for YAML serialization. The updated data is saved back to the same file. This function also
    provides user feedback via flash messages and maintains a consistent UI using a shared template.

    Parameters:
    - filename (str): The name of the YAML configuration file to be updated. The file is expected
      to exist in the predefined bots directory.

    Returns:
    - Response object (Flask `redirect` or `render_template`) that either redirects the user to the
      bots overview page after a successful update or re-renders the form with current file content.
    """
    filepath = os.path.join(botsdir, filename)
    form = BotForm(filename=filename)
    if form.validate_on_submit():
        data = request.form.to_dict(flat=False)
        cleandata = datanested(data)
        with open(filepath, 'w') as f:
            SaveYAML(filepath, cleandata)
        flash('Bot successfully updated', 'success')
        return redirect(url_for('bots'))
    with open(filepath, 'r') as f:
        content = yaml.safe_load(f)
    return render_template('edit.html', form=form, data=content, filename=filename, metadata=fields, title='Update Bot', mode='update')


# Function 'datanested'
def datanested(flat_data):
    """
    Converts a dictionary of flat dot-separated keys into a properly nested
    structure. It is designed to process HTML form input where keys like
    'main.option.timeout' should be interpreted as nested dictionaries. The
    function also attempts to auto-cast string values into appropriate types.

    Parameters:
    - flat_data (dict): A dictionary from form data with dot-separated keys.

    Returns:
    - dict: A nested dictionary with typed values (bool, None, int, float, str).
    """
    result = {}
    for key, value in flat_data.items():
        if key == 'filename':
            continue
        keys = key.split('.')
        ref = result
        for k in keys[:-1]:
            ref = ref.setdefault(k, {})
        val = value[0] if len(value) == 1 else value
        if val in ('True', 'False'):
            val = val == 'True'
        elif val == 'None' or val == 'Null':
            val = None
        else:
            try:
                if '.' in val:
                    val = float(val)
                else:
                    val = int(val)
            except:
                pass
        ref[keys[-1]] = val
    return result


# Main callback
if __name__ == '__main__':
    """
    Entry point for launching the Flask application when this script is run directly.
    It initializes the web server in debug mode, enabling live reloading and enhanced
    error output. This mode is useful during development to catch issues early and
    iteratively test new features without restarting the server manually.

    Parameters:
    - None

    Returns:
    - None
    """
    app.run(host='0.0.0.0', port=5000, debug=True)
