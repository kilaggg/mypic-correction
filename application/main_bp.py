from application import ADDRESS_ALGO_OURSELF
from application.auction import manage_auction
from application.buy import manage_buy, check_resale
from application.constants import *
from application.market import (
    build_image_favorites,
    cancel_resale,
    create_new_image,
    create_resale,
    create_resale_from_back,
    download_blob_data,
    get_image_from_address,
    get_new_images,
    get_nft_back,
    get_resale,
    send_nft_back
)
from application.smart_contract import check_algo_for_tx, list_account_assets, list_account_assets_all
from application.user import (
    is_follow,
    follow,
    unfollow,
    get_address_from_email,
    get_address_from_username,
    get_current_price_from_token_id,
    get_date_from_token_id,
    get_followers_from_username,
    get_fullname_from_email,
    get_fullname_from_username,
    get_historical_bid,
    get_infos_from_email,
    get_infos_from_username,
    get_info_token,
    get_is_public_from_username,
    get_nsfw_from_email,
    get_password_from_email,
    get_price_resale,
    get_profile_picture_extension_from_email,
    get_profile_picture_extension_from_username,
    get_stars_from_follower,
    get_username_of_resale,
    hash_password,
    is_resale,
    token_in_sell_by_username,
    update_address,
    update_fullname,
    update_nsfw,
    update_password,
    update_profile_picture
)
from datetime import datetime, timedelta
from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from flask_jwt_extended import get_jwt_identity, jwt_required
from joblib import delayed, Parallel
from werkzeug.utils import secure_filename
from werkzeug.security import safe_str_cmp
import json
import multiprocessing
import re

bp = Blueprint('main', __name__, url_prefix='')
REGEX_TITLE_IMAGE = "^[a-zA-Z0-9 ]*$"
REGEX_DESCRIPTION_IMAGE = "^[a-zA-Z0-9 .,]*$"
CATEGORIES = [{"value": "default", "name": "Default"}, {"value": "animal", "name": "Animal"}, {"value": "art", "name": "Art"}, {"value": "body_art", "name": "Body Art"}, {"value": "car", "name": "Car"}, {"value": "city", "name": "City"}, {"value": "flower", "name": "Flower"}, {"value": "landscape", "name": "Landscape"}, {"value": "meme", "name": "Meme"}, {"value": "movie", "name": "Movie"}, {"value": "nature", "name": "Nature"}, {"value": "other", "name": "Other"}, {"value": "pixel_art", "name": "Pixel Art"}, {"value": "sport", "name": "Sport"}]


@bp.route('/account', methods=('GET', 'POST'))
@jwt_required
def account() -> str:
    email = get_jwt_identity()['email']
    username = get_jwt_identity()['username']
    user_infos = get_infos_from_username(username)
    fullname = user_infos.loc[0, 'fullname']
    address = user_infos.loc[0, 'address']
    pp_extension = user_infos.loc[0, 'profile_picture_extension']
    followers = user_infos.loc[0, 'total_followers']
    nsfw = user_infos.loc[0, 'nsfw']
    pp_path = pp_extension if pp_extension == 'default-profile.png' else f"{username.lower()}.{pp_extension}"
    profile_picture = download_blob_data(PROFILE_PICTURES_CONTAINER, pp_path)
    pp = f"data:{pp_extension};base64,{profile_picture}"
    user = {'username': username,
            'fullname': fullname,
            'nsfw': nsfw,
            'address': address,
            'profile_picture': pp,
            'followers': str(followers)}
    if request.method == 'POST':
        if 'update_parameters' in request.form:
            if 'fullname' in request.form and request.form['fullname'] != fullname:
                if len(request.form['fullname']) < 1 or len(request.form['fullname']) > 20:
                    e_full = "The length of Fullname must be between 1 and 20 chars."
                    return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
                if not bool(re.match(REGEX_FULLNAME, request.form['fullname'])):
                    e_full = "Fullname should contains only letters, numbers and spaces."
                    return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
                update_fullname(email, request.form['fullname'])
                message_full = "Fullname was updated."
                return json.dumps({"status": 200, "message": UPDATE_DONE, "message_full": message_full})

            if 'nsfw' in request.form and (request.form['nsfw'] == 'on') != nsfw:
                new_nsfw = int(request.form['nsfw'] == 'on')
                update_nsfw(email, new_nsfw)
                message_full = "NSFW account was updated."
                return json.dumps({"status": 200, "message": UPDATE_DONE, "message_full": message_full})

            if 'old_password' in request.form and 'new_password' in request.form and request.form['new_password'] != '':
                old_password = hash_password(request.form['old_password'])
                new_password = hash_password(request.form['new_password'])
                if len(request.form['new_password']) < 6:
                    e_full = "Password should contains at least 6 chars."
                    return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
                if not safe_str_cmp(old_password, get_password_from_email(email)):
                    e_full = "Wrong Password."
                    return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
                update_password(email, new_password)
                message_full = "Password was updated."
                return json.dumps({"status": 200, "message": UPDATE_DONE, "message_full": message_full})
            e_full = "Endpoint not found."
            return json.dumps({"status": 404, "e": NO_API, "e_full": e_full})

        if 'update_profile_picture' in request.form:
            if 'file' not in request.files:
                e_full = "Image file is required."
                json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
            file = request.files['file']
            extension = DICTIONARY_FORMAT[secure_filename(file.filename).split('.')[-1].lower()]
            session['extension'] = extension
            update_profile_picture(username, file, extension)
            message_full = "Profile Picture was updated."
            return json.dumps({"status": 200, "message": UPDATE_DONE, "message_full": message_full})
    return render_template('app/account.html', user=user, pp=pp)


