# Class 'BotFields'
class BotFields:
    """ Class description """

    # Class initialization
    def __init__(self):
        """ Initializer description """
        self.fields = self.buildfields()

    # Function 'buildfields'
    @staticmethod
    def buildfields():
        """ Function description """
        return {
            'main': {
                'status': {
                    'label': 'Bot Status',
                    'type': 'select',
                    'description': 'Enable or disable this bot instance entirely.',
                    'options': ['True', 'False']
                },
                'botname': {
                    'label': 'Bot Name',
                    'type': 'text',
                    'description': 'A unique name to identify and reference this specific bot configuration.'
                },
                'sandbox': {
                    'label': 'Sandbox Mode',
                    'type': 'select',
                    'description': 'When enabled, activates paper trading mode (simulated trades with no real SOL).',
                    'options': ['True', 'False']
                },
                'maxopentrades': {
                    'label': 'Max. Open Trades',
                    'type': 'text',
                    'description': 'Maximum number of simultaneous trades that can be open at any given time. Set to 0 for unlimited.'
                },
                'initbalance': {
                    'label': 'Initial Balance',
                    'type': 'text',
                    'description': 'Starting virtual balance in SOL for the bot when running in sandbox mode.'
                }
            },
            'monitoring': {
                'chain': {
                    'label': 'Chain',
                    'type': 'select',
                    'description': 'Defines the event source to listen for token detection (e.g., new blocks or logs).',
                    'options': ['blocks', 'logs']
                },
                'interval': {
                    'label': 'Interval',
                    'type': 'text',
                    'description': 'Defines the interval to wait in millseconds before to store the detected token into the database  (e.g. 60000 = 60 seconds).'
                }
            },
            'filters': {
                'chainlistener': {
                    'label': 'Chain Listener',
                    'type': 'select',
                    'description': 'Defines the event source to listen for token detection (e.g., new blocks or logs).',
                    'options': ['blocks', 'logs']
                },
                'matchstring': {
                    'label': 'Match String',
                    'type': 'text',
                    'description': 'Only consider tokens whose name or symbol contains this substring.'
                },
                'matchaddress': {
                    'label': 'User Address',
                    'type': 'text',
                    'description': 'Only consider tokens deployed by this specific wallet address.'
                },
                'noshorting': {
                    'label': 'No Shorting',
                    'type': 'select',
                    'description': 'If enabled, disables shorting and allows only buy trades.',
                    'options': ['True', 'False']
                },
                'nostopping': {
                    'label': 'No Stopping',
                    'type': 'select',
                    'description': 'When enabled, the bot continuously executes token trades based on real-time market signals.',
                    'options': ['True', 'False']
                }
            },
            'timing': {
                'tokenidleinit': {
                    'label': 'Token Initialization',
                    'type': 'text',
                    'description': 'Time to wait after a token is created before any trade can be considered.'
                },
                'tokenidleshort': {
                    'label': 'Token Sell Period',
                    'type': 'text',
                    'description': 'Cooldown period after a token has been sold before it becomes eligible for another buy.'
                },
                'tokenidlefresh': {
                    'label': 'Token New Detection',
                    'type': 'text',
                    'description': 'Delay before scanning or acting on a newly detected token.'
                },
                'tokenminage': {
                    'label': 'Min. Token Age',
                    'type': 'text',
                    'description': 'Minimum token age in seconds required to qualify for trading.'
                },
                'tokenmaxage': {
                    'label': 'Max. Token Age',
                    'type': 'text',
                    'description': 'Maximum token age in seconds beyond which tokens will be ignored.'
                },
                'tokentimeout': {
                    'label': 'Token Timeout',
                    'type': 'text',
                    'description': 'Timeout (in seconds) to wait for token metadata or price response before skipping.'
                }
            },
            'trade': {
                'buyamount': {
                    'label': 'Buy Amount',
                    'type': 'text',
                    'description': 'Amount of SOL to allocate for each token purchase.'
                },
                'buyslippage': {
                    'label': 'Buy Slippage',
                    'type': 'text',
                    'description': 'Maximum allowable slippage for buy orders (as a decimal percentage, e.g., 0.05 = 5%).'
                },
                'sellslippage': {
                    'label': 'Sell Slippage',
                    'type': 'text',
                    'description': 'Maximum allowable slippage for sell orders (as a decimal percentage).'
                },
                'fastmode': {
                    'label': 'Fast Mode',
                    'type': 'select',
                    'description': 'Bypass price checks and execute buys immediately after detection.',
                    'options': ['True', 'False']
                },
                'fasttokens': {
                    'label': 'Fast Tokens',
                    'type': 'text',
                    'description': 'Number of tokens to buy when fast mode is enabled.'
                },
                'stoploss': {
                    'label': 'Stop Loss',
                    'type': 'text',
                    'description': 'Loss threshold in percentage. The bot will sell if the price drops by this amount.'
                },
                'takeprofit': {
                    'label': 'Take Profit',
                    'type': 'text',
                    'description': 'Profit threshold in percentage. The bot will sell if the price increases by this amount.'
                },
                'trailprofit': {
                    'label': 'Trailing Profit',
                    'type': 'select',
                    'description': 'Activate multilevel trailing profit once the price has increased by these level.',
                    'options': ['True', 'False']
                },
                'trailone': {
                    'label': 'Trailing Level 1',
                    'type': 'text',
                    'description': 'The first trailing profit level the bot must secure, expressed as a percentage.'
                },
                'trailtwo': {
                    'label': 'Trailing Level 2',
                    'type': 'text',
                    'description': 'The second trailing profit level the bot must secure, expressed as a percentage.'
                },
                'trailthree': {
                    'label': 'Trailing Level 3',
                    'type': 'text',
                    'description': 'The third trailing profit level the bot must secure, expressed as a percentage.'
                },
                'trailfour': {
                    'label': 'Trailing Level 4',
                    'type': 'text',
                    'description': 'The fourth trailing profit level the bot must secure, expressed as a percentage.'
                },
                'trailfive': {
                    'label': 'Trailing Level 5',
                    'type': 'text',
                    'description': 'The fifth trailing profit level the bot must secure, expressed as a percentage.'
                }
            },
            'priority': {
                'dynamic': {
                    'label': 'Dynamic Priority',
                    'type': 'select',
                    'description': 'Use real-time gas fee estimation for adjusting priority fees.',
                    'options': ['True', 'False']
                },
                'fixed': {
                    'label': 'Fixed Fee',
                    'type': 'select',
                    'description': 'Use a fixed fee value instead of dynamic estimation.',
                    'options': ['True', 'False']
                },
                'lamports': {
                    'label': 'Base Lamports',
                    'type': 'text',
                    'description': 'Base fee in microlamports (1,000,000 = 0.001 SOL).'
                },
                'extra': {
                    'label': 'Extra Percentage',
                    'type': 'text',
                    'description': 'Percentage to increase the base fee for better priority.'
                },
                'hardcap': {
                    'label': 'Hard Cap',
                    'type': 'text',
                    'description': 'Maximum priority fee in microlamports to prevent overspending.'
                }
            },
            'retries': {
                'attempts': {
                    'label': 'Max. Attempts',
                    'type': 'text',
                    'description': 'Maximum number of retry attempts for submitting a failed transaction before giving up.'
                }
            },
            'wipe': {
                'clean': {
                    'label': 'Cleanup Mode',
                    'type': 'select',
                    'description': 'Defines when cleanup actions (e.g., burning or closing accounts) should occur.',
                    'options': ['disabled', 'fail', 'sell', 'session']
                },
                'burn': {
                    'label': 'Force Burn',
                    'type': 'select',
                    'description': 'If enabled, any remaining tokens will be forcefully burned after trading.',
                    'options': ['True', 'False']
                },
                'rate': {
                    'label': 'Priority Rate',
                    'type': 'select',
                    'description': 'Use priority rate for cleanup-related transactions.',
                    'options': ['True', 'False']
                }
            },
            'rules': {
                'minmarketcap': {
                    'label': 'Min. Market Cap',
                    'type': 'text',
                    'description': 'Minimum market capitalization (SOL) required for a token to be eligible.'
                },
                'maxmarketcap': {
                    'label': 'Max. Market Cap',
                    'type': 'text',
                    'description': 'Maximum market capitalization (SOL) allowed for a token to qualify.'
                },
                'minmarketvol': {
                    'label': 'Min. Market Volume',
                    'type': 'text',
                    'description': 'Minimum trading volume (SOL) required for a token to be considered.'
                },
                'maxmarketvol': {
                    'label': 'Max. Market Volume',
                    'type': 'text',
                    'description': 'Maximum trading volume (SOL) allowed for a token to qualify.'
                },
                'minholdowner': {
                    'label': 'Min. Owner Hold',
                    'type': 'text',
                    'description': 'Minimum percentage of total supply the token owner must hold.'
                },
                'maxholdowner': {
                    'label': 'Max. Owner Hold',
                    'type': 'text',
                    'description': 'Maximum percentage of total supply the token owner is allowed to hold.'
                },
                'topholders': {
                    'label': 'Top Holder',
                    'type': 'text',
                    'description': 'Maximum allowed percentage held by the top wallet holder.'
                },
                'minholders': {
                    'label': 'Min. Holders',
                    'type': 'text',
                    'description': 'Minimum number of unique token holders required for eligibility.'
                },
                'maxholders': {
                    'label': 'Max. Holders',
                    'type': 'text',
                    'description': 'Maximum number of holders allowed for a token to qualify.'
                },
                'holderscheck': {
                    'label': 'Holders Check',
                    'type': 'select',
                    'description': 'Enable to verify that all holders have a minimum SOL balance.',
                    'options': ['True', 'False']
                },
                'holdersbalance': {
                    'label': 'Holders Balance',
                    'type': 'text',
                    'description': 'Minimum balance required in each holder\'s account for the token to qualify.'
                },
                'minliquidity': {
                    'label': 'Min. Liquidity Pool',
                    'type': 'text',
                    'description': 'Minimum liquidity (in SOL) the token must have in its trading pool.'
                },
                'maxliquidity': {
                    'label': 'Max. Liquidity Pool',
                    'type': 'text',
                    'description': 'Maximum liquidity (in SOL) allowed for token eligibility.'
                }
            }
        }

    # Function 'getfields'
    def getfields(self):
        """ Function description """
        return self.fields
