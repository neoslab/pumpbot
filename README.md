# Pumpbot

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

This project delivers a **fully autonomous trading and sniping bot** designed specifically for **PumpFun** on the **Solana blockchain**, written entirely in **Python** and engineered to function **independently of third-party APIs**. It directly interacts with the **Solana RPC node** or integrates with **Helius** to fetch and process real-time blockchain data, ensuring low-latency execution and maximum reliability without depending on external aggregators or indexers.

* * *

## Automatic Server Setup

```bash
wget -qO- https://neoslab.com/wp-content/uploads/bash/pumpbot.sh | bash
```

* * *

## Manual Server Setup

### Update/upgrade machine

```bash
sudo apt -y update && sudo apt -y upgrade && sudo apt -y dist-upgrade
sudo apt -y remove && sudo apt -y autoremove
sudo apt -y clean && sudo apt -y autoclean
```

### Change the SSH port from 22 to 49622

```bash
sudo sed -i 's/^#\?Port 22/Port 49622/' /etc/ssh/sshd_config
sudo sed -i 's/^#\?ListenStream=22/ListenStream=49622/' /lib/systemd/system/ssh.socket
```

### Restart the SSH service

```bash
sudo systemctl daemon-reload
sudo systemctl restart ssh
```

### Install System Dependencies

```bash
sudo apt -y install build-essential curl git libbz2-dev libclang-dev libdb5.3-dev \
libexpat1-dev libffi-dev libgdbm-dev liblzma-dev libncurses5-dev libncursesw5-dev \
libpq-dev libreadline-dev libsqlite3-dev libssl-dev libudev-dev llvm net-tools \
pkg-config protobuf-compiler software-properties-common tk-dev uuid-dev zlib1g-dev
```

### Install Python Packages

```bash
sudo apt -y install python3 python3-bs4 python3-cryptography python3-dateutil \
python3-dev python3-django python3-flask python3-ipython python3-jinja2 python3-lxml \
python3-matplotlib python3-numpy python3-pandas python3-pip python3-pyqt5 \
python3-requests python3-scipy python3-setuptools python3-sklearn python3-venv
sudo ln -s /usr/bin/python3 /usr/local/bin/python
sudo ln -s /usr/bin/pip3 /usr/local/bin/pip
python --version
pip --version
```

### Install Rust Latest Version

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y > /dev/null 2>&1
. "$HOME/.cargo/env"
rustc --version
cargo --version
```

### Install Solana CLI Latest Version

```bash
sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)" > /dev/null 2>&1
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
echo 'export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
solana --version
```

### Clone Project Repository

```bash
cd $HOME
git clone https://github.com/neoslab/pumpbot
cd $HOME/pumpbot
python3 -m venv pumpbot
source pumpbot/bin/activate
```

### Install PIP dependencies

If you are using Linux, run the following command to ensure `uvloop` be installed along with the another required packages.

```bash
sed -i 's/^#\?uvloop>=0.21.0/uvloop>=0.21.0/' $HOME/pumpbot/requirements.txt
```

Install the PIP packages dependencies.

```bash
python -m pip install -r requirements.txt
```

### Modify username and password

```bash
nano config/user.yaml
```

### Launch the bot

```bash
nohup python app.py > nohup.log 2>&1 &
```

* * *

### Windows PyCharm Setup

**Upgrade PIP if needed**

```bash
C:\<DIRECTORY\FULLPATH>\pumpbot\.venv\Scripts\python.exe -m pip install --upgrade pip
```

**Install requirements**

```bash
C:\<DIRECTORY\FULLPATH>\pumpbot\.venv\Scripts\python.exe -m pip install -r C:\<DIRECTORY\FULLPATH>\pumpbot\requirements.txt
```

**Start App**

```bash
C:\<DIRECTORY\FULLPATH>\pumpbot\.venv\Scripts\python.exe C:\<DIRECTORY\FULLPATH>\Python\pumpbot\main.py
```

* * *

### Endpoint Configuration

**Solana Node**

```
https://api.mainnet-beta.solana.com
wss://api.mainnet-beta.solana.com
```

**Helius Node**

```
https://mainnet.helius-rpc.com/?api-key=<HELIUS-API-KEY>
wss://mainnet.helius-rpc.com/?api-key=<HELIUS-API-KEY>
```

### Bot Configuration

The trading bots can be fully configured through individual YAML files located in the bots/ folder. Each file defines a separate bot instance with its own strategy, settings, and behavior. You can add as many bots as you want by creating new YAML files in this folder.

```bash
# This file defines comprehensive parameters and settings for the trading bot.
# Carefully review and adjust values to match your trading strategy and risk tolerance.

