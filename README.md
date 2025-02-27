# GUIDE


## Bot Deploy Smartcontracts on Monad Testnet

>If you want to use this bot for another chain, simply just edit .env file by running :

`nano .env`

This Bot automates smart contract deployment with:
- Mint Tokens
- Burn Tokens
- Renounce Ownership
- Auto Verification

>This bot requires "foundry" if u havent installed it, dont worry it will automatically install it when you run the bot

## Install foundry manually

`curl -L https://foundry.paradigm.xyz | bash`

`source ~/.bashrc`

`foundryup`


### Install Dependencies

`sudo apt update && sudo apt upgrade -y`

`sudo apt install python3 -y`

`sudo apt install python3-venv -y`

`sudo apt install python3-pip -y`

### Tutorial on how to install and run bot


Clone the repository :
`git clone https://github.com/Can6999/Bot-deploy.git`

`cd Bot-deploy`

### Use python virtual environment to install requirements.txt

`python3 -m venv venv`

`source venv/bin/activate`

`pip install -r requirements.txt`


### After done, open .env file and edit like this
`nano .env`


>RPC_URL=https://testnet-rpc.monad.xyz

>PRIVATE_KEY=your_private_key

>CHAIN_ID=10143

>ETHERSCAN_API_KEY=https://sourcify-api-monad.blockvision.org


### Run the bot


>Run bot

`python3 scripts/deploy.py`


