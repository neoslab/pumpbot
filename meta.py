fields = {
    'main': {
        'enabled': {
            'label': 'Bot Enabled',
            'type': 'select',
            'description': 'Enable or disable this bot instance.',
            'options': ['True', 'False']
        },
        'name': {
            'label': 'Name',
            'type': 'text',
            'description': 'Unique name to identify the bot instance.'
        },
        'rpcendpoint': {
            'label': 'RPC Endpoint',
            'type': 'text',
            'description': 'Solana RPC endpoint (e.g., Helius, QuickNode).'
        },
        'wssendpoint': {
            'label': 'WSS Endpoint',
            'type': 'text',
            'description': 'WebSocket endpoint for real-time data.'
        },
        'privkey': {
            'label': 'Private Key',
            'type': 'password',
            'description': 'Solana wallet private key (keep it secret).'
        },
        'separate': {
            'label': 'Separate Process',
            'type': 'select',
            'description': 'Run in a separate process/thread.',
            'options': ['True', 'False']
        },
        'sandbox': {
            'label': 'Sandbox Mode',
            'type': 'select',
            'description': 'Enable paper trading mode.',
            'options': ['True', 'False']
        }
    },
    'filters': {
        'listener': {
            'label': 'Listener',
            'type': 'select',
            'description': 'Event source for token detection.',
            'options': ['logs', 'blocks', 'geyser']
        },
        'matchstring': {
            'label': 'Match String',
            'type': 'text',
            'description': 'Only trade tokens containing this string.'
        },
        'useraddress': {
            'label': 'User Address',
            'type': 'text',
            'description': 'Only trade tokens created by this address.'
        },
        'noshorting': {
            'label': 'No Shorting',
            'type': 'select',
            'description': 'If true, buy-only mode.',
            'options': ['True', 'False']
        },
        'filteroff': {
            'label': 'Filter Off',
            'type': 'select',
            'description': 'If true, disables all filters.',
            'options': ['True', 'False']
        }
    },
    'geyser': {
        'endpoint': {
            'label': 'Endpoint',
            'type': 'text',
            'description': 'Geyser endpoint for fast on-chain data.'
        },
        'apitoken': {
            'label': 'API Token',
            'type': 'text',
            'description': 'API token for Geyser access.'
        },
        'authtype': {
            'label': 'Auth Type',
            'type': 'select',
            'description': 'Authentication method for Geyser.',
            'options': ['x-token', 'basic']
        }
    },
    'timing': {
        'tokenmaxage': {
            'label': 'Max. Token Age',
            'type': 'text',
            'description': 'Maximum age of token (in seconds) to be considered fresh.'
        },
        'tokentimeout': {
            'label': 'Token Timeout',
            'type': 'text',
            'description': 'Token server response timeout in seconds.'
        }
    },
    'trade': {
        'buyamount': {
            'label': 'Buy Amount',
            'type': 'text',
            'description': 'SOL amount per token buy.'
        },
        'buyslippage': {
            'label': 'Buy Slippage',
            'type': 'text',
            'description': 'Max slippage allowed for buy orders (e.g. 0.3 = 30%).'
        },
        'sellslippage': {
            'label': 'Sell Slippage',
            'type': 'text',
            'description': 'Max slippage allowed for sell orders.'
        },
        'fastmode': {
            'label': 'Fast Mode',
            'type': 'select',
            'description': 'Enable fast buy without price confirmation.',
            'options': ['True', 'False']
        },
        'fasttokens': {
            'label': 'Fast Tokens',
            'type': 'text',
            'description': 'Amount of tokens to buy when fastmode is enabled.'
        },
        'stoplosspercent': {
            'label': 'Stoploss Percentage',
            'type': 'text',
            'description': 'Stop loss percentage.'
        },
        'stoplossmarketcap': {
            'label': 'Stoploss Market Cap',
            'type': 'text',
            'description': 'Stop loss based on market cap (USD).'
        },
        'takeprofitpercent': {
            'label': 'Take Profit Percentage',
            'type': 'text',
            'description': 'Take profit percentage.'
        },
        'takeprofitmarketcap': {
            'label': 'Take Profit Market Cap',
            'type': 'text',
            'description': 'Take profit based on market cap (USD).'
        },
        'trailingstop': {
            'label': 'Trailing Stop',
            'type': 'select',
            'description': 'Enable trailing stop loss.',
            'options': ['True', 'False']
        },
        'trailingdrop': {
            'label': 'Trailing Drop Percentage',
            'type': 'text',
            'description': 'Trailing drop percentage to trigger sell.'
        }
    },
    'priority': {
        'enabledynamic': {
            'label': 'Dynamic Priority',
            'type': 'select',
            'description': 'Enable dynamic priority fee estimation.',
            'options': ['True', 'False']
        },
        'enablefixed': {
            'label': 'Fixed Fee',
            'type': 'select',
            'description': 'Use fixed fee instead of dynamic.',
            'options': ['True', 'False']
        },
        'baselamports': {
            'label': 'Base Lamports',
            'type': 'text',
            'description': 'Base priority fee in microlamports (1_000_000 = 0.001 SOL).'
        },
        'extrapercent': {
            'label': 'Extra Percentage',
            'type': 'text',
            'description': 'Extra percentage to add to the base fee.'
        },
        'hardcap': {
            'label': 'Hard Cap',
            'type': 'text',
            'description': 'Maximum fee cap in microlamports.'
        }
    },
    'retries': {
        'maxattempts': {
            'label': 'Max Attempts',
            'type': 'text',
            'description': 'Max attempts to submit a transaction.'
        },
        'waitaftercreation': {
            'label': 'Wait After Creation',
            'type': 'text',
            'description': 'Wait time in seconds after token creation.'
        },
        'waitafterbuy': {
            'label': 'Wait After Buy',
            'type': 'text',
            'description': 'Wait time in seconds after buying.'
        },
        'waitnewtoken': {
            'label': 'Wait New Token',
            'type': 'text',
            'description': 'Pause between token trades in seconds.'
        }
    },
    'cleanup': {
        'mode': {
            'label': 'Cleanup Mode',
            'type': 'select',
            'description': 'Cleanup strategy after trades.',
            'options': ['disabled', 'on_fail', 'after_sell', 'post_session']
        },
        'forceburn': {
            'label': 'Force Burn',
            'type': 'select',
            'description': 'Force burn remaining tokens before account cleanup.',
            'options': ['True', 'False']
        },
        'priorityfee': {
            'label': 'Priority Fee',
            'type': 'select',
            'description': 'Use priority fee for cleanup transactions.',
            'options': ['True', 'False']
        }
    },
    'rules': {
        'minmarketcap': {
            'label': 'Min. Market Cap',
            'type': 'text',
            'description': 'Minimum required market cap (USD).'
        },
        'maxmarketcap': {
            'label': 'Max. Market Cap',
            'type': 'text',
            'description': 'Maximum allowed market cap (USD).'
        },
        'maxholdowner': {
            'label': 'Max. Owner Hold',
            'type': 'text',
            'description': 'Max % of supply the owner is allowed to hold.'
        },
        'holdertop': {
            'label': 'Top Holder',
            'type': 'text',
            'description': 'Max % held by the top wallet.'
        },
        'minholders': {
            'label': 'Min. Holders',
            'type': 'text',
            'description': 'Minimum number of holders required.'
        },
        'maxholders': {
            'label': 'Max. Holders',
            'type': 'text',
            'description': 'Maximum number of holders allowed.'
        },
        'checkholders': {
            'label': 'Check. Holders',
            'type': 'select',
            'description': 'Check if holders have a minimum SOL balance.',
            'options': ['True', 'False']
        },
        'liquiditypool': {
            'label': 'Liquidity Pool',
            'type': 'text',
            'description': 'Minimum liquidity pool size (USD).'
        }
    }
}
