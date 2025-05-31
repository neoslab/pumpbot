# Import libraries
import datetime
import os
import psutil
import subprocess
import sys
import uuid
import yaml

# Import packages
from decimal import Decimal
from decimal import InvalidOperation
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
from math import ceil
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

# Import dependencies
from handler.exchange import SolPrice
from utils.fields import BotFields
from utils.forms import BotForm
from utils.forms import EndpointForm
from utils.forms import LoginForm
from utils.forms import WalletForm
from utils.models import PumpBase
from utils.models import PumpTableTokens
from utils.models import PumpTableTrades
from utils.models import PumpTableWallet
from utils.scaler import NumberScaler
from utils.scripts import ScriptUtils
from utils.serialization import QuotedDumper


# Class 'PumpBotUI'
class PumpBotUI:
    """ Class description """

    # Class initialization
    def __init__(self):
        """ Initializer description """
        # Inside __init__(self):
        basedir = os.path.abspath(os.path.dirname(__file__))
        self.app = Flask(__name__, template_folder=os.path.join(basedir, 'templates'))
        self.app.secret_key = 'supersecretkey'
        self.csrf = CSRFProtect(self.app)

        # Bots and user config
        self.botsdir = 'bots'
        self.userfile = 'config/user.yaml'
        os.makedirs(self.botsdir, exist_ok=True)

        # === Trades Database ===
        dbtokendir = os.path.join(basedir, "database")
        os.makedirs(dbtokendir, exist_ok=True)
        dbtokenspath = os.path.join(dbtokendir, "tokens.db")
        dbtokensbase = f"sqlite:///{dbtokenspath}"

        self.tokensengine = create_engine(dbtokensbase)
        PumpBase.metadata.create_all(self.tokensengine)
        self.TokensSession = sessionmaker(bind=self.tokensengine)

        # === Trades Database ===
        dbtradesdir = os.path.join(basedir, "database")
        os.makedirs(dbtradesdir, exist_ok=True)
        dbtradespath = os.path.join(dbtradesdir, "trades.db")
        dbtradesbase = f"sqlite:///{dbtradespath}"

        self.dbtradesengine = create_engine(dbtradesbase)
        PumpBase.metadata.create_all(self.dbtradesengine)
        self.TradesSession = sessionmaker(bind=self.dbtradesengine)

        # === Wallet Database ===
        dbwalletdir = os.path.join(basedir, "database")
        os.makedirs(dbwalletdir, exist_ok=True)
        dbwalletpath = os.path.join(dbwalletdir, "wallet.db")
        dbwalletbase = f"sqlite:///{dbwalletpath}"

        self.dbwalletengine = create_engine(dbwalletbase)
        PumpBase.metadata.create_all(self.dbwalletengine)
        self.WalletSession = sessionmaker(bind=self.dbwalletengine)

        # Flask context + routes
        self.app.context_processor(self.injectglobals)
        self.routes()
        self.app.jinja_env.filters['safedatetime'] = ScriptUtils.safedatetime
        self.app.jinja_env.filters['formatsuffix'] = NumberScaler.formatsuffix

    # Function 'botcheckproc'
    @staticmethod
    def botcheckproc():
        """ Function description """
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if 'bot.py' in cmdline:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False

    # Function 'injectglobals'
    def injectglobals(self):
        """ Function description """
        botstatus = PumpBotUI.botcheckproc()
        sessdbwallet = self.WalletSession()
        try:
            dbwalletdir = os.path.abspath(os.path.dirname(__file__))
            dbwalletpath = os.path.join(dbwalletdir, "database", "wallet.db")
            if not os.path.exists(dbwalletpath):
                return {
                    'projectname': 'PumpBot',
                    'projectvers': '4.0',
                    'walletbalance': '0.000000000',
                    'botstatus': botstatus
                }

            wallet = sessdbwallet.get(PumpTableWallet, 1)
            balance = wallet.balance if wallet and wallet.balance else '0.00'
            sessdbwallet.close()
            return {
                'projectname': 'PumpBot',
                'projectvers': '4.0',
                'walletbalance': balance,
                'botstatus': botstatus
            }

        except SQLAlchemyError:
            return {
                'projectname': 'PumpBot',
                'projectvers': '4.0',
                'walletbalance': '0.000000000',
                'botstatus': botstatus
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

        # Start Bot Status
        @app.route('/api/botstatus', methods=['GET'])
        def botstatus():
            status = PumpBotUI.botcheckproc()
            return jsonify({
                'status': status,
                'label': 'Running' if status else 'Stopped',
                'css': 'text-success' if status else 'text-danger'
            })

        # Start Bot
        @app.route('/api/botstart', methods=['POST'])
        @self.loadsession
        def botstart():
            """Start bot.py as a background process."""
            if self.botcheckproc():
                return jsonify({'success': False, 'message': 'Bot is already running.'}), 200
            try:
                self.botcheckproc = subprocess.Popen([sys.executable, 'bot.py'])
                return jsonify({'success': True, 'message': 'Bot started successfully.'}), 200
            except Exception as e:
                return jsonify({'success': False, 'message': f'Failed to start bot: {str(e)}'}), 500

        # Stop Bot
        @app.route('/api/botstop', methods=['POST'])
        @self.loadsession
        def botstop():
            try:
                stopped = False
                bot_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'bot.py'))

                for proc in psutil.process_iter(['pid', 'cmdline']):
                    try:
                        cmdline = proc.info['cmdline']
                        if not cmdline:
                            continue

                        # Match exact script
                        for part in cmdline:
                            if os.path.abspath(part) == bot_path:
                                proc.terminate()
                                proc.wait(timeout=5)
                                stopped = True
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                        continue

                if stopped:
                    return jsonify({'success': True, 'message': 'Bot stopped successfully.'}), 200
                else:
                    return jsonify({'success': False, 'message': 'Bot is not running.'}), 200

            except Exception as e:
                return jsonify({'success': False, 'message': f'Failed to stop bot: {str(e)}'}), 500

        @app.route('/api/botbalance', methods=['GET'])
        def botbalance():
            try:
                sessdbwallet = self.WalletSession()
                wallet = sessdbwallet.get(PumpTableWallet, 1)
                balance = wallet.balance if wallet and wallet.balance else '0.000000000'
                return jsonify({'balance': f"{float(balance):.9f}"})
            except Exception as e:
                print("Wallet balance error:", e)
                return jsonify({'balance': '0.000000000'})

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
            return render_template('edit.html', form=form, data=content, filename='', metadata=BotFields().getfields(),
                                   title='Add Bot', mode='add')

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

            if form.validate_on_submit():
                data = {
                    'rpc': form.rpc.data.strip(),
                    'wss': form.wss.data.strip()
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
                            status = config.get('main', {}).get('status', False)
                    except (ValueError, TypeError):
                        status = False
                    botfiles.append({'filename': filename, 'status': status, 'id': f"switch_{uuid.uuid4().hex[:8]}"})
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
                    lines = [
                        ScriptUtils.stripansi(line).strip()
                        for line in f
                        if line.strip()
                    ]
                    logflask = '\n'.join(lines)
            except FileNotFoundError:
                logflask = 'File not found'
            except Exception as e:
                logflask = f'Error while reading log file: {str(e)}'

            return render_template('logs.html', title='Logs', logflask=logflask)

        # Function 'screener'
        @app.route('/screener')
        @self.loadsession
        def screener():
            """Render screener page with paginated token info and computed prices."""
            sessiondbtrades = self.TokensSession()
            query = request.args.get('page', 1, type=int)

            items = 20
            count = sessiondbtrades.query(PumpTableTokens).count()
            tokens = (sessiondbtrades.query(PumpTableTokens).order_by(PumpTableTokens.created.desc()).offset(
                (query - 1) * items).limit(items).all())
            sessiondbtrades.close()

            solmarket = SolPrice.solvsusd()
            solchange = Decimal(str(solmarket)) if solmarket is not None else None

            for token in tokens:
                try:
                    token.liquidity = Decimal(str(token.liquidity))
                except (InvalidOperation, TypeError):
                    token.liquidity = Decimal(0)

                try:
                    token.marketcap = Decimal(str(token.marketcap))
                except (InvalidOperation, TypeError):
                    token.marketcap = Decimal(0)

                try:
                    token.volume = Decimal(str(token.volume))
                except (InvalidOperation, TypeError):
                    token.volume = Decimal(0)

            nbrpages = ceil(count / items)
            startpage = max(query - 2, 1)
            lastpage = min(startpage + 4, nbrpages)
            if lastpage - startpage < 4:
                startpage = max(lastpage - 4, 1)

            pages = list(range(startpage, lastpage + 1))
            return render_template('screener.html', title='Screener', tokens=tokens, solprice=solchange, query=query, nbrpages=nbrpages, pages=pages)



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
            sessiondbtrades = self.TradesSession()
            query = request.args.get('page', 1, type=int)

            items = 20
            count = sessiondbtrades.query(PumpTableTrades).count()
            trades = (sessiondbtrades.query(PumpTableTrades).order_by(PumpTableTrades.start.desc()).offset(
                (query - 1) * items).limit(items).all())
            sessiondbtrades.close()

            solmarket = SolPrice.solvsusd()
            solchange = Decimal(str(solmarket)) if solmarket is not None else None

            nbrpages = ceil(count / items)
            startpage = max(query - 2, 1)
            lastpage = min(startpage + 4, nbrpages)
            if lastpage - startpage < 4:
                startpage = max(lastpage - 4, 1)

            pages = list(range(startpage, lastpage + 1))
            return render_template('trades.html', title='Trades', trades=trades, solprice=solchange, query=query,
                                   nbrpages=nbrpages, pages=pages)

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
            return render_template('edit.html', form=form, data=content, filename=filename,
                                   metadata=BotFields().getfields(), title='Update Bot', mode='update')

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
    def run(self, host='0.0.0.0', port=5002, debug=False):
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


# Function 'def main():"
def main():
    """ Function description """
    app = PumpBotUI()
    app.run()


# Main callback
if __name__ == '__main__':
    """ Function description """
    main()
