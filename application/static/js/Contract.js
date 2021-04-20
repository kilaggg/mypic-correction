const LEDGER = 'MainNet';
const CONTRACT_KIND = {
    BUY: "buy",
    BID: "bid",
    SELL: "sell",
    CANCEL: "cancel",
    GET_BACK: "get_back",
    DIRECT_SELL: "direct_sell",
    ICO: "ico",
}

class AlgoSignerAPI {
    constructor() {}

    static connect(callback = () => {}, errorCallback = () => {}) {
        if (typeof AlgoSigner === 'undefined') {
            alert('AlgoSigner is not installed. Please install it.');
            return
        }
    
        AlgoSigner.connect()
            .then((d) => {
                callback(d)
            })
            .catch((e) => {
                errorCallback (e);
                addTooltip("Failed to connect to AlgoSigner", "Please check that you have properly installed it.");
            });
    }


    static account(callback = () => { }, errorCallback = () => { }) {
        AlgoSigner.accounts({
            ledger: LEDGER
        }).then((d) => {
            if (d.length == 0) {
                addTooltip("Failed to get your Algo Address.", "Please check that you have at least one address in your wallet.");
                return;
            }
            callback(d[0]['address'], d);
        })
        .catch((e) => {
            errorCallback (e);
            AlgoSignerAPI.connect(() => {
                AlgoSignerAPI.account(callback, errorCallback)
            });
        });
    }

    static get_param(callback = () => { }, errorCallback = () => { }) {
        AlgoSigner.algod({
            ledger: LEDGER,
            path: '/v2/transactions/params'
        })
        .then((d) => {
            callback(d);
        })
        .catch((e) => {
            errorCallback(e);
            addTooltip("Failed to get the parameters for the transaction", "Please retry the transaction. If the problem persists, send us an email.");
            console.error(e);
        });
    }

    static signPay(from, to, amount, note, txParams, callback = () => { }, errorCallback = () => { }) {
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
            errorCallback(e);
            console.error(e);
            addTooltip("Failed to create the transaction", "Please retry. If the problem persists, send us an email.");
        });
    }

    static signIn(from, token_id, note, txParams, callback = () => {}, errorCallback = () => {}) {
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
                callback(d);
            })
            .catch((e) => {
                console.error(e);
                errorCallback(e);
            });
    }

    static send_algo(signedTx, callback = () => { }, errorCallback = () => {}) {
        AlgoSigner.send({
            ledger: LEDGER,
            tx: signedTx.blob
        })
        .then((d) => {
            callback(d);
        })
        .catch((e) => {
            console.error(e);
            errorCallback(e);
        });
    }

    static signAXFER(from, to, txParams, token_id, callback=() => {}, errorCallback = () => {}) {
        AlgoSigner.sign({
            type: 'axfer',
            from: from,
            to: to,
            fee: txParams['fee'],
            firstRound: txParams['last-round'],
            lastRound: txParams['last-round'] + 1000,
            genesisID: txParams['genesis-id'],
            genesisHash: txParams['genesis-hash'],
    
            amount: 1,
            assetIndex: token_id
        })
            .then((d) => {
                callback(d);
            })
            .catch((e) => {
                console.error(e);
                addTooltip("Failed to create the transaction", "Please retry. If the problem persists, send us an email.");
                errorCallback(e);
            });
    }

    static createNFT(token_id, callback = ()=>{}) {
        let note = "";
        AlgoSignerAPI.account((from) => {
            AlgoSignerAPI.get_param((tx) => {
                AlgoSignerAPI.signIn(from, token_id, note, tx, (signedTx) => {
                    AlgoSignerAPI.send_algo(signedTx, 
                        (s) => {
                            addTooltip("Asset opt-in successful, redirecting you to the gallery.", "");
                            callback(from, tx, signedTx);
                        }, 
                        () => { AlgoCreateNFT(token_id, callback) });
                    }, 
                    () => { AlgoCreateNFT(token_id, callback) });
                }, 
                () => { AlgoCreateNFT(token_id, callback) });
            }, 
            () => { AlgoCreateNFT(token_id, callback) });
    }
}


