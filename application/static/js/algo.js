const LEDGER = 'TestNet';

function connect(callback = () => {}) {
    if (typeof AlgoSigner === 'undefined') {
        alert('AlgoSigner is not installed. Please install it.');
        return
    }

    AlgoSigner.connect()
        .then((e) => {
            AlgoSigner.accounts({
                ledger: LEDGER
            }).then((d) => {
                callback(d);
            })
            .catch((e) => {
                addTooltip("Failed to connect to AlgoSigner", "Please check that you have properly installed it.");
            });
        })
        .catch((e) => {
        });
}

function account(callback = (name) => { }, errorCallback = () => { }) {
    AlgoSigner.accounts({
        ledger: LEDGER
    })
    .then((d) => {
        callback(d[0]['address']);
    })
    .catch((e) => {
        connect(() => {
            account(callback);
        });
    });
}

function get_param(callback = (txParams) => { }, errorCallback = () => { }) {
    AlgoSigner.algod({
        ledger: LEDGER,
        path: '/v2/transactions/params'
    })
    .then((d) => {
        callback(d);
    })
    .catch((e) => {
        errorCallback();
        console.error(e);
        addTooltip("Failed to get the parameters for the transaction", "Please retry the transaction. If the problem persits, send us an email.");
    });
}


function pay(from, to, amount, note, txParams, callback = (status) => { }, errorCallback = () => { }) {
    AlgoSigner.sign({
        from: from,
        to: to,
        amount: amount,
        note: note,
        type: 'pay',
        fee: txParams['fee'],
        firstRound: txParams['last-round'],
        lastRound: txParams['last-round'] + 1000,
        genesisID: txParams['genesis-id'],
        genesisHash: txParams['genesis-hash']
    })
    .then((d) => {
        callback(d);
    })
    .catch((e) => {
        errorCallback();
        console.error(e);
        addTooltip("Failed to create the transaction", "Please retry. If the problem persits, send us an email.");
    });
}

function get_status(txID) {
    AlgoSigner.algod({
        ledger: LEDGER,
        path: '/v2/transactions/pending/' + txID
    })
        .then((d) => {
            console.log(d);
        })
        .catch((e) => {
            console.error(e);
        });
}

function send_algo(signedTx, callback = (status) => { }, errorCallback = () => {}) {
    AlgoSigner.send({
        ledger: LEDGER,
        tx: signedTx.blob
    })
    .then((d) => {
        callback(d);
    })
    .catch((e) => {
        console.error(e);
        errorCallback();
    });
}

function AlgoPay(to, amount, note, token_id, url, type) {
    account((from) => {
        get_param((tx) => {
            pay(from, to, amount, note, tx, (signedTx) => {
                send_algo(signedTx, (s) => {
                    get_status(signedTx.txID);
                    submitTransaction(amount, from, token_id, url, signedTx.txID, type);
                }, () => {
                    cancelTransaction(amount, from, token_id, url);
                });
            }, () => {
                cancelTransaction(amount, from, token_id, url);
            });
        }, () => {
            cancelTransaction(amount, from, token_id, url);
        });
    });
}

function submitTransaction(amount, from, token_id, url, txID, type) {
    var http = new XMLHttpRequest();
    http.open('POST', "/" + url, true);
    http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    http.onreadystatechange = function () {//Call a function when the state changes.
        if (http.readyState == 4 && http.status == 200) {
            if (type == "validate_resale") {
                addTooltip("Buy successfull", "You bought Token ID " + token_id + " for " + (amount / 1000000) + " algo");
                try {
                    document.getElementById("picture-" + token_id).remove();
                } catch (error) {
                    
                }
            } else {
                addTooltip("Bid successfull", "Your bid for " + token_id + ": " + (amount / 1000000) + " algo");
            }
        }
    }
    http.send("token_id=" + token_id + "&type=" + type + "&price=" + amount + "&address=" + from + "&txID=" + txID);
}


function cancelTransaction(amount, from, token_id, url) {
    var http = new XMLHttpRequest();
    http.open('POST', "/" + url, true);
    http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    http.onreadystatechange = function () {//Call a function when the state changes.
        if (http.readyState == 4 && http.status == 200) {
        }
    }
    http.send("token_id=" + token_id + "&type=error_new" + "&price=" + amount + "&address=" + from);
}