@bp.route('/create', methods=('GET', 'POST'))
@jwt_required
def create() -> str:
    email = get_jwt_identity()['email']
    username = get_jwt_identity()['username']
    if request.method == 'POST' and 'create' in request.form:
        if 'file' not in request.files:
            e_full = "File is required."
            return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
        if 'title' not in request.form:
            e_full = "Title is required."
            return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
        if 'price' not in request.form:
            e_full = "Price is required."
            return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
        if 'duration' not in request.form:
            e_full = "Duration is required."
            return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
        if 'private' not in request.form:
            e_full = "Private is required."
            return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
        if 'category' not in request.form:
            e_full = "Category is required."
            return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
        if 'nsfw' not in request.form:
            e_full = "NSFW is required."
            return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
        if 'royalties' not in request.form:
            e_full = "Royalties is required."
            return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
        if 'description' not in request.form:
            e_full = "Description is required."
            return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
        try:
            int(request.form['price'])
        except ValueError:
            e_full = "Enter an integer for Price."
            return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
        if int(request.form['price']) < 10:
            e_full = "Price should be higher than 10 ALGO."
            return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
        try:
            int(request.form['duration'])
        except ValueError:
            e_full = "Enter an integer for Duration."
            return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
        if int(request.form['duration']) > 200 or int(request.form['duration']) < 0:
            e_full = "Duration should be lower than 200 hours"
            return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
        try:
            int(request.form['royalties'])
        except ValueError:
            e_full = "Enter an integer for Royalties."
            return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
        if int(request.form['royalties']) > 5 or int(request.form['royalties']) < 0:
            e_full = "Royalties should be lower than 5%"
            return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
        if len(request.form['description']) > 255:
            e_full = "Description should be with a maximum of 255 chars."
            return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
        if len(request.form['title']) > 30 or len(request.form['title']) < 1:
            e_full = "The length of Title must be between 1 and 30 chars."
            return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
        if not bool(re.match(REGEX_TITLE_IMAGE, request.form['title'])):
            e_full = "Title should contains only letters, numbers and spaces"
            return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
        if not bool(re.match(REGEX_DESCRIPTION_IMAGE, request.form['description'])):
            e_full = "Description should contains only letters, numbers, spaces, commas and dots"
            return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
        if secure_filename(request.files['file'].filename).split('.')[-1].lower() not in DICTIONARY_FORMAT:
            e_full = f"We only accept format in : {','.join(list(DICTIONARY_FORMAT.keys()))}"
            return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})

        address = get_address_from_email(email)
        if address is None:
            e_full = "To create NFT, We need an Address. Go to 'Account' and link an ALGO Address"
            return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
        file = request.files['file']
        title = request.form['title']
        price = int(request.form['price'])
        royalties = int(request.form['royalties'])
        description = request.form['description']
        end_date = datetime.utcnow() + timedelta(hours=int(request.form['duration']))
        public = 0 if request.form['private'] == 'on' else 1
        nsfw = 0 if request.form['nsfw'] == 'off' else 1
        category = request.form['category']
        token_id = create_new_image(username, file, title, price, end_date, public, nsfw, royalties, description,
                                    category)
        message_full = "NFT Successfully created"
        return json.dumps({'status': 200, 'token_id': token_id, 'message': CREATION_DONE, "message_full": message_full})
    pp_extension = session['extension']
    pp_path = pp_extension if pp_extension == 'default-profile.png' else f"{username.lower()}.{pp_extension}"
    profile_picture = download_blob_data(PROFILE_PICTURES_CONTAINER, pp_path)
    pp = f"data:{pp_extension};base64,{profile_picture}"
    return render_template('app/create.html', categories=CATEGORIES, pp=pp)


