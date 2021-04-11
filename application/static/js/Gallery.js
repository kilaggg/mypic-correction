const GALLERY_KIND = {
    BUY: "buy",
    BID: "bid",
    PREVIEW_BUY: "preview_buy",
    PREVIEW_BID: "preview_bid",
    SELL: "sell",
    SELLING: "selling",
    CANCEL: "cancel",
    GET_BACK: "get_back",
    DEFAULT: "",
}

class GalleryModal {
    constructor(page, image) {
        this._render(page, image);
    }

    _render(page, image) {
        // Holder
        let modal_div = document.createElement("div");
        modal_div.id = "modal_" + image.token_id;
        modal_div.classList.add("modal");
        modal_div.classList.add("fade");
        modal_div.setAttribute("role", "dialog");
        document.getElementById(page+"_div").appendChild(modal_div);
    
        let modal_content = document.createElement("div");
        modal_content.classList.add("modal-dialog");
        modal_content.classList.add("modal-lg");
        modal_div.appendChild(modal_content);
    
        // Headerr
        let modal_header = document.createElement("div");
        modal_header.classList.add("modal-header");
        modal_content.appendChild(modal_header);
    
        let close_button = document.createElement("button");
        close_button.setAttribute("type", "button");
        close_button.setAttribute("data-dismiss", "modal");
        close_button.classList.add("close");
        close_button.innerHTML = "&times";
        modal_header.append(close_button);
    
        let title = document.createElement("h1");
        title.classList.add("modal-title");
        title.innerText = image.token_id + ": " + image.title_full;
        modal_header.append(title);
    
        // Body
        let modal_body = document.createElement("div");
        modal_body.classList.add("modal-form")
        modal_content.appendChild(modal_body);
    
        let img = document.createElement("img");
        img.setAttribute("src", image.uri);
        modal_body.appendChild(img);
    
        // Details
        let img_infos = document.createElement("div");
        img_infos.classList.add("image-infos");
        modal_body.appendChild(img_infos);
    
        let user = document.createElement("a");
        user.setAttribute("href", "/gallery/" + image.username);
        user.classList.add("modal-user");
        img_infos.append(user);
    
        let pp = document.createElement("div");
        pp.classList.add("modal-pp");
        pp.setAttribute("style", "background-image:url(" + image.pp + ")");
        user.appendChild(pp);
    
        let username = document.createElement("div");
        username.innerText = image.username;
        username.classList.add("modal-username");
        user.appendChild(username);
    
        let description = document.createElement("div");
        description.classList.add("image-description");
        description.innerText = image.description;
        img_infos.appendChild(description);
    

        // Footer
        let modal_footer = document.createElement("div");
        modal_footer.classList.add("modal-footer");
        modal_content.appendChild(modal_footer);
    
        let close_button2 = document.createElement("button");
        close_button2.setAttribute("type", "button");
        close_button2.setAttribute("data-dismiss", "modal");
        close_button2.classList.add("btn");
        close_button2.classList.add("btn-default");
        close_button2.innerHTML = "Close";
        modal_footer.append(close_button2);
    }
}

class GalleryImage {
    constructor (url, page, image, type) {
        this.url = url;
        this._render(page, image, type);
    }

