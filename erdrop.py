import requests
import re
import time
import logging
from eth_account import Account
from web3 import Web3

logging.basicConfig(filename='claim_tokens.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s')

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
            logging.info("Token claim successful!")
            return True
        else:
            logging.error("Token claim failed.")
            return False
    except Exception as e:
        logging.error(f"An error occurred while claiming tokens: {str(e)}")
        return False

def display_separator():
    logging.info("-" * 50)

private_key = input("Enter your private key: ")
meta_mask_address = Account.from_key(private_key).address

onfinality_api_url = 'https://mint.club/api/distribution?chainId=666666666&isPublic=true'
retry_count = 3
while retry_count > 0:
    try:
        response_onfinality = requests.get(onfinality_api_url, timeout=10)  # Set timeout to prevent hanging
        if response_onfinality.ok:
            onfinality_data = response_onfinality.json()
            if isinstance(onfinality_data, list) and len(onfinality_data) > 0:
                for entry in onfinality_data:
                    pattern = re.compile(r'2024-03-30')
                    if pattern.search(entry.get("updatedAt")):
                        claimed_count = entry.get("claimedCount")
                        if claimed_count == 0 and entry.get("walletCount"):  # Check if walletCount has value
                            display_separator()
                            logging.info("New Token Available!")
                            display_separator()
                            message = f"Address token: {entry.get('tokenAddress')}\n" \
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
                            logging.info("Attempting to claim tokens...")
                            if claim_tokens(private_key):
                                logging.info(f"Token claim successful for token: {token_symbol} with value: {entry.get('walletCount')}")
                            else:
                                logging.error("Token claim failed.")
                            time.sleep(3)  # Delay for 3 seconds
            else:
                logging.error("Error: No data available from the OnFinality API.")
            break  # Exit the retry loop if successful
        else:
            logging.error("Failed to retrieve data from the OnFinality API.")
            retry_count -= 1
            time.sleep(5)  # Wait before retrying
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {str(e)}")
        retry_count -= 1
        time.sleep(5)  # Wait before retrying

if retry_count == 0:
    logging.error("Failed to retrieve data after multiple retries. Exiting.")