@bp.route('/favorites', methods=('GET', 'POST'), endpoint='v1')
@bp.route('/feed', methods=('GET', 'POST'), endpoint='v2')
@jwt_required
def feed() -> str:
    page = 'feed' if request.endpoint == 'main.v2' else 'favorites'
    email = get_jwt_identity()['email']
    username = get_jwt_identity()['username']
    print(request.form)
    if request.method == 'POST':
        if "more" in request.form:
            nsfw = get_nsfw_from_email(email)
            follower = None if request.endpoint == 'main.v2' else username
            if request.form["more"] == "new":
                data_new_images = get_new_images(session.get(f'{page}_number_new'), nsfw, follower=follower)
                session[f'{page}_number_new'] = session.get(f'{page}_number_new') + 1
                message = "Successfully load images"
                return json.dumps({'status': 200, 'pictures': data_new_images, 'message': message})

            if request.form["more"] == "resale":
                resale_images = get_resale(session.get(f'{page}_number_resale'), nsfw, follower=follower)
                session[f'{page}_number_resale'] = session.get(f'{page}_number_resale') + 1
                message = "Successfully load images"
                return json.dumps({'status': 200, 'pictures': resale_images, 'message': message})

        if 'type' in request.form:
            if (request.form['type'] == 'new'
                    or request.form['type'] == 'validate_new'
                    or request.form['type'] == 'error_new'):
                return manage_auction(request.form, get_jwt_identity()['username'])

            if request.form['type'] == 'resale' or request.form['type'] == 'validate_resale':
                return manage_buy(request.form, get_jwt_identity()['username'])

            if request.form['type'] == 'check_resale':
                return check_resale(request.form)
        e_full = "Endpoint not found."
        return json.dumps({"status": 404, "e": NO_API, "e_full": e_full})
    session[f'{page}_number_new'] = 0
    session[f'{page}_number_resale'] = 0

    pp_extension = session['extension']
    pp_path = pp_extension if pp_extension == 'default-profile.png' else f"{username.lower()}.{pp_extension}"
    profile_picture = download_blob_data(PROFILE_PICTURES_CONTAINER, pp_path)
    pp = f"data:{pp_extension};base64,{profile_picture}"
    return render_template(f'app/{page}.html', categories=CATEGORIES, pp=pp)