class Contract {
    constructor(type, url, token_id, price = 0) {
        switch (type) {
            case CONTRACT_KIND.BUY:
                this._buy(url, token_id, price);
                break;
            case CONTRACT_KIND.BID:
                this._bid(url, token_id, price);
                break;
            case CONTRACT_KIND.SELL:
                this._sell(url, token_id, price);
                break;
            case CONTRACT_KIND.DIRECT_SELL:
                this._direct_sell(url, token_id, price);
                break;
            case CONTRACT_KIND.CANCEL:
                this._cancel(url, token_id);
                break;
            case CONTRACT_KIND.GET_BACK:
                this._getBack(url, token_id);
                break;
        
            case CONTRACT_KIND.ICO:
                this._ico(url, price);
            default:
                break;
        }
    }

    _bid(url, token_id, price) {
        AlgoSignerAPI.account((from) => {
            AlgoSignerAPI.get_param((tx) => {
                this._callServer(url, "token_id=" + token_id + "&type=new" + "&price=" + price + "&address=" + from, (parsed) => {
                    let to = parsed.to;
                    let amount = parsed.amount;
                    let note = parsed.note;
                    if (parsed.check_token) {
                        this._bid_in_progress(url, token_id, from, to, tx, amount, note);
                    } else {
                        AlgoSignerAPI.signIn(from, token_id, "", tx, (signedTx) => {
                            AlgoSignerAPI.send_algo(signedTx, (s) => {
                                this._bid_in_progress(url, token_id, from, to, tx, amount, note);
                            });
                        });
                    }
                });
            });
        });
    }

    _bid_in_progress(url, token_id, from, to, tx, amount, note) {
        AlgoSignerAPI.signPay(from, to, amount, note, tx, (signedTx) => {
            AlgoSignerAPI.send_algo(signedTx, (s) => {
                this._callServer(url, 
                    "token_id=" + token_id + "&type=validate_new" + "&price=" + amount + "&address=" + from + "&txID=" + signedTx.txID, 
                    () => {
                        //addTooltip("Bid: successful", "Your bid for Token ID " + token_id + " for " + (amount / 1000000) + " ALGO");
                    }
                );
            }, () => {
                this.cancelTransaction(url, token_id, from, amount);
            });
        });
    }

    _buy(url, token_id, amount) {
        AlgoSignerAPI.account((from) => {
            this._callServer(url, "token_id=" + token_id + "&address=" + from + "&type=check_resale&price=" + amount, (parsed) => {
                let note = parsed.username + "_" + token_id;
                AlgoSignerAPI.get_param((tx) => {
                    if (parsed.check_token) {
                        this._buy_in_progress(url, token_id, from, amount, note, tx);
                    } else {
                        AlgoSignerAPI.signIn(from, token_id, "", tx, (signedTx) => {
                            AlgoSignerAPI.send_algo(signedTx, (s) => {
                                this._buy_in_progress(url, token_id, from, amount, note, tx);
                            });
                        });
                    }
                });
            });
        });
    }

    _buy_in_progress(url, token_id, from, amount, note, tx) {
        this._callServer(url, "token_id=" + token_id  + "&price=" + amount + "&address=" + from + "&type=resale", (parsed) => {
            let to = parsed.to;
            amount = parsed.amount;
            note = parsed.note;
            AlgoSignerAPI.signPay(from, to, amount, note, tx, (signedTx) => {
                AlgoSignerAPI.send_algo(signedTx, (s) => {
                    this._callServer(url, 
                        "token_id=" + token_id + "&type=validate_resale" + "&price=" + amount + "&address=" + from + "&txID=" + signedTx.txID, () => {
                            //addTooltip("Buy: successful", "You bought Token ID " + token_id + " for " + (amount / 1000000) + " ALGO");
                            try {
                                document.getElementById("picture-" + token_id).remove();
                            } catch (error) {
                                
                            }
                        }
                    );
                }, () => {
                    this.cancelTransaction(url, token_id, from, amount)
                });
            }, () => {
                this.cancelTransaction(url, token_id, from, amount)
            });
        });
    }

    _sell(url, token_id, price) {
        price = parseInt(price);
        if (isNaN(price)) {
            addTooltip("Price is required to sell the picture");
            return;
        }
        this._callServer(url, "type=check_sell", (parsed) => {
            let to = parsed.address;
            AlgoSignerAPI.account((from) => {
                AlgoSignerAPI.get_param((txParams) => {
                    AlgoSignerAPI.signAXFER(from, to, txParams, token_id, (signedTx) => {
                        AlgoSignerAPI.send_algo(signedTx, (s) => {
                            this._callServer(url, 
                                "token_id=" + token_id + "&type=sell" + "&price=" + price + "&txID="+signedTx.txID, 
                                () => {
                                    try {
                                        document.getElementById("picture-" + token_id).remove();
                                    } catch (error) {
                                        
                                    }
                                }
                            );
                        });
                    });
                });
            });
        });
    }

