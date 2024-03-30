import urllib3
import requests
import re
import time
import logging
from eth_account import Account
from web3 import Web3
import colorlog

# Setup colorlog
logger = colorlog.getLogger()
logger.setLevel(logging.INFO)

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
))
logger.addHandler(handler)

def save_message_to_file(message):
    with open('messages.txt', 'a', encoding='utf-8') as file:
        file.write(message + '\n')

def claim_tokens(private_key):
    try:
        web3 = Web3(Web3.HTTPProvider('https://rpc.degen.tips'))
        gas_price = web3.eth.gas_price  # Get current gas price
        account = Account.from_key(private_key)  # Create account object from private key
        nonce = web3.eth.get_transaction_count(account.address)
        tx = {
            'chainId': 666666666,  # Chain ID for Degen
            'gas': 1000000,
            'gasPrice': gas_price,  # Use current gas price
            'nonce': nonce,
        }
        signed_tx = web3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            logger.info("Token claim successful!")
            return True
        else:
            logger.error("Token claim failed.")
            return False
    except Exception as e:
        logger.error(f"An error occurred while claiming tokens: {str(e)}")
        return False

def display_separator():
    logger.info("-" * 50)

private_key = input("Enter your private key: ")
meta_mask_address = Account.from_key(private_key).address

claimed_tokens = set()  # Set to store claimed tokens

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

onfinality_api_url = 'https://mint.club/api/distribution?chainId=666666666&isPublic=true'
session = requests.Session()  # Create session outside the loop
total_claimed_tokens = 0  # Variable to store total claimed tokens

while True:  # Continuous loop until all tokens are claimed
    try:
        response_onfinality = session.get(onfinality_api_url, timeout=10, verify=False)  # Set timeout to prevent hanging and disable SSL verification
        if response_onfinality.ok:
            onfinality_data = response_onfinality.json()
            if isinstance(onfinality_data, list) and len(onfinality_data) > 0:
                new_tokens_available = False  # Flag to check if new tokens are available
                for entry in onfinality_data:
                    pattern = re.compile(r'2024-03-30')
                    if pattern.search(entry.get("updatedAt")):
                        claimed_count = entry.get("claimedCount")
                        token_address = entry.get("tokenAddress")
                        if claimed_count == 0 and entry.get("walletCount") and token_address not in claimed_tokens:  # Check if walletCount has value and token has not been claimed
                            new_tokens_available = True  # Set flag to True
                            display_separator()
                            logger.info("New Token Available!")
                            display_separator()
                            message = f"Address token: {token_address}\n" \
                                      f"Maximal claim: {entry.get('walletCount')}\n" \
                                      f"claimedCount: EARLY CLAIM\n" \
                                      f"Title token: {entry.get('title')}\n" \
                                      f"Time update: {entry.get('updatedAt')}\n"
                            token = entry.get("token")
                            if isinstance(token, dict):
                                token_symbol = token.get("symbol")
                                message += f"Token Symbol: {token_symbol}\n" \
                                           f"Buy Token: https://mint.club/token/degen/{token_symbol}\n"
                            save_message_to_file(message)
                            logger.info("Attempting to claim tokens...")
                            if claim_tokens(private_key):
                                logger.info(f"Token claim successful for token: {token_symbol} with value: {entry.get('walletCount')}")
                                claimed_tokens.add(token_address)  # Add claimed token to set
                                total_claimed_tokens += 1  # Increment total claimed tokens
                            else:
                                logger.error("Token claim failed.")
                            time.sleep(3)  # Delay for 3 seconds
                
                # If no new tokens are available, break the loop
                if not new_tokens_available:
                    logger.info(f"No new tokens available. Total claimed tokens: {total_claimed_tokens}")
                    break
            else:
                logger.error("Error: No data available from the OnFinality API.")
                break
        else:
            logger.error("Failed to retrieve data from the OnFinality API.")
            time.sleep(5)  # Wait before retrying
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        time.sleep(5)  # Wait before retrying