@bp.route('/gallery', methods=('GET', 'POST'))
@jwt_required
def gallery() -> str:
    email = get_jwt_identity()['email']
    username = get_jwt_identity()['username']
    if request.method == 'POST':
        address = get_address_from_email(email)
        nsfw = get_nsfw_from_email(email)
        if "more" in request.form:
            if request.form["more"] == "my-pics":
                data_my_gallery = get_image_from_address(address, session.get('number_my_gallery'), True, nsfw)
                session['number_my_gallery'] = session.get('number_my_gallery') + 1
                message = "Successfully load images"
                return json.dumps({'status': 200, "pictures": data_my_gallery, "message": message})

            if request.form["more"] == "my-auctions":
                data_new_images = get_new_images(session.get('number_my_new_image'), nsfw, username=username, my=True)
                session['number_my_new_image'] = session.get('number_my_new_image') + 1
                message = "Successfully load images"
                return json.dumps({'status': 200, "pictures": data_new_images, "message": message})

            if request.form["more"] == "my-resales":
                resale_images = get_resale(session.get('number_my_resale'), nsfw, username=username, my=True)
                session['number_my_resale'] = session.get('number_my_resale') + 1
                message = "Successfully load images"
                return json.dumps({'status': 200, "pictures": resale_images, "message": message})

        if 'type' in request.form:
            if request.form['type'] == 'cancel':
                if 'token_id' not in request.form:
                    e_full = "Token ID is required."
                    return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
                try:
                    int(request.form['token_id'])
                except ValueError:
                    e_full = "Enter an integer for Token ID."
                    return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})

                token_id = int(request.form['token_id'])
                if get_username_of_resale(token_id) != username:
                    e_full = "You are not the seller of this token, you cannot cancel it."
                    return json.dumps({"status": 404, "e": SYSTEM_ERROR, "e_full": e_full})
                cancel = cancel_resale(token_id)
                if not cancel:
                    e_full = "Something went wrong, please retry. If the issue persists, please contact us."
                    return json.dumps({"status": 404, "e": SYSTEM_ERROR, "e_full": e_full})
                message_full = "Sell was cancelled."
                return json.dumps({"status": 200, "message": TRANSACTION_DONE, "message_full": message_full})

            if request.form['type'] == 'check_sell':
                message_full = "Sell in progress."
                return json.dumps({"status": 200, "address": ADDRESS_ALGO_OURSELF, "message": TRANSACTION_IN_PROGRESS,
                                   "message_full": message_full})

            if request.form['type'] == 'sell':
                if 'txID' not in request.form:
                    e_full = "Transaction ID is required."
                    return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
                if 'price' not in request.form:
                    e_full = "Price is required."
                    return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
                if 'token_id' not in request.form:
                    e_full = "Token ID is required."
                    return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
                try:
                    int(request.form['price'])
                except ValueError:
                    e_full = "Enter an integer for Price."
                    return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
                try:
                    int(request.form['token_id'])
                except ValueError:
                    e_full = "Enter an integer for Token ID."
                    return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
                price = int(request.form['price'])
                token_id = int(request.form['token_id'])
                tx_id = request.form['txID']
                resale = create_resale(username, token_id, price, tx_id)
                if not resale:
                    e_full = "Error during the transaction. If the problem persists, please contact us."
                    return json.dumps({"status": 404, "e": TRANSACTION_ERROR, "e_full": e_full})
                message_full = "Sell successfully created."
                return json.dumps({"status": 200, "message": TRANSACTION_DONE, "message_full": message_full})
        e_full = "Endpoint not found."
        return json.dumps({"status": 404, "e": NO_API, "e_full": e_full})
    session['number_my_gallery'] = 0
    session['number_my_new_image'] = 0
    session['number_my_resale'] = 0
    pp_extension = session['extension']
    pp_path = pp_extension if pp_extension == 'default-profile.png' else f"{username.lower()}.{pp_extension}"
    profile_picture = download_blob_data(PROFILE_PICTURES_CONTAINER, pp_path)
    pp = f"data:{pp_extension};base64,{profile_picture}"
    return render_template("app/gallery.html", pp=pp)