    _render(page, image, type) {
        // Holder
        let picture_div = document.createElement("div");
        this.holder = picture_div;
        picture_div.id = "picture-" + image.token_id;
        picture_div.classList.add("picture");
        document.getElementById(page + "_div").appendChild(picture_div);

        // User description
        let user = document.createElement("a");
        user.setAttribute("href", "/gallery/" + image.username);
        user.classList.add("picture-user");
        picture_div.append(user);

        let pp = document.createElement("div");
        pp.classList.add("picture-pp");
        pp.setAttribute("style", "background-image:url(" + image.pp + ")");
        user.appendChild(pp);

        let username = document.createElement("div");
        username.innerText = image.username;
        username.classList.add("picture-username");
        user.appendChild(username);

        // Title of the image
        let title = document.createElement("div");
        title.innerText = image.title;
        title.classList.add("picture-title");
        picture_div.appendChild(title);

        // Image Form
        let form = document.createElement("div");
        form.classList.add("picture-form")
        picture_div.appendChild(form);
    
        if (type == GALLERY_KIND.BID || type == GALLERY_KIND.PREVIEW_BID) {
            this._bid(image, form, type == GALLERY_KIND.PREVIEW_BID);
        } else if (type == GALLERY_KIND.BUY || type == GALLERY_KIND.PREVIEW_BUY) {
            this._buy(image, form, type == GALLERY_KIND.PREVIEW_BUY);
        } else if (type == GALLERY_KIND.GET_BACK) {
            this._get_back(image, form);
        } else if (type == GALLERY_KIND.CANCEL) { 
            this._cancel(image, form);
        } else if (type == GALLERY_KIND.SELL) {
            this._sell(image, form);
        } else if (type == GALLERY_KIND.SELLING) {
            this._selling(image, form);
        }

        // Modal
        let image_button = document.createElement("button");
        image_button.setAttribute("type", "button");
        image_button.setAttribute("data-toggle", "modal");
        image_button.setAttribute("data-target", "#modal_" + image.token_id);
        image_button.classList.add("img-button");
        image_button.classList.add("picture-photo");
        picture_div.appendChild(image_button);

        var img = new Image()
        img.src = window.URL.createObjectURL(b64toBlob(image.uri, image.extension));
        image_button.appendChild(img);

        new GalleryModal(page, image);
    }
    _buy(image, form, isPreview = false) {
        console.log("buy")
        let price = document.createElement("div");
        price.classList.add("picture-price")
        price.setAttribute("name", "price");
        price.innerText = image.price;
        form.appendChild(price);

        let algo = document.createElement("div");
        algo.classList.add("algo");
        form.appendChild(algo);

        if (!isPreview) {
            let submit = document.createElement("button");
            submit.setAttribute("type", "submit");
            submit.setAttribute("name", "buy");
            submit.classList.add("buy-button");
            submit.addEventListener("click", () => {
                new Contract(CONTRACT_KIND.BUY, this.url, image.token_id, image.price);
            });
            submit.innerText = "Buy";
            form.appendChild(submit);
        }

        let seller = document.createElement("a");
        seller.classList.add("picture-seller");
        seller.innerText = "Sold by: " + image.seller;
        seller.setAttribute("href", "/gallery/" + image.seller);
        this.holder.appendChild(seller);
    }

    _bid(image, form, isPreview = false) {
        let price
        if (!isPreview) {
            price = document.createElement("input");
            price.classList.add("picture-bid")
            price.setAttribute("type", "number");
            price.setAttribute("name", "price");
            price.setAttribute("min", image.min_price);
            price.setAttribute("value", image.min_price);
            form.appendChild(price);
        } else {
            price = document.createElement("div");
            price.classList.add("picture-bid");
            price.innerText = image.min_price;
            form.appendChild(price);
        }

        let algo = document.createElement("div");
        algo.classList.add("algo");
        form.appendChild(algo);

        if (!isPreview) {
            let submit = document.createElement("button");
            submit.setAttribute("name", "bid");
            submit.classList.add("buy-button");
            submit.addEventListener("click", () => {
                new Contract(CONTRACT_KIND.BID, this.url, image.token_id, price.value);
            });
            submit.innerText = "Bid";
            form.appendChild(submit);
        }

        let countdown = document.createElement("div");
        countdown.classList.add("picture-countdown");
        createCountdown(image.end_date.replace(" ", "T"), countdown);
        this.holder.appendChild(countdown);
    }

    _sell(image, form) {
        let price = document.createElement("input");
        price.classList.add("picture-price")
        price.setAttribute("type", "number");
        price.setAttribute("name", "price");
        price.setAttribute("min", "0");
        form.appendChild(price);

        let algo = document.createElement("div");
        algo.classList.add("algo");
        form.appendChild(algo);

        let submit = document.createElement("button");
        submit.setAttribute("name", "sell");
        submit.innerText = "Sell";
        submit.addEventListener("click", () => {
            new Contract(CONTRACT_KIND.SELL, this.url, image.token_id, price.value);
        })
        form.appendChild(submit);
    }

    _selling(image, form) {
        let price = document.createElement("div");
        price.classList.add("picture-price")
        price.setAttribute("name", "price");
        price.innerText = image.price;
        form.appendChild(price);

        let algo = document.createElement("div");
        algo.classList.add("algo");
        form.appendChild(algo);

        let countdown = document.createElement("div");
        countdown.classList.add("picture-countdown");
        createCountdown(image.end_date.replace(" ", "T"), countdown);
        this.holder.appendChild(countdown);
    }

    _cancel(image, form) {
        let price = document.createElement("div");
        price.classList.add("picture-price")
        price.setAttribute("name", "price");
        price.innerText = image.price;
        form.appendChild(price);

        let algo = document.createElement("div");
        algo.classList.add("algo");
        form.appendChild(algo);

        let submit = document.createElement("button");
        submit.setAttribute("type", "submit");
        submit.setAttribute("name", "cancel");
        submit.addEventListener("click", () => {
            new Contract(CONTRACT_KIND.CANCEL, this.url, image.token_id);
        });
        submit.innerText = "Cancel";
        form.appendChild(submit);
    }