function setupTX(from, txParams, token_id, callback=() => {}) {
    let txn = {
        type: 'axfer',
        from: from,
        to: 
        "HKDGSHRLJJLQP463PPTGIRQWMSPOIWR5CGAOCKOHOEH3WEU44SEYIDHPR4",
        fee: txParams['fee'],
        firstRound: txParams['last-round'],
        lastRound: txParams['last-round'] + 1000,
        genesisID: txParams['genesis-id'],
        genesisHash: txParams['genesis-hash'],

        amount: 1,
        assetIndex: token_id
    };
    callback(txn)
}


function AlgoTransferAsset(token_id, price, url) {
    account((from) => {
        get_param((txParams) => {
            setupTX(from, txParams, token_id, (txn) => {
                AlgoSigner.sign(txn)
                    .then((d) => {
                        signedTx = d;
                        send_algo(d, (s) => {
                            validateTransfer(token_id, price, url, signedTx.txID);
                        });
                    })
                    .catch((e) => {
                        addTooltip("Failed to create the transaction", "Please retry. If the problem persits, send us an email.");
                        console.error(e);
                    });
            });
        });
    });
}

function validateTransfer(token_id, price, url, txID) {
    var http = new XMLHttpRequest();
    http.open('POST', "/" + url, true);
    http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    http.onreadystatechange = function () {//Call a function when the state changes.
        if (http.readyState == 4 && http.status == 200) {
            addTooltip("Resale successfull", "Token ID " + token_id + " resale is on for " + price + " algo");
            try {
                document.getElementById("picture-" + token_id).remove();
            } catch (error) {
                
            }
        }
    }
    http.send("token_id=" + token_id + "&type=sell" + "&price=" + price + "&txID="+txID);
}


/// Buy

function signIn(from, token_id, note, txParams, callback = () => {}, errorCallback = () => {}) {
    AlgoSigner.sign({
        from: from,
        to: from,
        assetIndex: token_id,
        note: note,
        amount: 0,
        type: 'axfer',
        fee: txParams['fee'],
        firstRound: txParams['last-round'],
        lastRound: txParams['last-round'] + 1000,
        genesisID: txParams['genesis-id'],
        genesisHash: txParams['genesis-hash']
    })
        .then((d) => {
            signedTx = d;
            callback(d);
        })
        .catch((e) => {
            console.error(e);
            errorCallback(e);
        });
}

function AlgoSignIn(amount, token_id, url) {
    let note = "";
    account((from) => {
        get_param((tx) => {
            signIn(from, token_id, note, tx, (signedTx) => {
                send_algo(signedTx, (s) => {
                    submitSignIn(amount, from, token_id, url);
                });
            });
        });
    });
}

function submitSignIn(amount, from, token_id, url) {
    var http = new XMLHttpRequest();
    http.open('POST', "/" + url, true);
    http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    http.onreadystatechange = function () {//Call a function when the state changes.
        if (http.readyState == 4 && http.status == 200) {
            let parsed = JSON.parse(http.responseText);
            if (parsed.status == 404) {
                addTooltip("Could not buy " + token_id, parsed.e);
            } else if (parsed.status == 200) {
                AlgoPay(parsed.to, parsed.amount, parsed.note, token_id, url, "validate_resale");
            }
        }
    }
    http.send("token_id=" + token_id  + "&price=" + amount + "&address=" + from + "&type=resale");
}

function AlgoCreateNFT(token_id, callback = ()=>{}) {
    let note = "";
    account((from) => {
        get_param((tx) => {
            signIn(from, token_id, note, tx, (signedTx) => {
                send_algo(signedTx, (s) => {
                    addTooltip("Opt in succesfull, redirecting you to the gallery.", "");
                    callback(from, tx, signedTx);
                }, () => {
                    AlgoCreateNFT(token_id, callback)
                });
            }, () => {
                AlgoCreateNFT(token_id, callback)
            });
        }, () => {
            AlgoCreateNFT(token_id, callback)
        });
    }, () => {
        AlgoCreateNFT(token_id, callback)
    });
}