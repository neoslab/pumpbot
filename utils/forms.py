# Import packages
from flask_wtf import FlaskForm
from wtforms import PasswordField
from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import DataRequired


# Class 'BotForm'
class BotForm(FlaskForm):
    """ Class description """
    filename = StringField('Filename', validators=[DataRequired()])
    submit = SubmitField('Save Bot')


# Class 'EndpointForm'
class EndpointForm(FlaskForm):
    """ Class description """
    rpc = StringField(
        'RPC Endpoint',
        description='Solana RPC endpoint used for blockchain interactions (e.g., Solana, Helius, QuickNode)',
        validators=[DataRequired()]
    )
    wss = StringField(
        'WSS Endpoint',
        description='Solana WSS endpoint used for blockchain interactions (e.g., Solana, Helius, QuickNode)',
        validators=[DataRequired()]
    )
    api = StringField(
        'API Key',
        description='API key if using Helius or QuickNode (optional)'
    )
    submit = SubmitField('Save Endpoint')


# Class 'LoginForm'
class LoginForm(FlaskForm):
    """ Class description """
    username = StringField(
        'Username',
        validators=[DataRequired()]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )
    submit = SubmitField('Login')


# Class 'WalletForm'
class WalletForm(FlaskForm):
    """ Class description """
    pubadd = StringField(
        'Public Address',
        description='Solana wallet public address used for sending, receiving, and monitoring funds.',
        validators=[DataRequired()]
    )
    prikey = StringField(
        'Private Key',
        description='Solana wallet private key used for signing transactions (keep this secret).',
        validators=[DataRequired()]
    )
    submit = SubmitField('Save Wallet')
