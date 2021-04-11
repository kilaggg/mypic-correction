from application import dict_buy
from application.constants import TRANSACTION_IN_PROGRESS, TRANSACTION_STARTED
from application.constants import (
    CONVERT_TO_MICRO,
    MISSING_ARGUMENT,
    NO_API,
    TRANSACTION_DONE,
    TRANSACTION_ERROR,
    WRONG_ARGUMENT
)
from application.market import execute_buy
from application.smart_contract import (
    check_algo_for_tx,
    create_resale_smart_contract,
    fund_smart_contract,
    list_account_assets_all,
    send_transactions,
    transfer_algo_to_user,
    verify_buy_transaction,
    wait_for_confirmation
)
from application.user import get_address_from_username, get_address_of_resale, get_royalties, get_username_of_token
import json


def manage_buy(form, username):
    print(form)
    if 'token_id' not in form:
        e_full = "Token ID is required."
        return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
    if 'price' not in form:
        e_full = "Price is required."
        return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
    if 'address' not in form:
        e_full = "Address ID is required."
        return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
    try:
        int(form['token_id'])
    except ValueError:
        e_full = "Enter an integer for Token ID."
        return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
    try:
        int(form['price'])
    except ValueError:
        e_full = "Enter an integer for Price."
        return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})

    token_id = int(form['token_id'])
    price = int(form['price'])
    address = form['address']
    if form['type'] == 'resale':
        price = int(form['price'])
        micro_price = price * CONVERT_TO_MICRO
        smartcontract_address, swap_tx = create_resale_smart_contract(micro_price, token_id, address)
        tx_id = fund_smart_contract(smartcontract_address)
        tx_info = wait_for_confirmation(tx_id)
        if bool(tx_info.get('confirmed-round')):
            note = f"{username}_{token_id}_resale"
            dict_buy[note] = swap_tx
            message_full = "Successfully created the smart contract, you can send ALGO"
            return json.dumps({'status': 200, 'to': smartcontract_address, 'amount': micro_price, 'note': note,
                               'message': TRANSACTION_IN_PROGRESS, 'message_full': message_full})
        e_full = "Failed to create the smart contract, please retry"
        return json.dumps({"status": 404, "e": TRANSACTION_ERROR, "e_full": e_full})

    if form['type'] == 'validate_resale':
        micro_price = int(form['price'])
        if 'txID' not in form:
            e_full = "Transaction ID is required."
            return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
        address = form['address']
        tx_id = form['txID']
        price = int(micro_price/CONVERT_TO_MICRO)
        note = f"{username}_{token_id}_resale"
        # TODO : verify buy transaction with more check
        if verify_buy_transaction(tx_id):
            tx_swap_id = send_transactions(dict_buy[note])
            owner_address = get_address_of_resale(token_id)
            creator_username = get_username_of_token(token_id)
            royalties = get_royalties(token_id)
            price_owner = int(price * (100 - royalties) * 10000)
            price_creator = int(price * royalties * 10000)
            print("price owner", price_owner)
            print("price creator", price_creator)
            tx_owner_id = transfer_algo_to_user(owner_address, price_owner)
            tx_swap_info = wait_for_confirmation(tx_swap_id)
            if price_creator > 0:
                creator_address = get_address_from_username(creator_username)
                tx_creator_id = transfer_algo_to_user(creator_address, price_creator)
                tx_creator_info = wait_for_confirmation(tx_creator_id)
                tx_creator_info_bool = bool(tx_creator_info.get('confirmed-round'))
            else:
                tx_creator_info_bool = True
            tx_owner_info = wait_for_confirmation(tx_owner_id)
            if bool(tx_swap_info.get('confirmed-round')) & bool(tx_owner_info.get('confirmed-round')) & tx_creator_info_bool:
                execute_buy(token_id)
                dict_buy.pop(note, None)
                message_full = "Buy was successfully done"
                return json.dumps({'status': 200, 'message': TRANSACTION_DONE, 'message_full': message_full})
            e_full = "Something went wrong."
            return json.dumps({'status': 404, "e": TRANSACTION_ERROR, "e_full": e_full})
        e_full = "Transaction does not exist"
        return json.dumps({"status": 404, "e": TRANSACTION_ERROR, "e_full": e_full})
    e_full = "Endpoint not found."
    return json.dumps({"status": 404, "e": NO_API, "e_full": e_full})


def check_resale(form):
    if 'token_id' not in form:
        e_full = "Token ID is required."
        return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
    if 'address' not in form:
        e_full = "Address is required."
        return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
    if 'price' not in form:
        e_full = "Price is required."
        return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
    try:
        int(form['token_id'])
    except ValueError:
        e_full = "Enter an integer for Token ID."
        return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
    try:
        int(form['price'])
    except ValueError:
        e_full = "Enter an integer for Price."
        return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
    token_id = int(form['token_id'])
    price = int(form['price'])
    micro_price = price * CONVERT_TO_MICRO
    address = form['address']
    bool_optin = token_id in list_account_assets_all(address)
    bool_tx = check_algo_for_tx(address, micro_price, bool_optin)
    if not bool_tx:
        e_full = "Not enough Algo on your address, please fill your wallet."
        return json.dumps({"status": 404, "e": TRANSACTION_ERROR, "e_full": e_full})
    message_full = "Wait few seconds to get your NFT"
    return json.dumps({"status": 200, "check_token": bool_optin, "message": TRANSACTION_STARTED,
                       "message_full": message_full})
