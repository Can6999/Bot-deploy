import os
import subprocess
from web3 import Web3
from eth_account import Account

# --- Helper Functions for Keys and Chains ---

def load_keys(filename="keys.txt"):
    """
    Load private keys from keys.txt.
    Expected format: label=private_key (ignores comments and blank lines).
    """
    keys = {}
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                label, key_value = line.split("=", 1)
                keys[label.strip()] = key_value.strip()
    return keys

def select_key():
    """
    Prompt the user to select one of the available keys.
    Returns a tuple: (selected_key_label, private_key)
    """
    keys = load_keys()
    if not keys:
        print("[!] No keys found in keys.txt")
        exit(1)
    key_labels = list(keys.keys())
    if len(key_labels) == 1:
        label = key_labels[0]
        print(f"[✓] Using the only available key: {label}")
        return label, keys[label]
    else:
        print("\n=== Select Private Key ===")
        for idx, label in enumerate(key_labels, start=1):
            print(f"{idx}. {label}")
        choice = input(f"Select a key (1-{len(key_labels)}): ")
        try:
            choice = int(choice)
            if 1 <= choice <= len(key_labels):
                selected_label = key_labels[choice - 1]
                print(f"[✓] Selected key: {selected_label}")
                return selected_label, keys[selected_label]
            else:
                print("[!] Invalid choice")
                exit(1)
        except ValueError:
            print("[!] Invalid input. Please enter a number.")
            exit(1)

def load_chains(filename="chains.txt"):
    """
    Load chain configurations from chains.txt.
    Each chain block is separated by a blank line and must include a 'name' field.
    """
    chains = {}
    with open(filename, "r") as f:
        block = {}
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                if block:
                    if "name" in block:
                        chains[block["name"]] = block
                    block = {}
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                block[key.strip()] = value.strip()
        if block and "name" in block:
            chains[block["name"]] = block
    return chains

def select_chain():
    chains = load_chains()
    if not chains:
        print("[!] No chains found in chains.txt")
        exit(1)
    chain_names = list(chains.keys())
    if len(chain_names) == 1:
        selected = chain_names[0]
        print(f"[✓] Using the only available chain: {selected}")
        return chains[selected]
    else:
        print("\n=== Select Blockchain Network ===")
        for idx, name in enumerate(chain_names, start=1):
            print(f"{idx}. {name}")
        choice = input(f"Select a chain (1-{len(chain_names)}): ")
        try:
            choice = int(choice)
            if 1 <= choice <= len(chain_names):
                selected = chain_names[choice - 1]
                print(f"[✓] Selected chain: {selected}")
                return chains[selected]
            else:
                print("[!] Invalid choice")
                exit(1)
        except ValueError:
            print("[!] Invalid input. Please enter a number.")
            exit(1)

# --- Token Storage Functions ---

# Updated common file storage: now storing key_label, chain_name, token_name, contract_address, verification_status.
def store_contract_info_single(token_name, contract_address, key_label, chain_name, filename="contract_info.txt"):
    with open(filename, "a") as f:
        f.write(f"{key_label},{chain_name},{token_name},{contract_address},unverified\n")

def list_contract_info_single(filename="contract_info.txt", key_label=None, chain_name=None):
    tokens = []
    if os.path.exists(filename):
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    # Expected format: key_label, chain_name, token_name, contract_address, status
                    parts = line.split(",", 4)
                    if len(parts) == 5:
                        stored_key, stored_chain, token_name, contract_address, status = parts
                    elif len(parts) == 4:
                        # Fallback if chain wasn't recorded
                        stored_key, token_name, contract_address, status = parts
                        stored_chain = None
                    else:
                        continue
                    if ((key_label is None or stored_key == key_label) and 
                        (chain_name is None or stored_chain == chain_name)):
                        tokens.append((token_name, contract_address, status))
    return tokens

def get_tokens_filename(key_label):
    return f"tokens_{key_label}.txt"

# Updated separate file storage: now storing chain_name, token_name, contract_address, verification_status.
def store_contract_info_separate(token_name, contract_address, key_label, chain_name):
    filename = get_tokens_filename(key_label)
    with open(filename, "a") as f:
        f.write(f"{chain_name},{token_name},{contract_address},unverified\n")