@bp.route('/gallery/<username>', methods=('GET', 'POST'))
@jwt_required
def gallery_navigation(username: str) -> str:
    if username == get_jwt_identity()['username']:
        return redirect(url_for('main.gallery'))
    if request.method == 'POST':
        is_public = get_is_public_from_username(username)
        if "more" in request.form:
            email = get_jwt_identity()['email']
            nsfw = get_nsfw_from_email(email)
            address = get_address_from_username(username)
            if request.form["more"] == "my-pics":
                data_my_gallery = get_image_from_address(address, session.get('number_other_gallery'), is_public, nsfw)
                session['number_other_gallery'] = session.get('number_other_gallery') + 1
                message = "Successfully load images"
                return json.dumps({'status': 200, "pictures": data_my_gallery, "message": message})

            if request.form["more"] == "my-auctions":
                data_new_images = get_new_images(session.get('number_other_new_image'), nsfw, username=username)
                session['number_other_new_image'] = session.get('number_other_new_image') + 1
                message = "Successfully load images"
                return json.dumps({'status': 200, "pictures": data_new_images, "message": message})

            if request.form["more"] == "my-resales":
                resale_images = get_resale(session.get('number_other_resale'), nsfw, username=username)
                session['number_other_resale'] = session.get('number_other_resale') + 1
                message = "Successfully load images"
                return json.dumps({'status': 200, "pictures": resale_images, "message": message})

        if 'type' in request.form:
            if (request.form['type'] == 'new'
                    or request.form['type'] == 'validate_new'
                    or request.form['type'] == 'error_new'):
                return manage_auction(request.form, get_jwt_identity()['username'])

            if request.form['type'] == 'resale' or request.form['type'] == 'validate_resale':
                return manage_buy(request.form, get_jwt_identity()['username'])

            if request.form['type'] == 'check_resale':
                return check_resale(request.form)

            if request.form['type'] == 'follow':
                follow(get_jwt_identity()['username'], username)
                message = "Follow was done."
                return json.dumps({'status': 200, "message": message})

            if request.form['type'] == 'unfollow':
                unfollow(get_jwt_identity()['username'], username)
                message = "Unfollow was done."
                return json.dumps({'status': 200, "message": message})

    session['number_other_gallery'] = 0
    session['number_other_new_image'] = 0
    session['number_other_resale'] = 0
    user_infos = get_infos_from_username(username)
    if len(user_infos) == 0:
        # TODO : 404 user
        return redirect(url_for('main.gallery'))
    fullname = user_infos.loc[0, 'fullname']
    pp_extension = user_infos.loc[0, 'profile_picture_extension']
    followers = user_infos.loc[0, 'total_followers']
    pp_path = pp_extension if pp_extension == 'default-profile.png' else f"{username.lower()}.{pp_extension}"
    profile_picture = download_blob_data(PROFILE_PICTURES_CONTAINER, pp_path)
    is_follow_int = int(is_follow(get_jwt_identity()['username'], username))
    user = {'username': username,
            'profile_picture': f"data:{pp_extension};base64,{profile_picture}",
            'followers': str(followers),
            'fullname': fullname,
            'is_follow': is_follow_int}

    username = get_jwt_identity()['username']
    pp_extension = session['extension']
    pp_path = pp_extension if pp_extension == 'default-profile.png' else f"{username.lower()}.{pp_extension}"
    profile_picture = download_blob_data(PROFILE_PICTURES_CONTAINER, pp_path)
    pp = f"data:{pp_extension};base64,{profile_picture}"
    return render_template("app/gallery_navigation.html", user=user, authorized=True, pp=pp)


@bp.route('/visit/<username>', methods=('GET', 'POST'))
def gallery_visit(username: str) -> str:
    if request.method == 'POST':
        is_public = get_is_public_from_username(username)
        if "more" in request.form:
            address = get_address_from_username(username)
            if request.form["more"] == "my-pics":
                data_my_gallery = get_image_from_address(address, session.get('number_visit_gallery'), is_public, False)
                session['number_visit_gallery'] = session.get('number_visit_gallery') + 1
                message_full = "Successfully load images"
                return json.dumps({'status': 200, "pictures": data_my_gallery, "message": LOAD_DONE,
                                   "message_full": message_full})

            if request.form["more"] == "my-auctions":
                data_new_images = get_new_images(session.get('number_visit_new_image'), False, username=username)
                session['number_visit_new_image'] = session.get('number_visit_new_image') + 1
                message_full = "Successfully load images"
                return json.dumps({'status': 200, "pictures": data_new_images, "message": LOAD_DONE,
                                   "message_full": message_full})

            if request.form["more"] == "my-resales":
                resale_images = get_resale(session.get('number_visit_resale'), False, username=username)
                session['number_visit_resale'] = session.get('number_visit_resale') + 1
                message_full = "Successfully load images"
                return json.dumps({'status': 200, "pictures": resale_images, "message": LOAD_DONE,
                                   "message_full": message_full})
        e_full = "Endpoint not found."
        return json.dumps({"status": 404, "e": NO_API, "e_full": e_full})
    session['number_visit_gallery'] = 0
    session['number_visit_new_image'] = 0
    session['number_visit_resale'] = 0
    pp_extension = get_profile_picture_extension_from_username(username)
    pp_path = pp_extension if pp_extension == 'default-profile.png' else f"{username.lower()}.{pp_extension}"
    profile_picture = download_blob_data(PROFILE_PICTURES_CONTAINER, pp_path)
    followers = get_followers_from_username(username)
    fullname = get_fullname_from_username(username)
    is_follow_int = 0
    user = {'username': username,
            'profile_picture': f"data:{pp_extension};base64,{profile_picture}",
            'followers': str(followers),
            'fullname': fullname,
            'is_follow': is_follow_int}
    return render_template("app/unauth/gallery_navigation.html", user=user, authorized=False)


