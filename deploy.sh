#!/bin/bash

# Update/upgrade machine
sudo apt -y update && sudo apt -y upgrade && sudo apt -y dist-upgrade
sudo apt -y remove && sudo apt -y autoremove
sudo apt -y clean && sudo apt -y autoclean

# Change the SSH port from 22 to 49622
sudo sed -i 's/^#\?Port 22/Port 49622/' /etc/ssh/sshd_config
sudo sed -i 's/^#\?ListenStream=22/ListenStream=49622/' /lib/systemd/system/ssh.socket

# Restart the SSH service
sudo systemctl daemon-reload
sudo systemctl restart ssh

# Install System Dependencies
sudo apt -y install build-essential curl git libbz2-dev libclang-dev libdb5.3-dev \
libexpat1-dev libffi-dev libgdbm-dev liblzma-dev libncurses5-dev libncursesw5-dev \
libpq-dev libreadline-dev libsqlite3-dev libssl-dev libudev-dev llvm net-tools \
pkg-config protobuf-compiler software-properties-common tk-dev uuid-dev zlib1g-dev

# Install Python Packages
sudo apt -y install python3 python3-bs4 python3-cryptography python3-dateutil \
python3-dev python3-django python3-flask python3-ipython python3-jinja2 python3-lxml \
python3-matplotlib python3-numpy python3-pandas python3-pip python3-pyqt5 \
python3-requests python3-scipy python3-setuptools python3-sklearn python3-venv
sudo ln -s /usr/bin/python3 /usr/local/bin/python
sudo ln -s /usr/bin/pip3 /usr/local/bin/pip
python --version
pip --version

# Install Rust Latest Version
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y > /dev/null 2>&1
. "$HOME/.cargo/env"
rustc --version
cargo --version

# Install Solana CLI Latest Version
sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)" > /dev/null 2>&1
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
echo 'export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
solana --version

# Clone Project Repository
cd $HOME
git clone https://github.com/neoslab/pumpbot
cd $HOME/pumpbot
python3 -m venv pumpbot
source pumpbot/bin/activate

# Install PIP dependencies
sed -i 's/^#\?uvloop>=0.21.0/uvloop>=0.21.0/' $HOME/pumpbot/requirements.txt
python -m pip install -r requirements.txt