def list_contract_info_separate(key_label, chain_name):
    tokens = []
    filename = get_tokens_filename(key_label)
    if os.path.exists(filename):
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    # Expected format: chain_name, token_name, contract_address, status
                    parts = line.split(",", 3)
                    if len(parts) == 4:
                        stored_chain, token_name, contract_address, status = parts
                    elif len(parts) == 3:
                        stored_chain, token_name, contract_address = parts
                        status = "unverified"
                    else:
                        continue
                    if chain_name is None or stored_chain == chain_name:
                        tokens.append((token_name, contract_address, status))
    return tokens

# Updated status updater to handle both storage formats.
def update_contract_status_in_file(filename, contract_address, new_status):
    if not os.path.exists(filename):
        return
    updated_lines = []
    with open(filename, "r") as f:
        for line in f:
            line_strip = line.strip()
            if not line_strip:
                continue
            parts = line_strip.split(",")
            # For common file: key_label, chain_name, token_name, contract_address, status (length 5)
            if len(parts) == 5:
                if parts[3] == contract_address:
                    parts[4] = new_status
                    updated_line = ",".join(parts) + "\n"
                    updated_lines.append(updated_line)
                else:
                    updated_lines.append(line)
            # For separate file: chain_name, token_name, contract_address, status (length 4)
            elif len(parts) == 4:
                if parts[2] == contract_address:
                    parts[3] = new_status
                    updated_line = ",".join(parts) + "\n"
                    updated_lines.append(updated_line)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
    with open(filename, "w") as f:
        f.writelines(updated_lines)

def update_verified_status(contract_address, key_label):
    # Update both storage files for the given contract address.
    update_contract_status_in_file("contract_info.txt", contract_address, "verified")
    update_contract_status_in_file(get_tokens_filename(key_label), contract_address, "verified")

# --- Set Up Environment Based on User Selections ---

selected_key_label, PRIVATE_KEY = select_key()
account = Account.from_key(PRIVATE_KEY)

chain_config = select_chain()
RPC_URL = chain_config["RPC_URL"]
CHAIN_ID = int(chain_config["CHAIN_ID"])
ETHERSCAN_API_KEY = chain_config.get("ETHERSCAN_API_KEY", "")

web3 = Web3(Web3.HTTPProvider(RPC_URL))

# --- Smart Contract Template ---

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

# File to save deployed token info for the common file approach.
CONTRACT_INFO_FILE = "contract_info.txt"

# --- Deployment and Post-Deployment Functions ---

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
    if result.stderr:
        print("Deployment Error Output:")
        print(result.stderr)
    if "Deployed to:" in result.stdout:
        contract_address = result.stdout.split("Deployed to: ")[1].split("\n")[0].strip()
        print(f"[✓] Contract Deployed at: {contract_address}")
        return contract_address
    else:
        print("[!] Deployment Failed")
        return None

def verify_contract(contract_address, name, prompt_for_verification=True):
    """
    Verify the contract using Etherscan if available, otherwise use Sourcify.
    If prompt_for_verification is True, ask the user before verifying.
    """
    if prompt_for_verification:
        option = input("Do you want to verify the contract? (yes/no): ")
        if option.lower() != "yes":
            print("[!] Verification Skipped")
            return
    print("[+] Verifying Contract...")
    if ETHERSCAN_API_KEY:
        print("[+] Using Etherscan verification for chain:", chain_config["name"])
        verify_cmd = [
            "forge", "verify-contract",
            contract_address,
            f"contracts/{name}.sol:{name}",
            "--chain", chain_config["name"],
            "--etherscan-api-key", ETHERSCAN_API_KEY,
            "--rpc-url", RPC_URL,
        ]
    else:
        verifier_url = chain_config.get("VERIFIER_URL", "https://sourcify-api-monad.blockvision.org")
        print("[+] Using Sourcify verification for chain:", chain_config["name"])
        print("[+] Verifier URL:", verifier_url)
        verify_cmd = [
            "forge", "verify-contract",
            contract_address,
            f"contracts/{name}.sol:{name}",
            "--rpc-url", RPC_URL,
            "--verifier", "sourcify",
            "--verifier-url", verifier_url
        ]
    subprocess.run(verify_cmd, check=True)
    print("[✓] Contract Verified")
    update_verified_status(contract_address, selected_key_label)