    _direct_sell(url, token_id, price) {
        this._callServer(url, 
            "token_id=" + token_id + "&type=sell" + "&price=" + price, 
            () => {
                try {
                    document.getElementById("picture-" + token_id).remove();
                } catch (error) {
                    
                }
            }
        );
    }

    _cancel(url, token_id) {
        addTooltip("Cancel in progress, wait a minute.", "");
        this._callServer(url, "token_id=" + token_id + "&type=cancel", () => {
            try {
                document.getElementById("picture-" + token_id).remove();
            } catch (error) {
                
            }
        });
    }

    _getBack(url, token_id) {
        let to;
        let amount;
        let note = "";

        AlgoSignerAPI.account((from) => {
            this._callServer(url, "token_id=" + token_id + "&address=" + from + "&type=check", (parsed) => {
                to = parsed.address;
                amount = parsed.price;
                note = parsed.username + "_" + token_id;
                AlgoSignerAPI.get_param((tx) => {
                    if (parsed.check_token) {
                        this._getBack_in_progress(url, token_id, from, to, amount, note, tx);
                    } else {
                        AlgoSignerAPI.signIn(from, token_id, "", tx, (signedTx) => {
                            AlgoSignerAPI.send_algo(signedTx, (s) => {
                                this._getBack_in_progress(url, token_id, from, to, amount, note, tx);
                            });
                        });
                    }
                });
            });
        });
    }

    _getBack_in_progress(url, token_id, from, to, amount, note, tx) {
        AlgoSignerAPI.signPay(from, to, amount, note, tx, (signedTx) => {
            AlgoSignerAPI.send_algo(signedTx, (s) => {
                this._callServer(url, 
                    "token_id=" + token_id + "&type=get_back" + "&price=" + amount + "&address=" + from + "&txID=" + signedTx.txID, 
                    (parsed) => {
                        try {
                            document.getElementById("picture-" + token_id).remove();
                        } catch (error) {
                            
                        }
                    }
                );
            }, () => {
                this.cancelTransaction(url, token_id, from, amount)
            });
        });
    }

    _callServer(url, toSend, callback = () => {}) {
        var http = new XMLHttpRequest();
        http.open('POST', "/" + url, true);
        http.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
        http.onreadystatechange = function () {//Call a function when the state changes.
            console.log(http.status);
            if (http.readyState == 4 && http.status == 200) {
                console.log(http.responseText)
                let parsed = JSON.parse(http.responseText);
                if (parsed.status == 404) {
                    addTooltip(parsed.e, parsed.e_full);
                    return;
                }
                addTooltip(parsed.message, parsed.message_full);
                callback(parsed);
            } else if (http.status == 500){
                addTooltip("Failed to create the transaction", "Please retry. If the problem persists, send us an email.");
            }
        }
        http.send(toSend);
    }

    cancelTransaction(url, token_id, from, amount) {
        this._callServer(url, "token_id=" + token_id + "&type=error_new" + "&price=" + amount + "&address=" + from);
    }


    _ico(url, amount) {
        console.log(amount);
        AlgoSignerAPI.account((from) => {
            this._callServer(url, "address=" + from + "&type=check&price=" + amount, (parsed) => {
                amount = parsed.price;
                let token_id = parsed.token_id;
                let address = parsed.address;
                let note = "";//parsed.username + "_ico";
                AlgoSignerAPI.get_param((tx) => {
                    if (parsed.check_token) {
                        this._ico_in_progress(url, token_id, from, address, amount, note, tx);
                    } else {
                        AlgoSignerAPI.signIn(from, token_id, "", tx, (signedTx) => {
                            AlgoSignerAPI.send_algo(signedTx, (s) => {
                                this._ico_in_progress(url, token_id, from, address, amount, note, tx);
                            });
                        });
                    }
                });
            });
        });
    }

    _ico_in_progress(url, token_id, from, to, amount, note, tx) {
        AlgoSignerAPI.signPay(from, to, amount, note, tx, (signedTx) => {
            AlgoSignerAPI.send_algo(signedTx, (s) => {
                this._callServer(url, 
                    "token_id=" + token_id + "&type=validate" + "&price=" + amount + "&address=" + from + "&tx=" + JSON.stringify(tx) + "&signedTx=" + JSON.stringify(signedTx));
            }, (e) => {
                console.log(e)
            });
        }, (e) => {
            console.log(e)
        });
    }
}