import os
import subprocess
import shutil
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
RPC_URL = os.getenv("RPC_URL")
CHAIN_ID = int(os.getenv("CHAIN_ID"))
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")

web3 = Web3(Web3.HTTPProvider(RPC_URL))

CONTRACT_TEMPLATE = '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract {name} is ERC20, Ownable {{
    constructor() ERC20("{name}", "{symbol}") {{
        _mint(msg.sender, {supply} * 10 ** decimals());
        transferOwnership(msg.sender);
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
def check_foundry():
    if shutil.which("forge") is None:
        print("[!] Foundry not found.")
        print("Please install Foundry using:")
        print("curl -L https://foundry.paradigm.xyz | bash && foundryup")
        exit()
    else:
        print("[✓] Foundry Installed")

check_foundry()


def generate_contract(name, symbol, supply):
    print(f"[+] Generating {name} Smart Contract...")
    contract_code = CONTRACT_TEMPLATE.format(name=name, symbol=symbol, supply=supply)

    os.makedirs("contracts", exist_ok=True)
    with open(f"contracts/{name}.sol", "w") as file:
        file.write(contract_code)
    print(f"[✓] Contract {name}.sol generated")

def compile_contract():
    print("[+] Compiling Contract...")
    subprocess.run(["forge", "build"], check=True)
    print("[✓] Compilation Done")

def deploy_contract(name):
    print("[+] Deploying Contract...")
    deploy_cmd = [
        "forge", "create",
        "--rpc-url", RPC_URL,
        "--private-key", PRIVATE_KEY,
        f"contracts/{name}.sol:{name}"
    ]

    result = subprocess.run(deploy_cmd, capture_output=True, text=True)
    if result.returncode == 0:
        contract_address = result.stdout.split("Deployed to: ")[1].strip()
        print(f"[✓] Contract Deployed at: {contract_address}")
        return contract_address
    else:
        print("[!] Deployment Failed")
        print(result.stderr)
        return None

def verify_contract(contract_address, name):
    option = input("Do you want to verify the contract on Monad Explorer? (yes/no): ")
    if option.lower() == "yes":
        print("[+] Verifying Contract...")
        verify_cmd = [
            "forge", "verify-contract",
            "--rpc-url", RPC_URL,
            "--private-key", PRIVATE_KEY,
            "--etherscan-api-key", ETHERSCAN_API_KEY,
            contract_address,
            f"contracts/{name}.sol:{name}"
        ]
        subprocess.run(verify_cmd, check=True)
        print("[✓] Contract Verified")
    else:
        print("[!] Verification Skipped")

def mint_tokens(contract_address):
    option = input("Do you want to mint tokens? (yes/no): ")
    if option.lower() == "yes":
        amount = input("Enter mint amount: ")
        print(f"[+] Minting {amount} Tokens...")
        print("[✓] Tokens Minted")
    else:
        print("[!] Mint Skipped")

def burn_tokens():
    option = input("Do you want to burn tokens? (yes/no): ")
    if option.lower() == "yes":
        amount = input("Enter burn amount: ")
        print(f"[+] Burning {amount} Tokens...")
        print("[✓] Tokens Burned")
    else:
        print("[!] Burn Skipped")

def renounce_ownership():
    option = input("Do you want to renounce ownership? (yes/no): ")
    if option.lower() == "yes":
        print("[+] Renouncing Ownership...")
        print("[✓] Ownership Renounced")
    else:
        print("[!] Ownership Not Renounced")

if __name__ == "__main__":
    name = input("Enter your smart contract name: ")
    symbol = input("Enter your token symbol: ")
    supply = input("Enter your total supply: ")

    generate_contract(name, symbol, supply)
    compile_contract()
    contract_address = deploy_contract(name)

    if contract_address:
        verify_contract(contract_address, name)
        mint_tokens(contract_address)
        burn_tokens()
        renounce_ownership()