def prompt_valid_address(message):
    """Prompt the user for an address until a valid Ethereum address is provided."""
    while True:
        addr = input(message).strip()
        if web3.is_address(addr):
            return web3.to_checksum_address(addr)
        else:
            print("Invalid address. Please enter a valid Ethereum address.")

def mint_tokens(contract_address):
    recipient = prompt_valid_address("Enter recipient address for minting: ")
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

# --- Post Deployment Actions Menu ---
def post_deployment_actions(contract_address, name):
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
        print("5. Verify contract")  # New option for verifying unverified contracts
        print("0. Exit post deployment actions")
        choice = input("Select an action (0-5): ")
        if choice == "1":
            mint_tokens(contract_address)
        elif choice == "2":
            burn_tokens(contract_address)
        elif choice == "3":
            renounce_ownership(contract_address)
        elif choice == "4":
            transfer_tokens(contract_address)
        elif choice == "5":
            # Directly verify the contract without an extra prompt
            verify_contract(contract_address, name, prompt_for_verification=False)
        elif choice == "0":
            confirm = input("Are you sure you want to exit post deployment actions? (yes/no): ")
            if confirm.lower() == "yes":
                print("Exiting current post deployment session...")
                break
            else:
                print("Continuing post deployment actions...")
        else:
            print("Invalid choice. Please select a valid option.")

# --- Main Program Execution ---

if __name__ == "__main__":
    install_foundry_dependencies()

    # --- Listing previously deployed tokens (filtered by chain) ---
    tokens_common = list_contract_info_single(filename=CONTRACT_INFO_FILE, key_label=selected_key_label, chain_name=chain_config["name"])
    tokens_separate = list_contract_info_separate(selected_key_label, chain_config["name"])

    if tokens_common or tokens_separate:
        print("Found deployed tokens for your selected key on", chain_config["name"] + ":")
        if tokens_common:
            print("\n-- Common File Storage --")
            for idx, (token_name, contract_address, status) in enumerate(tokens_common, start=1):
                print(f"{idx}. {token_name} at {contract_address} [{status}]")
        if tokens_separate:
            print("\n-- Separate File Storage --")
            for idx, (token_name, contract_address, status) in enumerate(tokens_separate, start=1):
                print(f"{idx}. {token_name} at {contract_address} [{status}]")
        print("0. Deploy a new token")
        choice = input("Select a token to resume post deployment actions (or 0 to deploy new): ")
        if choice != "0":
            try:
                idx = int(choice) - 1
                tokens = tokens_common if tokens_common else tokens_separate
                if 0 <= idx < len(tokens):
                    token_name_saved, contract_address_saved, status = tokens[idx]
                    print(f"Resuming post deployment actions for {token_name_saved} at {contract_address_saved} [{status}]")
                    while True:
                        post_deployment_actions(contract_address_saved, token_name_saved)
                        resume = input("Would you like to resume post deployment actions for this token? (yes/no): ")
                        if resume.lower() != "yes":
                            print("Exiting all post deployment actions.")
                            break
                    exit()
                else:
                    print("Invalid selection. Proceeding to new deployment...")
            except ValueError:
                print("Invalid selection. Proceeding to new deployment...")

    # --- Deploy a new token if not resuming ---
    name = input("Enter your smart contract name: ").replace(" ", "_")
    symbol = input("Enter your token symbol: ")
    generate_contract(name, symbol)
    compile_contract()
    contract_address = deploy_contract(name)
    if contract_address:
        # Save token info using both approaches.
        store_contract_info_single(name, contract_address, selected_key_label, chain_config["name"], filename=CONTRACT_INFO_FILE)
        store_contract_info_separate(name, contract_address, selected_key_label, chain_config["name"])
        verify_contract(contract_address, name)  # Initial verification prompt
        
        # Outer loop: allow re-entry into post deployment actions.
        while True:
            post_deployment_actions(contract_address, name)
            resume = input("Would you like to resume post deployment actions for this token? (yes/no): ")
            if resume.lower() != "yes":
                print("Exiting all post deployment actions.")
                break
