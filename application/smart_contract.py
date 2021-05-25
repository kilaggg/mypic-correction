from algosdk import mnemonic, template, transaction, logic, error, encoding
from algosdk.error import AlgodHTTPError
from algosdk.future.transaction import AssetConfigTxn, AssetTransferTxn, PaymentTxn, AssetFreezeTxn
from application import accounts, ADDRESS_ALGO_OURSELF, algod_client, WORD_MNEMONIC
from application.constants import CONVERT_TO_MICRO, PRICE_GET_BACK
from binascii import unhexlify
import base64
import json
import base58


def check_algo_for_tx(address: str, micro_algo: int, optin: bool):
    """

    :param address:
    :param micro_algo:
    :param optin: True if token already in account
    :return:
    """
    number_asset = len(algod_client.account_info(address)['assets'])
    number_algo_freeze = 100000 + 100000 * number_asset
    number_algo = algod_client.account_info(address)['amount']
    algo_needed = micro_algo + 1000 + number_algo_freeze + int(not optin) * 101000
    print("algo needed:", algo_needed, "number_alg", number_algo)
    return algo_needed <= number_algo


def create_resale_smart_contract(micro_price, token_id, buyer_address):
    seller_private_key = get_private_key_from_mnemonic(WORD_MNEMONIC)
    expiry_round = algod_client.status()['last-round'] + 1000
    ratn = 1
    min_trade = (micro_price - 1)
    max_fee = 2000
    limit = template.LimitOrder(buyer_address, token_id, ratn, micro_price, expiry_round, min_trade, max_fee)
    escrow_address = limit.get_address()
    program = limit.get_program()
    asset_amount = 1
    tx_params = algod_client.suggested_params()
    fee = 0
    tx_ns = limit.get_swap_assets_transactions(program, asset_amount, micro_price, seller_private_key, tx_params.first,
                                               tx_params.first + 1000, tx_params.gh, fee)
    return escrow_address, tx_ns


def fund_smart_contract(smartcontract_address):
    seller_private_key = get_private_key_from_mnemonic(WORD_MNEMONIC)
    params = algod_client.suggested_params()
    params.fee = 1000
    params.flat_fee = True
    txn = PaymentTxn(ADDRESS_ALGO_OURSELF, params, smartcontract_address, 120000)
    stxn = txn.sign(seller_private_key)
    tx_id = algod_client.send_transaction(stxn)
    return tx_id


def get_private_key_from_mnemonic(mn):
    private_key = mnemonic.to_private_key(mn)
    return private_key


def list_account_assets(account: str) -> list:
    if account is None:
        return []
    account_info = algod_client.account_info(account)
    if 'assets' not in account_info:
        return []
    asset_list = [account_info['assets'][idx]['asset-id'] for idx, my_account_info in enumerate(account_info['assets'])
                  if account_info['assets'][idx]['amount'] == 1]
    return asset_list


def list_account_assets_all(account: str) -> list:
    if account is None:
        return []
    account_info = algod_client.account_info(account)
    if 'assets' not in account_info:
        return []
    asset_list = [account_info['assets'][idx]['asset-id'] for idx, my_account_info in enumerate(account_info['assets'])]
    return asset_list


def mint_official_nft(swarm_hash: str, is_public: bool, username: str, title: str, number: int,
                      asset_symbol: str = 'MYPIC', website_url: str = 'http://mypic.io'):
    params = algod_client.suggested_params()
    params.fee = 1000
    params.flat_fee = True
    data_set = {"is_public": f'{is_public}', 'username': username, 'title': title, 'number': f'{number}'}

    tx_note_json_str = json.dumps(data_set)
    tx_note_bytes = tx_note_json_str.encode("utf-8")

    swarm_hash_bytes = unhexlify(base58.b58decode(swarm_hash)[2:].hex()) if is_public else None
    # TODO : add ...
    asset_name = f"MyPic {username} {title}"[:32]
    txn = AssetConfigTxn(sender=accounts[1]['pk'],
                         sp=params,
                         total=1,
                         decimals=0,
                         unit_name=asset_symbol,
                         asset_name=asset_name,
                         strict_empty_address_check=False,
                         default_frozen=False,
                         metadata_hash=swarm_hash_bytes,
                         note=tx_note_bytes,
                         manager=accounts[1]['pk'],
                         reserve=accounts[1]['pk'],
                         freeze="",
                         clawback=accounts[1]['pk'],
                         url=website_url)

    stxn = txn.sign(accounts[1]['sk'])
    tx_id = algod_client.send_transaction(stxn)
    wait_for_confirmation(tx_id)
    ptx = algod_client.pending_transaction_info(tx_id)
    asset_id = ptx["asset-index"]
    return asset_id


