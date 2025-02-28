# GUIDE


## Deploying Tools


>Deploying tools to help you deploy Smartcontracts

>Curently support 4 Chains u can deploy on :

-Sepolia

-Monad Testnet

-Somnia Testnet

-Rome Testnet

>You can also add another chain if you want by simply add it in "chains.txt", make sure to follow the format written in it. 

What you can do with this tools :
- Mint Tokens
- Burn Tokens
- Renounce Ownership
- Verification Smartcontracts(only support for Monad & Sepolia for now)
- Support Multi Private Key
- Mamage your deployed token once it deployed with each private key
- Labelled your deployed Smart Contract for unverified one

>This tool requires "foundry" for Mint,Burn,Renounce,Verification,and Transfer. if u havent installed it, dont worry it will automatically install it when you run the bot. Or if you dont want it u can just install solc :

'sudo snap install solc'

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


### Run the bot

>Run bot

`python3 scripts/deploy.py`