@bp.route('/list_favorites', methods=('GET', 'POST'))
@jwt_required
def list_favorites():
    username = get_jwt_identity()['username']
    stars = get_stars_from_follower(username)
    num_cores = multiprocessing.cpu_count()
    users = Parallel(n_jobs=num_cores)(delayed(build_image_favorites)(star) for star in stars)
    pp_extension = session['extension']
    pp_path = pp_extension if pp_extension == 'default-profile.png' else f"{username.lower()}.{pp_extension}"
    profile_picture = download_blob_data(PROFILE_PICTURES_CONTAINER, pp_path)
    pp = f"data:{pp_extension};base64,{profile_picture}"
    return render_template("app/list_favorites.html", users=users, pp=pp)


@bp.route('/nft/<token_id>', methods=('GET', 'POST'))
@jwt_required
def nft(token_id: int) -> str:
    print(request.form)
    if request.method == 'POST':
        if 'type' in request.form:
            if (request.form['type'] == 'new'
                    or request.form['type'] == 'validate_new'
                    or request.form['type'] == 'error_new'):
                return manage_auction(request.form, get_jwt_identity()['username'])

            if request.form['type'] == 'resale' or request.form['type'] == 'validate_resale':
                return manage_buy(request.form, get_jwt_identity()['username'])

            if request.form['type'] == 'check_resale':
                return check_resale(request.form)

            if request.form['type'] == 'cancel':
                if 'token_id' not in request.form:
                    e_full = "Token ID is required."
                    return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
                try:
                    int(request.form['token_id'])
                except ValueError:
                    e_full = "Enter an integer for Token ID."
                    return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})

                token_id = int(request.form['token_id'])
                if get_username_of_resale(token_id) != get_jwt_identity()['username']:
                    e_full = "You are not the seller of this token, you cannot cancel it."
                    return json.dumps({"status": 404, "e": SYSTEM_ERROR, "e_full": e_full})
                cancel = cancel_resale(token_id)
                if not cancel:
                    e_full = "Something went wrong, please retry. If the issue persists, please contact us."
                    return json.dumps({"status": 404, "e": SYSTEM_ERROR, "e_full": e_full})
                message_full = "Sell was cancelled."
                return json.dumps({"status": 200, "message": TRANSACTION_DONE, "message_full": message_full})

        e_full = "Endpoint not found."
        return json.dumps({"status": 404, "e": NO_API, "e_full": e_full})
    bid = get_historical_bid(token_id)
    token = get_info_token(token_id)
    email = get_jwt_identity()['email']
    user_infos = get_infos_from_email(email)
    address = user_infos.loc[0, 'address']

    # create user variable
    username = token.loc[0, 'username']
    nft_user_infos = get_infos_from_username(username)
    pp_extension = nft_user_infos.loc[0, 'profile_picture_extension']
    pp_path = pp_extension if pp_extension == 'default-profile.png' else f"{username.lower()}.{pp_extension}"
    profile_picture = download_blob_data(PROFILE_PICTURES_CONTAINER, pp_path)
    pp = f"data:{pp_extension};base64,{profile_picture}"
    user = {'username': username,
            'fullname': nft_user_infos.loc[0, 'fullname'],
            'profile_picture': pp}

    # create nft variable
    nsfw = user_infos.loc[0, 'nsfw']
    my = (token_id in list_account_assets(address)
          or username == get_jwt_identity()['username']
          or token_in_sell_by_username(token_id, get_jwt_identity()['username']))
    container = IMAGES_CONTAINER if (token.loc[0, 'is_public'] or my) and (not token.loc[0, 'is_nsfw'] or nsfw) else BLURRY_IMAGES_CONTAINER
    extension = token.loc[0, 'extension']
    image_path = f"{token.loc[0, 'username'].lower()}/{token.loc[0, 'swarm_hash']}.{extension}"
    end_date = get_date_from_token_id(token_id)
    type = "bid" if end_date > datetime.utcnow() else "buy" if is_resale(token_id) else "none"
    price = None if type == "none" else int(get_current_price_from_token_id(token_id) * 1.1) + 1 if type == "bid" else get_price_resale(token_id)
    nft = {'title': token.loc[0, 'title'],
           'number': token.loc[0, 'number'],
           'description': token.loc[0, 'description'],
           'category': token.loc[0, 'category'],
           'royalties': token.loc[0, 'royalties'],
           'is_public': token.loc[0, 'is_public'],
           'is_nsfw': token.loc[0, 'is_nsfw'],
           'uri': f"data:image/{extension};base64,{download_blob_data(container, image_path)}",
           'token_id': token_id,
           'type': type,
           'price': price,
           'end_date': end_date,
           'my': my}
    bid_history = [{'price': row['current_price'], 'username': row['username'], 'date': row['sys_start_time']}
                   for _, row in bid.iterrows()]
    pp_extension = user_infos.loc[0, 'profile_picture_extension']
    pp_path = pp_extension if pp_extension == 'default-profile.png' else f"{username.lower()}.{pp_extension}"
    profile_picture = download_blob_data(PROFILE_PICTURES_CONTAINER, pp_path)
    pp = f"data:{pp_extension};base64,{profile_picture}"
    return render_template(f'app/nft.html', user=user, nft=nft, bids=bid_history, pp=pp)