# Bot main configuration
main:
    # Bot Status
    # Enable or disable this bot instance entirely.
    status: False

    # Bot Name
    # A unique name to identify and reference this specific bot configuration.
    botname: "bot-trader-1"

    # Sandbox Mode
    # When enabled, activates paper trading mode (simulated trades with no real SOL).
    sandbox: True

    # Max. Open Trades
    # Maximum number of simultaneous trades that can be open at any given time. Set to 0 for unlimited.
    maxopentrades: 5

    # Initial Balance
    # Starting virtual balance in SOL for the bot when running in sandbox mode.
    initbalance: 10

# Monitoring for token selection
monitoring:
    # Listener
    # Defines the event source to listen for token detection (e.g., new blocks or logs).
    chain: "logs"

    # Interval
    # Defines the interval to wait in millseconds before to store the detected token into the database  (e.g. 60000 = 60 seconds).
    interval: 0.001

# Filters for token selection
filters:
    # Match String
    # Only consider tokens whose name or symbol contains this substring.
    matchstring: Null

    # User Address
    # Only consider tokens deployed by this specific wallet address.
    matchaddress: Null

    # No Shorting
    # If enabled, disables shorting and allows only buy trades.
    noshorting: False

    # No Stopping
    # When enabled, the bot continuously executes token trades based on real-time market signals.
    nostopping: False

# Token timing configuration
timing:
    # Token Initialization
    # Time to wait after a token is created before any trade can be considered.
    tokenidleinit: 15

    # Token Sell Period
    # Cooldown period after a token has been sold before it becomes eligible for another buy.
    tokenidleshort: 15

    # Token Fresh Detection
    # Delay before scanning or acting on a newly detected token.
    tokenidlefresh: 15

    # Min. Token Age
    # Minimum token age (in milliseconds) required to qualify for trading (e.g. 60000 = 60 seconds).
    tokenminage: 0.001

    # Max. Token Age
    # Maximum token age (in milliseconds) beyond which tokens will be ignored. (e.g. 60000 = 60 seconds).
    tokenmaxage: 0.005

    # Token Timeout
    # Timeout (in seconds) to wait for token metadata or price response before skipping.
    tokentimeout: 30

# Trading parameters
trade:
    # Buy Amount
    # Amount of SOL to allocate for each token purchase.
    buyamount: 0.0001

    # Buy Slippage
    # Maximum allowable slippage for buy orders (as a decimal percentage, e.g., 0.05 = 5%).
    buyslippage: 0.3

    # Sell Slippage
    # Maximum allowable slippage for sell orders (as a decimal percentage).
    sellslippage: 0.3

    # Fast Mode
    # Bypass price checks and execute buys immediately after detection.
    fastmode: False

    # Fast Tokens
    # Number of tokens to buy when fast mode is enabled.
    fasttokens: 20

    # Stop Loss
    # Loss threshold in percentage. The bot will sell if the price drops by this amount.
    stoploss: 20

    # Take Profit
    # Profit threshold in percentage. The bot will sell if the price increases by this amount.
    takeprofit: 50

    # Trailing Profit
    # Activate multilevel trailing profit once the price has increased by these level.
    trailprofit: False

    # Trailing Level 1
    # The first trailing profit level the bot must secure, expressed as a percentage.
    trailone: 50

    # Trailing Level 2
    # The second trailing profit level the bot must secure, expressed as a percentage.
    trailtwo: 50

    # Trailing Level 3
    # The third trailing profit level the bot must secure, expressed as a percentage.
    trailthree: 50

    # Trailing Level 4
    # The fourth trailing profit level the bot must secure, expressed as a percentage.
    trailfour: 50

    # Trailing Level 5
    # The first fifth profit level the bot must secure, expressed as a percentage.
    trailfive: 50

