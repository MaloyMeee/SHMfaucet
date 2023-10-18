import telebot
import telegram
from telegram.ext import *
from web3 import Web3
import sqlite3
from os.path import isfile
from settings import *
from abi import TOKEN_ABI


def main():
    createDataBase()
    print("Started")
    bot = telegram.Bot(token=TG_BOT_KEY)
    updater = Updater(bot=bot, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("dclaim", shm_command))
    updater.start_polling()
    updater.idle()

def createDataBase():
    if isfile(DATABASE_FILE):
        print("Database exists...")
        ping_admin_dm("Database exists...")
    else:
        print("Creating Database...")
        executeNonQuery("CREATE TABLE faucetClaims (USER_ID INTEGER, ADDR TEXT, DT FLOAT);")
        print("Database created successfully")
        ping_admin_dm("Database created successfully")


def getTokenBalance(account, token_addr):
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    token_addr = Web3.toChecksumAddress(token_addr)
    contractToken = w3.eth.contract(address=token_addr, abi=TOKEN_ABI)
    account = Web3.toChecksumAddress(account)
    balance = contractToken.caller().balanceOf(account)
    return (w3.fromWei(balance, 'ether'))


def sendSHM(account):
    try:
        web3 = Web3(Web3.HTTPProvider(RPC_URL))
        nonce = web3.eth.get_transaction_count(WALLET_ADDR)
        print(True)
        tx = {
            'nonce': nonce,
            'to': account,
            'value': web3.to_wei(12, 'ether'),
            'gas': 21000,
            'gasPrice': web3.to_wei('7', 'gwei')}

        signed_tx = web3.eth.account.sign_transaction(tx, WALLET_PK)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return (f"Хеш транзакции: {(web3.to_hex(tx_hash))}")
    except Exception as e:
        ping_admin_dm(f"ERROR: {e}")

def ping_admin_dm(message):
    bot = telebot.TeleBot(TG_BOT_KEY)
    bot.send_message(admin_user_id, message)


def isLowOnGas(wallet, user_id):
    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    balance = web3.eth.get_balance(wallet)
    if balance < 0.003 or user_id == admin_user_id:
        return True
    return False


def isEligible(userId, wallet):
    conn = sqlite3.connect(DATABASE_FILE).cursor()
    conn.execute("SELECT 1 FROM faucetClaims WHERE (USER_ID = " + str(
        userId) + " OR ADDR = '" + wallet + "') AND DT > julianday('now', '-24 hours') ")
    rows = conn.fetchall()
    if (len(rows)) == 0 or userId == admin_user_id:
        return True
    return False


def executeNonQuery(command):
    conn = sqlite3.connect(DATABASE_FILE)
    conn.execute(command)
    conn.commit()
    conn.close()


def gimmeFunds(userId, address):
    if not isLowOnGas(address, userId):
        return "You have enough funds!"
    if not isEligible(userId, address):
        return "You have used the Faucet recently!"
    executeNonQuery("INSERT INTO faucetClaims (USER_ID, ADDR, DT) VALUES (" + str(
        userId) + ", '" + address + "', julianday(('now')));")
    return sendSHM(address)


def shm_command(update, context):
    context.bot.send_message(update.message.chat.id,
                             gimmeFunds(update.message.from_user['id'], update['message']['text'].split(' ')[1]),
                             parse_mode='HTML',
                             disable_web_page_preview=True)


if __name__ == '__main__':
    main()