def send_transactions(tx):
    tx_id = algod_client.send_transactions(tx)
    return tx_id


def transfer_algo_to_user(receiver, micro_algo_amount):
    mypic_private_key = get_private_key_from_mnemonic(WORD_MNEMONIC)
    params = algod_client.suggested_params()
    txn = PaymentTxn(ADDRESS_ALGO_OURSELF, params, receiver, micro_algo_amount)
    stxn = txn.sign(mypic_private_key)
    tx_id = algod_client.send_transaction(stxn)
    return tx_id


def transfer_nft_to_user(asset_id, address):
    mypic_private_key = get_private_key_from_mnemonic(WORD_MNEMONIC)
    params = algod_client.suggested_params()
    params.fee = 1000
    params.flat_fee = True
    txn = AssetTransferTxn(
        sender=ADDRESS_ALGO_OURSELF,
        sp=params,
        receiver=address,
        amt=1,
        index=asset_id)
    stxn = txn.sign(mypic_private_key)
    tx_id = algod_client.send_transaction(stxn)
    return tx_id


def verify_bid_transaction(tx_id, price, username, token_id, address):
    try:
        tx_info = wait_for_confirmation(tx_id)
        tx_price = int(tx_info.get('txn').get('txn').get('amt') / CONVERT_TO_MICRO)
        tx_note = base64.b64decode(tx_info.get('txn').get('txn').get('note')).decode('ascii')
        tx_sender = tx_info.get('txn').get('txn').get('snd')
        tx_receiver = tx_info.get('txn').get('txn').get('rcv')
        return (price == tx_price
                and f"{username}_{token_id}" == tx_note
                and tx_sender == address
                and tx_receiver == ADDRESS_ALGO_OURSELF
                and bool(tx_info.get('confirmed-round')))
    except AlgodHTTPError:
        return False


def verify_buy_transaction(tx_id):
    tx_info = wait_for_confirmation(tx_id)
    return bool(tx_info.get('confirmed-round'))


def verify_get_back_nft_transaction(tx_id, token_id, username, address):
    try:
        tx_info = wait_for_confirmation(tx_id)
        tx_price = tx_info.get('txn').get('txn').get('amt')
        tx_note = base64.b64decode(tx_info.get('txn').get('txn').get('note')).decode('ascii')
        tx_sender = tx_info.get('txn').get('txn').get('snd')
        tx_receiver = tx_info.get('txn').get('txn').get('rcv')
        return ((PRICE_GET_BACK == tx_price or tx_price == 1000)
                and f"{username}_{token_id}" == tx_note
                and tx_sender == address
                and tx_receiver == ADDRESS_ALGO_OURSELF
                and bool(tx_info.get('confirmed-round')))
    except AlgodHTTPError:
        return False


def wait_for_confirmation(tx_id):
    last_round = algod_client.status().get('last-round')
    tx_info = algod_client.pending_transaction_info(tx_id)
    while not (tx_info.get('confirmed-round') and tx_info.get('confirmed-round') > 0):
        print("Waiting for confirmation")
        last_round += 1
        algod_client.status_after_block(last_round)
        tx_info = algod_client.pending_transaction_info(tx_id)
    print("Transaction {} confirmed in round {}.".format(tx_id, tx_info.get('confirmed-round')))
    return tx_info



## ICO

