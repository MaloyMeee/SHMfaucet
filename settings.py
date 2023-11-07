from web3 import Web3
from web3.middleware import geth_poa_middleware

RPC_URL = "https://dapps.shardeum.org"
web3 = Web3(Web3.HTTPProvider(RPC_URL))
admin_user_id = 
def get_private():
    web3.eth.account.enable_unaudited_hdwallet_features()
    account = web3.eth.account.from_mnemonic("around brother lens ...")
    private_key = account._private_key
    return private_key

TG_BOT_KEY = ""
WALLET_ADDR = ""
WALLET_PK = get_private()
DATABASE_FILE = "faucet.db"
