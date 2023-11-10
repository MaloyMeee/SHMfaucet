import telebot
from telegram.ext import *
from web3 import Web3
import sqlite3
from os.path import isfile
from settings import *
from abi import TOKEN_ABI


def main():
    createDataBase()
    print("Started")
    updater = Updater(TG_BOT_KEY, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("claim", shm_command))
    dp.add_handler(CommandHandler("checkaddr", check_command))
    dp.add_handler(CommandHandler("checkfaucetbalance", check_faucet))
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


def get_balabce(wallet):
    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    balance = web3.eth.get_balance(wallet)
    return (f"Balance: {web3.from_wei(balance, 'ether')}")


def getTokenBalance(account, token_addr):
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    token_addr = Web3.to_checksum_address(token_addr)
    contractToken = w3.eth.contract(address=token_addr, abi=TOKEN_ABI)
    account = Web3.to_checksum_address(account)
    balance = contractToken.caller().balanceOf(account)
    return (w3.from_wei(balance, 'ether'))


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
        print(f"ERROR: {e}\nContinue...")
        delete_user_from_db(account)
        return ("Something went wrong")


def ping_admin_dm(message):
    bot = telebot.TeleBot(TG_BOT_KEY)
    bot.send_message(admin_user_id, message)


def isLowOnGas(wallet, userId):
    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    balance = web3.eth.get_balance(wallet)
    if userId == admin_user_id:
        return True
    elif balance < 0.003:
        return True
    return False


def delete_user_from_db(wallet):
    conn = sqlite3.connect(DATABASE_FILE).cursor()
    conn.execute("DELETE FROM faucetClaims WHERE ADDR = '" + wallet + "'")


def isEligible(userId, wallet):
    conn = sqlite3.connect(DATABASE_FILE).cursor()
    conn.execute("SELECT 1 FROM faucetClaims WHERE (USER_ID = " + str(
        userId) + " OR ADDR = '" + wallet + "') AND DT > julianday('now', '-24 hours') ")
    rows = conn.fetchall()
    if userId == admin_user_id:
        return True
    elif (len(rows)) == 0:
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


def check_command(update, context):
    context.bot.send_message(update.message.chat.id,
                             get_balabce(update['message']['text'].split(' ')[1]),
                             parse_mode='HTML',
                             disable_web_page_preview=True)


def check_faucet(update, context):
    context.bot.send_message(update.message.chat.id,
                             get_balabce(WALLET_ADDR),
                             parse_mode='HTML',
                             disable_web_page_preview=True)


if __name__ == '__main__':
    main()
