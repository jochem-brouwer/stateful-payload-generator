from eth_account import Account


def build_signed_tx(private_key_hex: str, chain_id: int, nonce: int, tpl: dict) -> str:
    tx = {
        "chainId": chain_id,
        "nonce": nonce,
        "type": 2,
        "maxFeePerGas": int(tpl["max_fee_per_gas"]),
        "maxPriorityFeePerGas": int(tpl["max_priority_fee_per_gas"]),
        "gas": int(tpl["gas"]),
        "to": tpl["to"],
        "value": int(tpl["value"]),
        "data": tpl.get("data", "0x"),
    }
    signed = Account.sign_transaction(tx, private_key_hex)
    raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    return raw.hex() if hasattr(raw, "hex") else raw
