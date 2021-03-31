function bid(token_id, price, url) {
    let bidPrice = price.value;
    var http = new XMLHttpRequest();
    http.open('POST', "/" + url, true);
    http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    http.onreadystatechange = function () {//Call a function when the state changes.
        if (http.readyState == 4 && http.status == 200) {
            let parsed = JSON.parse(http.responseText);
            if (parsed.status == 404) {
                addTooltip("Bid failled for " + token_id, parsed.e);
            } else if (parsed.status == 200) {
                addTooltip("Bid in process, allow up to a minute for the process.", "");
                AlgoPay(parsed.to, parsed.amount, parsed.note, token_id, url, "validate_new");
            }
        }
    }
    http.send("token_id=" + token_id + "&type=new" + "&price=" + bidPrice);
}

function buy(token_id, price, url) {
    let bidPrice = parseInt(price.innerText);
    addTooltip("Buy in process, allow up to a minute for the process.", "");
    AlgoSignIn(bidPrice, token_id, url);
}

function sell(token_id, price, url) {
    let bidPrice = price.value;
    if (isNaN(bidPrice)) {
        addTooltip("Input a price to sell the picture");
        return;
    }
    addTooltip("Sell in process, allow up to a minute for the process.", "");
    AlgoTransferAsset(token_id, bidPrice, url);
}

function cancel(token_id, url) {
    addTooltip("Cancelation of  " + token_id + " in process");
    var http = new XMLHttpRequest();
    http.open('POST', "/" + url, true);
    http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    http.onreadystatechange = function () {//Call a function when the state changes.
        if (http.readyState == 4 && http.status == 200) {
            addTooltip("Sell of " + token_id + " cancelled");
            try {
                document.getElementById("picture-" + token_id).remove();
            } catch (error) {
                
            }
        }
    }
    http.send("token_id=" + token_id + "&type=cancel");
}