@bp.route('/nft_back', methods=('GET', 'POST'))
@jwt_required
def nft_back() -> str:
    username = get_jwt_identity()['username']
    print(request.form)
    if request.method == 'POST':
        if "more" in request.form:
            data_nft_back = get_nft_back(session.get('nft_back'), username)
            session['nft_back'] = session.get('nft_back') + 1
            message = "Successfully claimed NFT."
            return json.dumps({"status": 200, "pictures": data_nft_back, "message": message})

        if "type" in request.form and request.form['type'] == 'sell':
            if 'token_id' not in request.form:
                e_full = "Token ID is required."
                return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
            if 'price' not in request.form:
                e_full = "Price is required."
                return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
            try:
                int(request.form['token_id'])
            except ValueError:
                e_full = "Enter an integer for token ID."
                return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
            try:
                int(request.form['price'])
            except ValueError:
                e_full = "Enter an integer for Price."
                return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
            token_id = int(request.form['token_id'])
            price = int(request.form['price'])
            address = get_address_from_username(username)
            create_resale_from_back(username, token_id, price, address)
            message_full = f"Successfully put Token {token_id} on sell"
            return json.dumps({"status": 200, "message": TRANSACTION_STARTED, "message_full": message_full})

        if "type" in request.form and request.form['type'] == 'check':
            if 'token_id' not in request.form:
                e_full = "Token ID is required."
                return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
            if 'address' not in request.form:
                e_full = "Address is required."
                return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
            try:
                int(request.form['token_id'])
            except ValueError:
                e_full = "Enter an integer for token ID."
                return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
            if get_address_from_username(username) != request.form['address']:
                e_full = "You don't use the same address on your Account. Please update your address in your Account."
                return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
            token_id = int(request.form['token_id'])
            if token_id not in list_account_assets(ADDRESS_ALGO_OURSELF):
                e_full = f"Token {token_id} was already sent."
                return json.dumps({"status": 404, "e": WRONG_REQUEST, "e_full": e_full})
            address = request.form['address']
            bool_optin = token_id in list_account_assets_all(address)
            bool_tx = check_algo_for_tx(address, PRICE_GET_BACK, bool_optin)
            if not bool_tx:
                e_full = "Not enough ALGO on your address, please fund your wallet."
                return json.dumps({"status": 404, "e": TRANSACTION_ERROR, "e_full": e_full})
            if token_id <= 191702862:
                amount = 1000
            else:
                amount = PRICE_GET_BACK
            message_full = "Wait a few seconds to get your NFT"
            return json.dumps({"status": 200, "username": username, "check_token": bool_optin, "price": amount,
                               "address": ADDRESS_ALGO_OURSELF, "message": TRANSACTION_STARTED,
                               "message_full": message_full})

        if "type" in request.form and request.form['type'] == 'get_back':
            if 'token_id' not in request.form:
                e_full = "Token ID is required."
                return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
            if 'address' not in request.form:
                e_full = "Address is required."
                return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
            try:
                int(request.form['token_id'])
            except ValueError:
                e_full = "Enter an integer for Token ID."
                return json.dumps({"status": 404, "e": WRONG_ARGUMENT, "e_full": e_full})
            if 'txID' not in request.form:
                e_full = "Transaction ID is required."
                return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
            token_id = int(request.form['token_id'])
            address = request.form['address']
            tx_id = request.form['txID']
            result = send_nft_back(token_id, address, tx_id, username)
            if result:
                message_full = "NFT was successfully sent."
                return json.dumps({"status": 200, "message": TRANSACTION_DONE, "message_full": message_full})
            e_full = "Issue during the transfer, please retry."
            return json.dumps({"status": 404, "e": WRONG, "e_full": e_full})
        e_full = "Endpoint not found."
        return json.dumps({"status": 404, "e": NO_API, "e_full": e_full})
    session['nft_back'] = 0
    pp_extension = session['extension']
    pp_path = pp_extension if pp_extension == 'default-profile.png' else f"{username.lower()}.{pp_extension}"
    profile_picture = download_blob_data(PROFILE_PICTURES_CONTAINER, pp_path)
    pp = f"data:{pp_extension};base64,{profile_picture}"
    return render_template(f'app/nft_back.html', pp=pp)


