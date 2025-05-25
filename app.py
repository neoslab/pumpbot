# Import libraries
import datetime
import os
import uuid
import sys
import yaml

# Import packages
from functools import wraps
from flask import Flask
from flask import flash
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask_wtf import CSRFProtect

# Import dependencies
from utils.fields import BotFields
from utils.forms import BotForm
from utils.forms import EndpointForm
from utils.forms import LoginForm
from utils.forms import WalletForm
from utils.serialization import QuotedDumper


# Class 'PumpBotUI'
class PumpBotUI:
    """ Class description """
    
    # Class initialization
    def __init__(self):
        """ Initializer description """
        basedir = os.path.abspath(os.path.dirname(__file__))
        self.app = Flask(__name__, template_folder=os.path.join(basedir, 'templates'))
        self.app.secret_key = 'supersecretkey'
        self.csrf = CSRFProtect(self.app)
        self.botsdir = 'bots'
        self.userfile = 'config/user.yaml'
        self.routes()
        self.app.context_processor(self.injectglobals)
        os.makedirs(self.botsdir, exist_ok=True)

    # Function 'injectglobals'
    @staticmethod
    def injectglobals():
        """ Function description """
        return {
            'projectname': 'PumpBot',
            'projectvers': '4.0',
        }

    # Function 'formatdata'
    @staticmethod
    def formatdata(flatdata):
        """ Function description """
        result = {}
        for key, value in flatdata.items():
            if key in ('filename', 'csrf_token'):
                continue

            keys = key.split('.')
            refs = result
            for k in keys[:-1]:
                refs = refs.setdefault(k, {})

            val = value[0] if len(value) == 1 else value
            if val in ('True', 'False'):
                val = val == 'True'
            elif val in ('None', 'Null'):
                val = None
            else:
                try:
                    val = float(val) if '.' in val else int(val)
                except (ValueError, TypeError):
                    pass
            refs[keys[-1]] = val
        return result

    # Function 'loaduser'
    def loaduser(self):
        """ Function description """
        with open(self.userfile, 'r') as f:
            return yaml.safe_load(f)

    # Function 'loadsession'
    @staticmethod
    def loadsession(f):
        """ Function description """

        # Function 'checksession'
        @wraps(f)
        def checksession(*args, **kwargs):
            """ Function description """
            if 'user' not in session:
                return redirect(url_for('login'))

            return f(*args, **kwargs)
        return checksession

    # Function 'routes'
    def routes(self):
        """ Function description """
        app = self.app

        # Function 'add'
        @app.route('/add', methods=['GET', 'POST'], endpoint='add')
        @self.loadsession
        def add():
            """ Function description """
            form = BotForm()
            if form.validate_on_submit():
                filename = form.filename.data
                data = request.form.to_dict(flat=False)
                cleandata = self.formatdata(data)
                filepath = os.path.join(self.botsdir, filename if filename.endswith('.yaml') else filename + '.yaml')
                QuotedDumper.dumpyaml(filepath, cleandata)
                flash('Bot successfully created', 'success')
                return redirect(url_for('bots'))

            with open('model/bot.yaml', 'r') as f:
                content = yaml.safe_load(f)
            return render_template('edit.html', form=form, data=content, filename='', metadata=BotFields().getfields(), title='Add Bot', mode='add')

        # Function 'bots'
        @app.route('/bots')
        @self.loadsession
        def bots():
            """ Function description """
            files = [f for f in os.listdir(self.botsdir) if f.endswith('.yaml')]
            return render_template('bots.html', files=files, title='Bots')

        # Function 'changelog'
        @app.route('/changelog')
        @self.loadsession
        def changelog():
            """ Function description """
            return render_template('changelog.html', title='Changelog')

        # Function 'delete'
        @app.route('/delete/<filename>', methods=['GET', 'POST'], endpoint='delete')
        @self.loadsession
        def delete(filename):
            """ Function description """
            path = os.path.join(self.botsdir, filename)

            if os.path.exists(path):
                os.remove(path)
                flash('Bot successfully deleted', 'success')

            return redirect(url_for('bots'))

        # Function 'endpoint'
        @app.route('/endpoint', methods=['GET', 'POST'])
        @self.loadsession
        def endpoint():
            """ Function description """
            form = EndpointForm()
            filepath = os.path.join('config', 'endpoint.yaml')

            filedata = {}
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    filedata = yaml.safe_load(f) or {}

            if request.method == 'GET':
                form.rpc.data = filedata.get('rpc', '')
                form.wss.data = filedata.get('wss', '')
                form.api.data = filedata.get('api', '')

            if form.validate_on_submit():
                data = {
                    'rpc': form.rpc.data.strip(),
                    'wss': form.wss.data.strip(),
                    'api': form.api.data.strip()
                }

                try:
                    with open(filepath, 'w'):
                        cleandata = self.formatdata(data)
                        QuotedDumper.dumpyaml(filepath, cleandata)
                    flash("Endpoint configuration saved successfully.", "success")
                except Exception as e:
                    flash(f"Failed to save configuration: {e}", "danger")

                return redirect(url_for('endpoint'))

            return render_template('endpoint.html', form=form, title='Endpoint')

        # Function 'home'
        @app.route('/home')
        @self.loadsession
        def home():
            """ Function description """
            botfiles = []
            for filename in os.listdir(self.botsdir):

                if filename.endswith('.yaml'):
                    filepath = os.path.join(self.botsdir, filename)

                    try:
                        with open(filepath, 'r') as f:
                            config = yaml.safe_load(f)
                            enabled = config.get('main', {}).get('enabled', False)
                    except (ValueError, TypeError):
                        enabled = False
                    botfiles.append({'filename': filename, 'enabled': enabled, 'id': f"switch_{uuid.uuid4().hex[:8]}"})
            return render_template('home.html', files=botfiles, title='Dashboard')

        # Function 'login'
        @app.route('/', methods=['GET', 'POST'])
        def login():
            """ Function description """
            form = LoginForm()
            creds = self.loaduser()

            if form.validate_on_submit():
                if form.username.data == creds['username'] and form.password.data == creds['password']:
                    session['user'] = form.username.data
                    return redirect(url_for('home'))

                flash('Invalid username and/or password', 'danger')
            return render_template('login.html', form=form, title='Login')

        # Function 'logout'
        @app.route('/logout')
        def logout():
            """ Function description """
            session.clear()
            flash('You have been logged out successfully.', 'success')
            return redirect(url_for('login'))

        # Function 'logs'
        @app.route('/logs')
        @self.loadsession
        def logs():
            """ Function description """
            logflask = False
            try:
                with open('logs/flask.log', 'r', encoding='utf-8') as f:
                    lines = [line.lstrip().rstrip('\n') for line in f if line.strip()]
                    logflask = '\n'.join(lines)
            except FileNotFoundError:
                logflask = 'File not found'
            except Exception as e:
                logflask = f'Error while reading log file : {str(e)}'

            return render_template('logs.html', title='Logs', logflask=logflask)

        # Function 'scanner'
        @app.route('/scanner')
        @self.loadsession
        def scanner():
            """ Function description """
            return render_template('scanner.html', title='Scanner')

        # Function 'switch'
        @app.route('/switch', methods=['POST'])
        @self.loadsession
        def switch():
            """ Function description """
            data = request.get_json()
            filename = data.get('filename')
            status = data.get('status')
            filepath = os.path.join(self.botsdir, filename)

            if not os.path.isfile(filepath):
                return jsonify({'error': 'File not found'}), 404

            try:
                with open(filepath, 'r') as f:
                    config = yaml.safe_load(f) or {}
                config.setdefault('main', {})['status'] = bool(status)
                QuotedDumper.dumpyaml(filepath, config)
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # Function 'trades'
        @app.route('/trades')
        @self.loadsession
        def trades():
            """ Function description """
            return render_template('trades.html', title='Trades')

        # Function 'update'
        @app.route('/update/<filename>', methods=['GET', 'POST'], endpoint='update')
        @self.loadsession
        def update(filename):
            """ Function description """
            filepath = os.path.join(self.botsdir, filename)
            form = BotForm(filename=filename)

            if form.validate_on_submit():
                data = request.form.to_dict(flat=False)
                cleandata = self.formatdata(data)
                QuotedDumper.dumpyaml(filepath, cleandata)
                flash('Bot successfully updated', 'success')
                return redirect(url_for('bots'))

            with open(filepath, 'r') as f:
                content = yaml.safe_load(f)
            return render_template('edit.html', form=form, data=content, filename=filename, metadata=BotFields().getfields(), title='Update Bot', mode='update')

        # Function 'wallet'
        @app.route('/wallet', methods=['GET', 'POST'])
        @self.loadsession
        def wallet():
            """ Function description """
            form = WalletForm()
            filepath = os.path.join('config', 'wallet.yaml')

            filedata = {}
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    filedata = yaml.safe_load(f) or {}

            if request.method == 'GET':
                form.publicaddr.data = filedata.get('publicaddr', '')
                form.privatekey.data = filedata.get('privatekey', '')

            if form.validate_on_submit():
                data = {
                    'publicaddr': form.publicaddr.data.strip(),
                    'privatekey': form.privatekey.data.strip()
                }

                try:
                    with open(filepath, 'w'):
                        cleandata = self.formatdata(data)
                        QuotedDumper.dumpyaml(filepath, cleandata)
                    flash("Wallet configuration saved successfully.", "success")
                except Exception as e:
                    flash(f"Failed to save wallet: {e}", "danger")

                return redirect(url_for('wallet'))

            return render_template('wallet.html', form=form, title='Wallet')

    # Function 'run'
    def run(self, host='0.0.0.0', port=5002, debug=True):
        """ Function description """
        basedir = os.path.abspath(os.path.dirname(__file__))
        logdir = os.path.join(basedir, 'logs')
        os.makedirs(logdir, exist_ok=True)

        logfile = os.path.join(logdir, 'flask.log')
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(logfile, 'a') as f:
             f.write(f"\n\n--- Flask App Started at {timestamp} ---\n")

        sys.stdout = open(logfile, 'a')
        sys.stderr = sys.stdout
        self.app.run(host=host, port=port, debug=debug)