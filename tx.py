from eth_account import Account
from eth_utils import to_checksum_address

CREATE2_DEPLOYER_ADDRESS = "0x4e59b44847b379578588920cA78FbF26c0B4956C"
CREATE2_DEPLOYER_GAS = 16777216


def _resolve_tx_fields(tpl: dict, tx_index: int) -> tuple[str, int, str]:
    template_type = tpl.get("type", "static")
    if template_type == "static":
        return to_checksum_address(tpl["to"]), int(tpl["gas"]), tpl.get("data", "0x")
    if template_type == "create2_deployer":
        salt = int(tpl["start_salt"]) + tx_index
        initcode_hex = tpl["initcode"]
        if initcode_hex.startswith("0x"):
            initcode_hex = initcode_hex[2:]
        data = "0x" + salt.to_bytes(32, "big").hex() + initcode_hex
        return to_checksum_address(CREATE2_DEPLOYER_ADDRESS), CREATE2_DEPLOYER_GAS, data
    raise ValueError(f"Unknown tx template type: {template_type}")


def build_signed_tx(
    private_key_hex: str,
    chain_id: int,
    nonce: int,
    tpl: dict,
    tx_index: int = 0,
) -> str:
    to, gas, data = _resolve_tx_fields(tpl, tx_index)
    tx = {
        "chainId": chain_id,
        "nonce": nonce,
        "type": 2,
        "maxFeePerGas": int(tpl["max_fee_per_gas"]),
        "maxPriorityFeePerGas": int(tpl["max_priority_fee_per_gas"]),
        "gas": gas,
        "to": to,
        "value": int(tpl["value"]),
        "data": data,
    }
    signed = Account.sign_transaction(tx, private_key_hex)
    raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    raw_hex = raw.hex() if hasattr(raw, "hex") else raw
    return raw_hex if raw_hex.startswith("0x") else "0x" + raw_hex