def get_mypic_asset_swap_txns(micro_algo_amount, micro_asset_amount, buyer_public_key):
    # Retrieve the program bytes
    program_bytes = "AiAIAQQCAOmB2lzoB9DbqAYgJgEg7enwSXp6w6FzbfJaV7JXMCbtVRVpf382aeBiISomJMkyBCISMRAjEhBAACEyBCISMRAiEhBAAEYyBCQSMwAQIhIQMwEQIxIQQABMJUMxEiUSMREhBBIQMQAxFBIQMQEhBQ4QMRMyAxIQMRUyAxIQMSAyAxIQMQQhBgwQQgBWMQcoEjEBIQUOEDEJMgMSEDEgMgMSEEIAPTMBEjMACAohBxIzAREhBBIQMwEAMwAHEhAzARQzAAASEDMBASEFDhAzARMyAxIQMwEVMgMSEDMBIDIDEhA="
    program = base64.b64decode(program_bytes)
    # Get suggested parameters from the network
    tx_params = algod_client.suggested_params()
    first_valid = tx_params.first
    last_valid = tx_params.first + 1000
    gh = tx_params.gh
    fee = 0
    contract = program
    contract_addr = logic.address(contract)
    print("contract_addr =", contract_addr)
    asset_id = 194412777
    max_fee = 1000

    if micro_asset_amount <= 0:
        raise error.TemplateInputError(
            "At least 0 MYPIC must be requested")

    if micro_asset_amount / micro_algo_amount != 32:
        raise error.TemplateInputError(
            "The exchange ratio of assets to microalgos must be = 32")

    txn_1 = transaction.PaymentTxn(
        buyer_public_key, fee, first_valid, last_valid, gh,
        contract_addr,
        int(micro_algo_amount))

    txn_2 = transaction.AssetTransferTxn(
        contract_addr, fee,
        first_valid, last_valid, gh, buyer_public_key, micro_asset_amount, asset_id)

    if txn_1.fee > max_fee or txn_2.fee > max_fee:
        raise error.TemplateInputError(
            "the transaction fee should not be greater than "
            + str(max_fee))

    transaction.assign_group_id([txn_1, txn_2])

    lsig = transaction.LogicSig(contract)
    stx_2 = transaction.LogicSigTransaction(txn_2, lsig)

    tx_1_enc = encoding.msgpack_encode(txn_1)
    stx_2_enc = encoding.msgpack_encode(stx_2)

    txns = [tx_1_enc, stx_2_enc]
    return txns


def mypic_asset_swap_txns_decode(algo_payment_tx1_blob, micro_asset_amount, buyer_public_key):
    # Retrieve the program bytes
    program_bytes = "AiAIAQQCAOmB2lzoB9DbqAYgJgEg7enwSXp6w6FzbfJaV7JXMCbtVRVpf382aeBiISomJMkyBCISMRAjEhBAACEyBCISMRAiEhBAAEYyBCQSMwAQIhIQMwEQIxIQQABMJUMxEiUSMREhBBIQMQAxFBIQMQEhBQ4QMRMyAxIQMRUyAxIQMSAyAxIQMQQhBgwQQgBWMQcoEjEBIQUOEDEJMgMSEDEgMgMSEEIAPTMBEjMACAohBxIzAREhBBIQMwEAMwAHEhAzARQzAAASEDMBASEFDhAzARMyAxIQMwEVMgMSEDMBIDIDEhA="
    program = base64.b64decode(program_bytes)
    # Get suggested parameters from the network
    tx_params = algod_client.suggested_params()
    first_valid = tx_params.first
    last_valid = tx_params.first + 1000
    gh = tx_params.gh
    fee = 0

    contract = program
    contract_addr = logic.address(contract)
    print("contract_addr =", contract_addr)
    asset_id = 194412777

    txn_2 = transaction.AssetTransferTxn(
        contract_addr, fee,
        first_valid, last_valid, gh, buyer_public_key, micro_asset_amount, asset_id)

    stx_1 = encoding.msgpack_decode(algo_payment_tx1_blob)
    transaction.assign_group_id([stx_1, txn_2])

    lsig = transaction.LogicSig(contract)
    stx_2 = transaction.LogicSigTransaction(txn_2, lsig)
    txns = [stx_1, stx_2]
    txid = send_transactions(txns)
    return txid


# stx_1 = swap_txns[0].sign(buyer_private_key)
# stx_2 = swap_txns[1]
# gstxns = [stx_1, stx_2]
# txid = send_transactions(algod_client_, gstxns)