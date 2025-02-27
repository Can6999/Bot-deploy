import os
import subprocess
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account

load_dotenv()

# Environment variables and web3 setup
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
RPC_URL = os.getenv("RPC_URL")
CHAIN_ID = int(os.getenv("CHAIN_ID"))
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")

web3 = Web3(Web3.HTTPProvider(RPC_URL))
account = Account.from_key(PRIVATE_KEY)

# Smart contract template (no tokens minted on deployment)
CONTRACT_TEMPLATE = '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract {name} is ERC20, Ownable {{
    constructor() ERC20("{name}", "{symbol}") Ownable(msg.sender) {{
        // No tokens minted on deployment.
    }}

    function mint(address to, uint256 amount) public onlyOwner {{
        _mint(to, amount * 10 ** decimals());
    }}

    function burn(uint256 amount) public {{
        _burn(msg.sender, amount * 10 ** decimals());
    }}

    function renounce() public onlyOwner {{
        renounceOwnership();
    }}
}}
'''

# File to save deployed token info (tokenName,contractAddress)
CONTRACT_INFO_FILE = "contract_info.txt"

def install_foundry_dependencies():
    if not os.path.exists("lib"):
        print("[+] Installing Foundry Dependencies...")
        subprocess.run(["forge", "install"], check=True)
        print("[✓] Foundry Dependencies Installed")
    else:
        print("[✓] Foundry Dependencies Already Installed")

def generate_contract(name, symbol):
    print(f"[+] Generating {name} Smart Contract...")
    contract_code = CONTRACT_TEMPLATE.format(name=name, symbol=symbol)
    os.makedirs("contracts", exist_ok=True)
    with open(f"contracts/{name}.sol", "w") as file:
        file.write(contract_code)
    print(f"[✓] Contract {name}.sol Generated")

def compile_contract():
    print("[+] Compiling Contract...")
    if os.path.exists("out"):
        print("[+] Cleaning previous build files...")
        subprocess.run(["rm", "-rf", "out"])
    subprocess.run(["forge", "build"], check=True)
    print("[✓] Compilation Done")

def deploy_contract(name):
    print("[+] Deploying Contract...")
    deploy_cmd = [
        "forge", "create",
        "--rpc-url", RPC_URL,
        "--private-key", PRIVATE_KEY,
        "--broadcast",
        "--force",
        f"contracts/{name}.sol:{name}"
    ]
    result = subprocess.run(deploy_cmd, capture_output=True, text=True)
    print("Deployment Output:")
    print(result.stdout)
    if "Deployed to:" in result.stdout:
        contract_address = result.stdout.split("Deployed to: ")[1].split("\n")[0].strip()
        print(f"[✓] Contract Deployed at: {contract_address}")
        return contract_address
    else:
        print("[!] Deployment Failed")
        return None

def verify_contract(contract_address, name):
    option = input("Do you want to verify the contract? (yes/no): ")
    if option.lower() == "yes":
        print("[+] Verifying Contract...")
        verify_cmd = [
            "forge", "verify-contract",
            contract_address,
            f"contracts/{name}.sol:{name}",
            "--rpc-url", RPC_URL,
            "--verifier", "sourcify",
            "--verifier-url", "https://sourcify-api-monad.blockvision.org"
        ]
        subprocess.run(verify_cmd, check=True)
        print("[✓] Contract Verified")
    else:
        print("[!] Verification Skipped")

def prompt_valid_address(message):
    """Prompt the user for an address until a valid Ethereum address is provided."""
    while True:
        addr = input(message).strip()
        if web3.isAddress(addr):
            return web3.toChecksumAddress(addr)
        else:
            print("Invalid address. Please enter a valid Ethereum address.")

def mint_tokens(contract_address, recipient=None, amount=None):
    if recipient is None:
        recipient = prompt_valid_address("Enter recipient address for minting: ")
    if amount is None:
        amount = input("Enter amount to mint: ")
    print(f"[+] Minting {amount} tokens to {recipient}...")
    mint_selector = web3.keccak(text="mint(address,uint256)")[:4]
    encoded_recipient = bytes.fromhex(recipient[2:]).rjust(32, b'\0')
    encoded_amount = int(amount).to_bytes(32, 'big')
    data = mint_selector + encoded_recipient + encoded_amount
    tx = {
        "to": contract_address,
        "data": data,
        "gas": 100000,
        "maxFeePerGas": web3.to_wei("57", "gwei"),
        "maxPriorityFeePerGas": web3.to_wei("50", "gwei"),
        "chainId": CHAIN_ID,
        "nonce": web3.eth.get_transaction_count(account.address),
    }
    signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"[✓] Mint Transaction Hash: {web3.to_hex(tx_hash)}")

def burn_tokens(contract_address):
    amount = input("Enter amount to burn: ")
    print(f"[+] Burning {amount} tokens...")
    burn_selector = web3.keccak(text="burn(uint256)")[:4]
    encoded_amount = int(amount).to_bytes(32, 'big')
    data = burn_selector + encoded_amount
    tx = {
        "to": contract_address,
        "data": data,
        "gas": 100000,
        "maxFeePerGas": web3.to_wei("57", "gwei"),
        "maxPriorityFeePerGas": web3.to_wei("50", "gwei"),
        "chainId": CHAIN_ID,
        "nonce": web3.eth.get_transaction_count(account.address),
    }
    signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"[✓] Burn Transaction Hash: {web3.to_hex(tx_hash)}")

def renounce_ownership(contract_address):
    print("[+] Renouncing Ownership...")
    renounce_selector = web3.keccak(text="renounce()")[:4]
    tx = {
        "to": contract_address,
        "data": renounce_selector,
        "gas": 100000,
        "maxFeePerGas": web3.to_wei("57", "gwei"),
        "maxPriorityFeePerGas": web3.to_wei("50", "gwei"),
        "chainId": CHAIN_ID,
        "nonce": web3.eth.get_transaction_count(account.address),
    }
    signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"[✓] Renounce Ownership Transaction Hash: {web3.to_hex(tx_hash)}")

def transfer_tokens(contract_address):
    recipient = prompt_valid_address("Enter the recipient address: ")
    amount = input("Enter the amount to transfer: ")
    print(f"[+] Transferring {amount} tokens to {recipient}...")
    transfer_selector = web3.keccak(text="transfer(address,uint256)")[:4]
    encoded_recipient = bytes.fromhex(recipient[2:]).rjust(32, b'\0')
    encoded_amount = int(amount).to_bytes(32, 'big')
    data = transfer_selector + encoded_recipient + encoded_amount
    tx = {
        "to": contract_address,
        "data": data,
        "gas": 100000,
        "maxFeePerGas": web3.to_wei("57", "gwei"),
        "maxPriorityFeePerGas": web3.to_wei("50", "gwei"),
        "chainId": CHAIN_ID,
        "nonce": web3.eth.get_transaction_count(account.address),
    }
    signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"[✓] Transfer Transaction Hash: {web3.to_hex(tx_hash)}")

def post_deployment_actions(contract_address):
    """
    Inner post-deployment loop.
    This menu lets you choose actions for the deployed token.
    """
    while True:
        print("\n=== Post Deployment Actions ===")
        print("1. Mint tokens")
        print("2. Burn tokens")
        print("3. Renounce ownership")
        print("4. Transfer tokens")
        print("0. Exit post deployment actions")
        choice = input("Select an action (0-4): ")
        if choice == "1":
            mint_tokens(contract_address)
        elif choice == "2":
            burn_tokens(contract_address)
        elif choice == "3":
            renounce_ownership(contract_address)
        elif choice == "4":
            transfer_tokens(contract_address)
        elif choice == "0":
            confirm = input("Are you sure you want to exit post deployment actions? (yes/no): ")
            if confirm.lower() == "yes":
                print("Exiting current post deployment session...")
                break
            else:
                print("Continuing post deployment actions...")
                continue
        else:
            print("Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    install_foundry_dependencies()
    
    # Check if there's an existing deployed token info saved
    if os.path.exists(CONTRACT_INFO_FILE):
        with open(CONTRACT_INFO_FILE, "r") as f:
            saved_data = f.read().strip()
        if saved_data:
            token_name_saved, contract_address_saved = saved_data.split(',')
            resume_choice = input(f"Found a deployed token '{token_name_saved}' at address {contract_address_saved}. Resume post deployment actions for this token? (yes/no): ")
            if resume_choice.lower() == "yes":
                while True:
                    post_deployment_actions(contract_address_saved)
                    resume = input("Would you like to resume post deployment actions for this token? (yes/no): ")
                    if resume.lower() != "yes":
                        print("Exiting all post deployment actions.")
                        break
                exit()
            else:
                os.remove(CONTRACT_INFO_FILE)
                print("Previous contract info cleared. Proceeding to new deployment...\n")
    
    # Deploy a new token if not resuming an existing one
    name = input("Enter your smart contract name: ").replace(" ", "_")
    symbol = input("Enter your token symbol: ")
    generate_contract(name, symbol)
    compile_contract()
    contract_address = deploy_contract(name)
    if contract_address:
        # Save deployed token info (token name and address)
        with open(CONTRACT_INFO_FILE, "w") as f:
            f.write(f"{name},{contract_address}")
        verify_contract(contract_address, name)
        
        # Outer loop: allow re-entry into post deployment actions
        while True:
            post_deployment_actions(contract_address)
            resume = input("Would you like to resume post deployment actions for this token? (yes/no): ")
            if resume.lower() != "yes":
                print("Exiting all post deployment actions.")
                break