    _get_back(image, form) {
        let submit = document.createElement("button");
        submit.setAttribute("name", "get_back");
        submit.classList.add("get-back-button");
        submit.addEventListener("click", () => {
            new Contract(CONTRACT_KIND.GET_BACK, this.url, image.token_id);
        });
        submit.innerText = "Get";
        form.appendChild(submit);
    }
}

class Gallery {
    displayedFirst = { };
    endPage = { };
    requestedMorePictures = {};
    currentPage;

    constructor(url, subpages, errors, subpagesType, askForMore=true) {
        this.url = url;
        this.subpages = subpages;
        this.errors = errors;
        this.subpageType = subpagesType;
        this.askForMore = askForMore;

        for (let page of this.subpages) {
            this.displayedFirst[page] = false;
            this.endPage[page] = false;
            this.requestedMorePictures[page] = false;

            try {
                document.getElementById(page + "_button").addEventListener("click", () => {
                    this._switch_page(page);
                });
            } catch (error) {}
        }

        if (this.subpages.length > 1) {
            let s = window.location.hash.substring(1);
            if (this.subpages.includes(s)) {
                this._switch_page(s);
            } else {
                this._switch_page(this.subpages[0]);
            }
        } else {
            this.currentPage = this.subpages[0];
            this._requestMore(this.subpages[0]);
        }
    
        window.addEventListener('scroll', (event) => {
            if (window.scrollY + window.innerHeight > 0.8 * document.documentElement.scrollHeight
                && this.displayedFirst[this.currentPage]
                && !this.requestedMorePictures[this.currentPage]
                && !this.endPage[this.currentPage]) {
                this._requestMore(this.currentPage);
            }
        });
    }

    _switch_page(page) {
        window.scrollTo(0, 0);
        window.location.hash = (this.subpages[0] != page) ? page : "";

        this.currentPage = page;
    
        if (!this.displayedFirst[page]) {
            this._requestMore(page);
        }
    
        for (let x of this.subpages) {
            if (x == page) {
                document.getElementById(x + "_div")
                    .classList.remove("hidden");
                document.getElementById(x + "_button")
                    .classList.add("selected");
            } else {
                document.getElementById(x + "_div")
                    .classList.add("hidden");
                document.getElementById(x + "_button")
                    .classList.remove("selected");
            }
        }
    }

    _displayMore(images, page) {
        if (images.length == 0) {
            if (!this.displayedFirst[page]) {
                document.getElementById(page + "_div").innerHTML = "<p>" + this.errors[page] + "</p>" ;
            }
            this.endPage[page] = true;
            return;
        }
        this.displayedFirst[page] = true;
    
        for (let image of images) {
            new GalleryImage(this.url, page, image, this.subpageType[page]);
        }
    
        if(!this.askForMore) {
            this.endPage[page] = true;
        }
    }

    filter(images, page) {
        document.getElementById(page + "_div").innerHTML = "";
        this._displayMore(images, page);
    }

    _requestMore(page) {
        if (this.endPage[page]) return;
        this.requestedMorePictures[page] = true;

        if (document.querySelector(".loading")) 
            document.querySelector(".loading").classList.remove("hidden");

        var http = new XMLHttpRequest();
        http.open('POST', "/" + this.url, true);
        http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
        http.onreadystatechange = () => {
            if (http.readyState == 4 && http.status == 200) {
                this._displayMore(JSON.parse(http.responseText).pictures, page);
                if (document.querySelector(".loading")) 
                    document.querySelector(".loading").classList.add("hidden");
                this.requestedMorePictures[page] = false;
            }
        }
        http.send("more=" + page);
    }
}


/* Utils for Gallery */
function b64toBlob(dataURI, extension) {
    var byteString = atob(dataURI.split(',')[1]);
    var ab = new ArrayBuffer(byteString.length);
    var ia = new Uint8Array(ab);

    for (var i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: 'image/' + extension });
}

function createCountdown(initialDate, countdown) {
    var countDownDate = new Date(initialDate).getTime();
    var x = setInterval(function () {
        var now = localDateToUTC(new Date()).getTime();
        var distance = countDownDate - now;
        var days = Math.floor(distance / (1000 * 60 * 60 * 24));
        var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        minutes = (minutes < 10) ? "0" + minutes : minutes;
        var seconds = Math.floor((distance % (1000 * 60)) / 1000);
        seconds = (seconds < 10) ? "0" + seconds : seconds;

        countdown.innerText = + days + " days and " + hours + ":"
            + minutes + ":" + seconds + "";

        if (distance < 0) {
            clearInterval(x);
            countdown.innerHTML = "EXPIRED";
        }
    }, 1000);
}

function localDateToUTC(localDate) {
    return new Date(localDate.getUTCFullYear(), localDate.getUTCMonth(), localDate.getUTCDate(),
                    localDate.getUTCHours(), localDate.getUTCMinutes(), localDate.getUTCSeconds());
}