# Priority fee configuration
priority:
    # Dynamic Priority
    # Use real-time gas fee estimation for adjusting priority fees.
    dynamic: False

    # Fixed Fee
    # Use a fixed fee value instead of dynamic estimation.
    fixed: True

    # Base Lamports
    # Base fee in microlamports (1,000,000 = 0.001 SOL).
    lamports: 1_000_000

    # Extra Percentage
    # Percentage to increase the base fee for better priority.
    extra: 0.0

    # Hard Cap
    # Maximum priority fee in microlamports to prevent overspending.
    hardcap: 1_000_000

# Retry and timeout settings
retries:
    # Max. Attempts
    # Maximum number of retry attempts for submitting a failed transaction before giving up.
    attempts: 1

# Token and account management
wipe:
    # Cleanup Mode
    # Defines when cleanup actions (e.g., burning or closing accounts) should occur.
    # disabled   > no cleanup will occur.
    # fail       > only clean up if a buy transaction fails.
    # sell       > clean up after selling.
    # session    > clean up all empty accounts after a trading session ends.
    clean: "session"

    # Force Burn
    # If enabled, any remaining tokens will be forcefully burned after trading.
    burn: False

    # Priority Rate
    # Use priority fees for cleanup-related transactions.
    rate: False

# Rules
rules:
    # Min. Market Cap
    # Minimum market capitalization (SOL) required for a token to be eligible.
    minmarketcap: 6000

    # Max. Market Cap
    # Maximum market capitalization (SOL) allowed for a token to qualify.
    maxmarketcap: 10000

    # Min. Market Volume
    # Minimum trading volume (SOL) required for a token to be considered.
    minmarketvol: 6000

    # Max. Market Volume
    # Maximum trading volume (SOL) allowed for a token to qualify.
    maxmarketvol: 10000

    # Min. Owner Hold
    # Minimum percentage of total supply the token owner must hold.
    minholdowner: 20

    # Max. Owner Hold
    # Maximum percentage of total supply the token owner is allowed to hold.
    maxholdowner: 30

    # Top Holder
    # Maximum allowed percentage held by the top wallet holder.
    topholders: 20

    # Min. Holders
    # Minimum number of holders required for a token to qualify.
    minholders: 10

    # Max. Holders
    # Maximum number of holders allowed for a token to qualify.
    maxholders: 20

    # Holders Check
    # Enable to verify that all holders have a minimum SOL balance.
    holderscheck: False

    # Holders Balance
    # Minimum balance required in each holder's account for the token to qualify.
    holdersbalance: 0.1

    # Min. Liquidity Pool
    # Minimum liquidity (in SOL) the token must have in its trading pool.
    minliquidity: 4000

    # Max. Liquidity Pool
    # Maximum liquidity (in SOL) allowed for token eligibility.
    maxliquidity: 10000
```

* * *

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Make your changes and commit them (`git commit -m "Add your feature"`).
4. Push to your branch (`git push origin feature/your-feature`).
5. Open a pull request with a clear description of your changes.

Ensure your code follows PEP 8 style guidelines and includes appropriate tests.

* * *

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

* * *

## Contact

For issues, suggestions, or questions, please open an issue on GitHub or contact the maintainer at [GitHub Issues](https://github.com/neoslab/pumpbot/issues).