@bp.route('/nft_visit/<token_id>', methods=('GET', 'POST'))
def nft_visit(token_id: int) -> str:
    bid = get_historical_bid(token_id)
    token = get_info_token(token_id)

    # create user variable
    username = token.loc[0, 'username']
    pp_extension = get_profile_picture_extension_from_username(username)
    pp_path = pp_extension if pp_extension == 'default-profile.png' else f"{username.lower()}.{pp_extension}"
    profile_picture = download_blob_data(PROFILE_PICTURES_CONTAINER, pp_path)
    pp = f"data:{pp_extension};base64,{profile_picture}"
    user = {'username': username,
            'fullname': get_fullname_from_username(username),
            'profile_picture': pp}

    # create nft variable
    container = IMAGES_CONTAINER if token.loc[0, 'is_public'] and not token.loc[0, 'is_nsfw'] else BLURRY_IMAGES_CONTAINER
    extension = token.loc[0, 'extension']
    image_path = f"{token.loc[0, 'username'].lower()}/{token.loc[0, 'swarm_hash']}.{extension}"
    type = "bid" if get_date_from_token_id(token_id) > datetime.utcnow() else "buy" if is_resale(token_id) else "none"
    price = None if type == "none" else int(get_current_price_from_token_id(token_id) * 1.1) + 1 if type == "bid" else get_price_resale(token_id)
    nft = {'title': token.loc[0, 'title'],
           'number': token.loc[0, 'number'],
           'description': token.loc[0, 'description'],
           'category': token.loc[0, 'category'],
           'royalties': token.loc[0, 'royalties'],
           'is_public': token.loc[0, 'is_public'],
           'is_nsfw': token.loc[0, 'is_nsfw'],
           'uri': f"data:image/{extension};base64,{download_blob_data(container, image_path)}",
           'token_id': token_id,
           'type': type,
           'price': price}
    bid_history = [{'price': row['current_price'], 'username': "test", 'date': row['sys_start_time']}
                   for _, row in bid.iterrows()]
    return render_template(f'app/unauth/nft.html', user=user, nft=nft, bids=bid_history)


@bp.route('/wallet_installed', methods=('GET', 'POST'))
@jwt_required
def wallet_installed():
    email = get_jwt_identity()['email']
    if 'wallet' not in request.form:
        e_full = "Wallet is required."
        return json.dumps({"status": 404, "e": MISSING_ARGUMENT, "e_full": e_full})
    address = json.loads(request.form['wallet'])[0]['address']
    update_address(email, address)
    session["installed"] = True
    message = "Address was updated."
    return json.dumps({"status": 200, "message": message})
