import os
import subprocess
from web3 import Web3
from eth_account import Account
from can_utils import can

banner() 


# ----------------------------------------------------------------------
# 1) HELPER: get_input with Back Option
# ----------------------------------------------------------------------

def get_input(prompt, allow_back=True):
    """
    Prompts the user for input. If allow_back=True and the user types
    'b' or 'back', return None to signal a 'go back' request.
    """
    user_input = input(prompt).strip()
    if allow_back and user_input.lower() in ['b', 'back']:
        return None
    return user_input

# ----------------------------------------------------------------------
# 2) LOAD KEY & CHAIN CONFIGS
# ----------------------------------------------------------------------

def load_keys(filename="keys.txt"):
    """
    Load private keys from keys.txt.
    Expected format: label=private_key
    Lines starting with '#' or blank lines are ignored.
    """
    if not os.path.exists(filename):
        return {}
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
    Shows a list of private keys from keys.txt and allows the user to pick one.
    The user can also type 'b' to exit the program (since there's no previous menu).
    Returns the selected private key string or None if the user typed 'b'.
    """
    while True:
        keys = load_keys()
        if not keys:
            print("[!] No keys found in keys.txt")
            exit(1)
            
        key_labels = list(keys.keys())
        print("\n=== Select Private Key ===")
        for idx, label in enumerate(key_labels, start=1):
            print(f"{idx}. {label}")
        print("b. Back (Exit Program)")

        choice = get_input(f"Select a key (1-{len(key_labels)}) or 'b' to exit: ")
        if choice is None:                                                                          
            return None

        try:
            idx = int(choice)
            if 1 <= idx <= len(key_labels):                                                             
                selected_label = key_labels[idx - 1]
                print(f"[✓] Selected key: {selected_label}")
                return keys[selected_label]
            else:
                print("[!] Invalid choice. Please try again.")
        except ValueError:
            print("[!] Invalid input. Please enter a number or 'b' to exit.")

def load_chains(filename="chains.txt"):
    """
    Load chain configurations from chains.txt.
    Each chain block is separated by a blank line and must include a 'name' field.
    """
    if not os.path.exists(filename):
        return {}

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
    """
    Display a list of chains and let the user select one.
    The user may type 'b' to go back to key selection.
    Returns the chain config dict or None if user typed 'b'.
    """
    while True:
        chains = load_chains()
        if not chains:
            print("[!] No chains found in chains.txt")
            exit(1)

        chain_names = list(chains.keys())
        print("\n=== Select Blockchain Network ===")
        for idx, name in enumerate(chain_names, start=1):
            print(f"{idx}. {name}")
        print("b. Back (to Private Key selection)")

        choice = get_input(f"Select a chain (1-{len(chain_names)}) or 'b' to go back: ")
        if choice is None:
            return None

        try:
            idx = int(choice)
            if 1 <= idx <= len(chain_names):
                selected_name = chain_names[idx - 1]
                print(f"[✓] Selected chain: {selected_name}")
                return chains[selected_name]
            else:
                print("[!] Invalid choice. Please try again.")
        except ValueError:
            print("[!] Invalid input. Please enter a number or 'b' to go back.")

# ----------------------------------------------------------------------
# 3) SMART CONTRACT TEMPLATE
# ----------------------------------------------------------------------

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

CONTRACT_INFO_FILE = "contract_info.txt"

# ----------------------------------------------------------------------
# 4) DEPLOYMENT / VERIFICATION / POST-DEPLOYMENT
# ----------------------------------------------------------------------

def install_foundry_dependencies():
    if not os.path.exists("lib"):
        print("[+] Installing Foundry Dependencies...")
        subprocess.run(["forge", "install", "--no-commit"], check=True)
        print("[✓] Foundry Dependencies Installed")
    else:
        print("[✓] Foundry Dependencies Already Installed")

def generate_contract(name, symbol):
    print(f"[+] Generating {name} Smart Contract...")
    code = CONTRACT_TEMPLATE.format(name=name, symbol=symbol)
    os.makedirs("contracts", exist_ok=True)
    with open(f"contracts/{name}.sol", "w") as file:
        file.write(code)
    print(f"[✓] Contract {name}.sol Generated")

def compile_contract():
    print("[+] Compiling Contract...")
    if os.path.exists("out"):
        print("[+] Removing previous build files...")
        subprocess.run(["rm", "-rf", "out"])
        subprocess.run(["forge", "build"], check=True)
    print("[✓] Compilation Done")

def deploy_contract(rpc_url, private_key, name):
    print("[+] Deploying Contract...")
    deploy_cmd = [
        "forge", "create",
        "--rpc-url", rpc_url,
        "--private-key", private_key,
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

# ----------------------------------------------------------------------
# 5) STORING & UPDATING TOKEN INFO (with deployer field)
# ----------------------------------------------------------------------

def store_contract_info(chain_name, token_name, contract_address, deployer, verified_status="unverified"):
    """
    Append new token info to contract_info.txt in the format:
    chainName,tokenName,contractAddress,verificationStatus,deployerAddress
    """
    with open(CONTRACT_INFO_FILE, "a") as f:
        f.write(f"{chain_name},{token_name},{contract_address},{verified_status},{deployer}\n")

def list_contract_info(chain_name, deployer):
    """
    Return a list of (token_name, contract_address, verification_status)
    for tokens on the given chain_name deployed by the given deployer.
    """
    tokens = []
    if os.path.exists(CONTRACT_INFO_FILE):
        with open(CONTRACT_INFO_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split(",")
                    if len(parts) == 5:
                        stored_chain, token_name, contract_address, status, token_deployer = parts
                        if stored_chain == chain_name and token_deployer.lower() == deployer.lower():
                            tokens.append((token_name, contract_address, status))
    return tokens

def update_verification_status(chain_name, token_name, contract_address, deployer, new_status):
    if not os.path.exists(CONTRACT_INFO_FILE):
        return
    lines = []
    with open(CONTRACT_INFO_FILE, "r") as f:
        for line in f:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            parts = line_stripped.split(",")
            if len(parts) == 5:
                c, t, addr, s, d = parts
                if c == chain_name and t == token_name and addr.lower() == contract_address.lower() and d.lower() == deployer.lower():
                    lines.append(f"{c},{t},{addr},{new_status},{d}")
                else:
                    lines.append(line_stripped)
            else:
                lines.append(line_stripped)
    with open(CONTRACT_INFO_FILE, "w") as f:
        for l in lines:
            f.write(l + "\n")

# ----------------------------------------------------------------------
# 6) VERIFICATION & POST-DEPLOYMENT ACTIONS
# ----------------------------------------------------------------------

def verify_contract(rpc_url, chain_config, token_name, contract_address, deployer):
    """
    Verify the contract.
    If the chain is 'monad', use the custom Sourcify endpoint and source location 'src/<token_name>.sol'.
    Otherwise, use Etherscan verification.
    """
    chain_name = chain_config["name"]
    chain_id = str(chain_config["CHAIN_ID"])
    choice = get_input("Do you want to verify the contract? (yes/no or 'b' to go back): ")
    if choice is None:
        print("[!] Skipping verification. Going back.")
        return
    if choice.lower() != "yes":
        print("[!] Verification Skipped")
        return

    print("[+] Verifying Contract...")

    if "monad" in chain_name.lower():
        # For Monad, use the updated command: note the source file path is in "contracts/"
        verify_cmd = [
            "forge", "verify-contract",
            contract_address,
            f"contracts/{token_name}.sol:{token_name}",
            "--rpc-url", rpc_url,
            "--chain-id", chain_id,
            "--verifier", "sourcify",
            "--verifier-url", "https://sourcify-api-monad.blockvision.org"
        ]
    else:
        verifier = "etherscan"
        etherscan_api_key = chain_config["ETHERSCAN_API_KEY"]
        etherscan_api_url = chain_config.get("ETHERSCAN_API_URL", "")
        verify_cmd = [
            "forge", "verify-contract",
            contract_address,
            f"contracts/{token_name}.sol:{token_name}",
            "--rpc-url", rpc_url,
            "--verifier", verifier,
            "--etherscan-api-key", etherscan_api_key,
            "--chain-id", chain_id,
        ]
        if etherscan_api_url:
            verify_cmd += ["--etherscan-api-url", etherscan_api_url]

    result = subprocess.run(verify_cmd, capture_output=True, text=True)
    print("Verification Output:")
    print(result.stdout)
    if result.stderr:
        print("Verification Error:")
        print(result.stderr)

    if result.returncode == 0:
        print(f"[✓] Contract Verified on {chain_name}")
        update_verification_status(chain_name, token_name, contract_address, deployer, "verified")
    else:
        print("[!] Verification failed. Check the error messages above.")

def init_web3(rpc_url, private_key):
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    acct = Account.from_key(private_key)
    return w3, acct

def prompt_valid_address(w3, prompt_msg):
    while True:
        addr = get_input(prompt_msg)
        if addr is None:
            return None
        if w3.is_address(addr):
            return w3.to_checksum_address(addr)
        else:
            print("Invalid address. Please enter a valid Ethereum address or 'b' to go back.")

def mint_tokens(w3, acct, chain_id, contract_address, private_key):
    recipient = prompt_valid_address(w3, "Enter recipient address (or 'b' to go back): ")
    if recipient is None:
        return
    amount = get_input("Enter amount to mint (or 'b' to go back): ")
    if amount is None:
        return
    print(f"[+] Minting {amount} tokens to {recipient}...")
    mint_selector = w3.keccak(text="mint(address,uint256)")[:4]
    encoded_recipient = bytes.fromhex(recipient[2:]).rjust(32, b'\0')
    encoded_amount = int(amount).to_bytes(32, 'big')
    data = mint_selector + encoded_recipient + encoded_amount
    tx = {
        "to": contract_address,                                                                                                                                                          
        "data": data,
        "gas": 100000,
        "maxFeePerGas": w3.to_wei("57", "gwei"),
        "maxPriorityFeePerGas": w3.to_wei("50", "gwei"),
        "chainId": chain_id,
        "nonce": w3.eth.get_transaction_count(acct.address),
    }
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"[✓] Mint Transaction Hash: {w3.to_hex(tx_hash)}")

def burn_tokens(w3, acct, chain_id, contract_address, private_key):
    amount = get_input("Enter amount to burn (or 'b' to go back): ")
    if amount is None:
        return
    print(f"[+] Burning {amount} tokens...")
    burn_selector = w3.keccak(text="burn(uint256)")[:4]
    encoded_amount = int(amount).to_bytes(32, 'big')                                                                                                                                 
    data = burn_selector + encoded_amount
    tx = {
        "to": contract_address,
        "data": data,
        "gas": 100000,
        "maxFeePerGas": w3.to_wei("57", "gwei"),
        "maxPriorityFeePerGas": w3.to_wei("50", "gwei"),
        "chainId": chain_id,
        "nonce": w3.eth.get_transaction_count(acct.address),
        }
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"[✓] Burn Transaction Hash: {w3.to_hex(tx_hash)}")

def renounce_ownership(w3, acct, chain_id, contract_address, private_key):
    print("[+] Renouncing Ownership...")
    renounce_selector = w3.keccak(text="renounce()")[:4]
    tx = {
        "to": contract_address,
        "data": renounce_selector,
        "gas": 100000,
        "maxFeePerGas": w3.to_wei("57", "gwei"),
        "maxPriorityFeePerGas": w3.to_wei("50", "gwei"),
        "chainId": chain_id,
        "nonce": w3.eth.get_transaction_count(acct.address),
    }
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"[✓] Renounce Ownership Transaction Hash: {w3.to_hex(tx_hash)}")

def transfer_tokens(w3, acct, chain_id, contract_address, private_key):
    recipient = prompt_valid_address(w3, "Enter the recipient address (or 'b' to go back): ")
    if recipient is None:
        return
    amount = get_input("Enter the amount to transfer (or 'b' to go back): ")
    if amount is None:
        return
    print(f"[+] Transferring {amount} tokens to {recipient}...")
    transfer_selector = w3.keccak(text="transfer(address,uint256)")[:4]
    encoded_recipient = bytes.fromhex(recipient[2:]).rjust(32, b'\0')
    encoded_amount = int(amount).to_bytes(32, 'big')
    data = transfer_selector + encoded_recipient + encoded_amount
    tx = {
        "to": contract_address,
        "data": data,
        "gas": 100000,
        "maxFeePerGas": w3.to_wei("57", "gwei"),
        "maxPriorityFeePerGas": w3.to_wei("50", "gwei"),
        "chainId": chain_id,
        "nonce": w3.eth.get_transaction_count(acct.address),
    }
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"[✓] Transfer Transaction Hash: {w3.to_hex(tx_hash)}")

def post_deployment_actions(w3, acct, chain_id, contract_address, private_key):
    while True:
        print("\n=== Post Deployment Actions ===")
        print("1. Mint tokens")
        print("2. Burn tokens")
        print("3. Renounce ownership")
        print("4. Transfer tokens")
        print("b. Back to previous menu")
        choice = get_input("Select an action (1-4) or 'b' to go back: ")
        if choice is None:
            print("Returning to previous menu...")
            break
        if choice == "1":
            mint_tokens(w3, acct, chain_id, contract_address, private_key)
        elif choice == "2":
            burn_tokens(w3, acct, chain_id, contract_address, private_key)
        elif choice == "3":
            renounce_ownership(w3, acct, chain_id, contract_address, private_key)
        elif choice == "4":
            transfer_tokens(w3, acct, chain_id, contract_address, private_key)
        else:
            print("[!] Invalid choice. Please select a valid option.")

# ----------------------------------------------------------------------
# 7) MAIN PROGRAM: NESTED LOOPS
# ----------------------------------------------------------------------

def main():
    install_foundry_dependencies()

    while True:
        # A) KEY SELECTION
        private_key = select_key()
        if private_key is None:
            print("Exiting program. Goodbye!")
            return

        while True:
            # B) CHAIN SELECTION
            chain_config = select_chain()
            if chain_config is None:
                print("Returning to key selection...\n")
                break                                                                                                                                                            
            rpc_url = chain_config["RPC_URL"]
            chain_id = int(chain_config["CHAIN_ID"])
            chain_name = chain_config["name"]

            # Initialize web3 + account (deployer)
            w3, acct = init_web3(rpc_url, private_key)
            deployer = acct.address

            while True:                                                                                                                                                                          
                # C) TOKEN MENU (now filtering tokens by chain AND deployer)
                tokens = list_contract_info(chain_name, deployer)
                if tokens:
                    print(f"\nFound the following deployed tokens on {chain_name} by {deployer}:")
                    for idx, (tname, taddr, status) in enumerate(tokens, start=1):
                        print(f"{idx}. {tname} at {taddr} [{status}]")
                else:
                    print(f"\nNo tokens found on {chain_name} yet for deployer {deployer}.")
                    print("b. Back to chain selection")
                    print("Or press Enter to deploy a new token.")
                                                                                                                                                                                                 
                choice = get_input("Select a token index to resume, 'b' to go back, or Enter to deploy new: ", allow_back=True)
                if choice is None:                                                                                                                                                                   
                    print("Returning to chain selection...\n")
                    break

                if choice == "":
                    # Deploy new token                                                                                                                                                               
                    token_name = get_input("Enter your smart contract name (or 'b' to go back): ")
                    if token_name is None:
                        print("Returning to token menu...\n")
                        continue
                    token_name = token_name.replace(" ", "_")

                    symbol = get_input("Enter your token symbol (or 'b' to go back): ")
                    if symbol is None:
                        print("Returning to token menu...\n")
                        continue

                    generate_contract(token_name, symbol)
                    compile_contract()
                    contract_address = deploy_contract(rpc_url, private_key, token_name)
                    if contract_address:
                        store_contract_info(chain_name, token_name, contract_address, deployer, "unverified")
                        verify_contract(rpc_url, chain_config, token_name, contract_address, deployer)
                        while True:
                            post_deployment_actions(w3, acct, chain_id, contract_address, private_key)
                            resume = get_input("Resume actions for this token? (yes/no or 'b' to go back): ")
                            if resume is None or resume.lower() in ['b','back','no']:
                                print("Returning to token menu...\n")
                                break
                    else:
                        print("[!] Deployment failed or canceled.")
                else:
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(tokens):
                            token_name_saved, contract_address_saved, status = tokens[idx]
                            print(f"\n[+] Resuming post-deployment actions for {token_name_saved} at {contract_address_saved} [{status}]")
                            if status.lower() == "unverified":
                                verify_contract(rpc_url, chain_config, token_name_saved, contract_address_saved, deployer)
                            while True:
                                post_deployment_actions(w3, acct, chain_id, contract_address_saved, private_key)
                                resume = get_input("Resume actions for this token? (yes/no or 'b' to go back): ")
                                if resume is None or resume.lower() in ['b','back','no']:
                                    print("Returning to token menu...\n")
                                    break
                        else:
                            print("[!] Invalid selection.")
                    except ValueError:
                        print("[!] Invalid selection.")
    print("Exiting program. Goodbye!")

# ----------------------------------------------------------------------
# 8) ENTRY POINT
# ----------------------------------------------------------------------

if __name__ == "__main__":
    main()
