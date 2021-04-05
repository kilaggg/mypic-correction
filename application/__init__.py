from algosdk import mnemonic
from algosdk.v2client import algod
from flask import Flask
# from flask_socketio import SocketIO
import os


app = Flask(__name__)
# socketio = SocketIO(app, logger=False, engineio_logger=False)
dict_bid = {}
dict_buy = {}

algod_address = os.environ['algod_address']
algod_token = os.environ['algod_token']
headers = {"X-API-Key": algod_token}
algod_client = algod.AlgodClient(algod_token=algod_token, algod_address=algod_address, headers=headers)

WORD_MNEMONIC = os.environ["mnemonic"]
accounts = {1: {'pk': mnemonic.to_public_key(WORD_MNEMONIC), 'sk': mnemonic.to_private_key(WORD_MNEMONIC)}}

CONNECTION_STRING = os.environ["database_conn"]
BLOB_CONNECTION_STRING = os.environ["blob_conn"]
LOGIC_APP_MAIL_URL = os.environ["insight_url"]
SWARM_URL_NODE = os.environ["swarm_node"]
ADDRESS_ALGO_OURSELF = mnemonic.to_public_key(WORD_MNEMONIC)
