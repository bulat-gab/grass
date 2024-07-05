#!/bin/bash

# Update package list
sudo apt update

# Install basic dependencies
sudo apt install -y python3 python3-pip python3-venv curl || true
sudo systemctl daemon-reload


# Create a virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt
deactivate

if [ ! -f ./.env ]; then
    echo ".env file not found. Creating one, please add USER ID and Proxy."
    cp ./.env-example ./.env
fi


# Installing Node.js and npm
curl -fsSL https://deb.nodesource.com/setup_current.x | sudo -E bash -
sudo apt-get install -y nodejs || true

# Install pm2 globally
sudo npm install pm2@latest -g

# echo "Creating virtual environment..."
# python3 -m venv venv

# echo "Activating virtual environment..."
# source venv/bin/activate

echo ""
echo "Installed Versions:"
echo "PM2 version: $(pm2 --version)"
echo "Python version: $(python3 --version 2>/dev/null || echo 'Python 3 not found')"
echo "Node.js version: $(node --version 2>/dev/null || echo 'Node.js not found')"
echo "npm version: $(npm --version 2>/dev/null || echo 'npm not found')"