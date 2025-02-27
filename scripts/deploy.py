import os
import subprocess
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
    constructor() ERC20("{name}", "{symbol}") Ownable(msg.sender) {{
        _mint(msg.sender, {supply} * 10 ** decimals());
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


def install_foundry_dependencies():
    if os.path.exists("requirements.forge"):
        print("[+] Installing Foundry Dependencies...")
        subprocess.run(["forge", "install"], check=True)
        print("[✓] Foundry Dependencies Installed")

def generate_contract(name, symbol, supply):
    print(f"[+] Generating {name} Smart Contract...")
    contract_code = CONTRACT_TEMPLATE.format(name=name, symbol=symbol, supply=supply)

    os.makedirs("contracts", exist_ok=True)
    with open(f"contracts/{name}.sol", "w") as file:
        file.write(contract_code)
    print(f"[✓] Contract {name}.sol Generated")

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
        "--broadcast",
        "--force",  # Force broadcasting even if Foundry thinks nothing has changed
        f"contracts/{name}.sol:{name}"
    ]
    result = subprocess.run(deploy_cmd, capture_output=True, text=True)
    print("Deployment Output:")
    print(result.stdout)
    print("Deployment Errors:")
    print(result.stderr)
    
    if "Deployed to:" in result.stdout:
        contract_address = result.stdout.split("Deployed to: ")[1].strip()
        print(f"[✓] Contract Deployed at: {contract_address}")
        return contract_address
    else:
        print("[!] Deployment output did not include the expected 'Deployed to:' string.")
        return None




def verify_contract(contract_address, name):
    option = input("Do you want to verify the contract? (yes/no): ")
    if option.lower() == "yes":
        print("[+] Verifying Contract...")
        verify_cmd = [
            "forge", "verify-contract",
            "--private-key", PRIVATE_KEY,
            "--etherscan-api-key", ETHERSCAN_API_KEY,
            contract_address,
            f"contracts/{name}.sol:{name}"
        ]
        subprocess.run(verify_cmd, check=True)
        print("[✓] Contract Verified")
    else:
        print("[!] Verification Skipped")

if __name__ == "__main__":
    install_foundry_dependencies()
    
    name = input("Enter your smart contract name: ").replace(" ", "_")
    symbol = input("Enter your token symbol: ")
    supply = input("Enter your total supply: ")

    generate_contract(name, symbol, supply)
    compile_contract()
    contract_address = deploy_contract(name)

    if contract_address:
        verify_contract(contract_address, name)
