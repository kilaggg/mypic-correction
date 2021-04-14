from application import ADDRESS_ALGO_OURSELF, dict_bid#, socketio
from application.constants import CONVERT_TO_MICRO, MISSING_ARGUMENT, SYSTEM_ERROR, TRANSACTION_ERROR, WRONG_ARGUMENT
from application.market import execute_bid
from application.smart_contract import (
    check_algo_for_tx,
    list_account_assets_all,
    transfer_algo_to_user,
    verify_bid_transaction,
    verify_buy_transaction
)
from application.user import get_current_price_from_token_id, get_date_from_token_id, get_previous_bidder
from datetime import datetime, timedelta
from flask import redirect, url_for
import json


def manage_auction(form, username):
    if 'token_id' not in form:
        e_full = "Token ID is required."
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
    if form['type'] == 'new':
        price = int(form['price'])
        if 'address' not in form:
            e_full = "Address is required."
            return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
        if datetime.utcnow() > get_date_from_token_id(token_id):
            e_full = "Auction has expired."
            return json.dumps({"status": 404, 'e': SYSTEM_ERROR, 'e_full': e_full})
        if price < int(get_current_price_from_token_id(token_id) * 1.1) + 1:
            e_full = f"Minimum bid price is : {int(get_current_price_from_token_id(token_id) * 1.1) + 1}"
            return json.dumps({"status": 404, 'e': WRONG_ARGUMENT, 'e_full': e_full})
        if token_id in dict_bid and dict_bid[token_id][0] + timedelta(minutes=2) > datetime.utcnow():
            e_full = "Someone process a bid, retry in one minute"
            return json.dumps({"status": 404, 'e': SYSTEM_ERROR, 'e_full': e_full})
        address = form['address']
        micro_price = price * CONVERT_TO_MICRO
        bool_optin = token_id in list_account_assets_all(address)
        bool_tx = check_algo_for_tx(address, micro_price, bool_optin)
        if not bool_tx:
            e_full = "Not enough ALGO on your address, please fill your wallet."
            return json.dumps({"status": 404, "e": TRANSACTION_ERROR, "e_full": e_full})
        dict_bid[token_id] = [datetime.utcnow(), username, price]
        message = "Successfully check the auction"
        return json.dumps({'status': 200, 'to': ADDRESS_ALGO_OURSELF, 'amount': micro_price,
                           'note': f"{username}_{token_id}", 'message': message, 'check_token': bool_optin})

    if form['type'] == 'error_new':
        dict_bid.pop(token_id, None)
        message = "Delete Bider from queue"
        return json.dumps({'status': 200, 'message': message})

    if form['type'] == 'validate_new':
        micro_price = int(form['price'])
        if 'address' not in form:
            e_full = "Address is required."
            return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
        if 'txID' not in form:
            e_full = "Transaction ID is required."
            return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
        address = form['address']
        tx_id = form['txID']
        price = int(micro_price/CONVERT_TO_MICRO)
        if verify_bid_transaction(tx_id, price, username, token_id, address):
            if username == dict_bid[token_id][1] and price == dict_bid[token_id][2]:
                old_price = int(get_current_price_from_token_id(token_id))
                old_micro_price = old_price * CONVERT_TO_MICRO
                old_address = get_previous_bidder(token_id)
                execute_bid(token_id, price, address, username)
                dict_bid.pop(token_id, None)
                # TODO : re-implement socket
                # socketio.emit("new", data=[str(int(price * 1.1) + 1), token_id])
                if old_address is not None:
                    tx_id = transfer_algo_to_user(old_address, old_micro_price)
                    if verify_buy_transaction(tx_id):
                        message = "Bid was successfully done."
                        return json.dumps({'status': 200, 'message': message})
                    # TODO : refund was not done, send message to us
                message = "Bid was successfully done."
                return json.dumps({'status': 200, 'message': message})
            else:
                tx_id = transfer_algo_to_user(address, micro_price)
                if verify_buy_transaction(tx_id):
                    message = "Refund was successfully done."
                    return json.dumps({'status': 200, 'message': message})
        else:
            e_full = "Transaction does not exist"
            return json.dumps({"status": 404, "e": SYSTEM_ERROR, "e_full": e_full})
    return redirect(url_for('main.feed'))
