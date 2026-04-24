import argparse
import json
from pathlib import Path

from eth_account import Account

from rpc import EngineClient
from tx import build_signed_tx


def load_config(path: str) -> dict:
    return json.loads(Path(path).read_text())


def run(cfg: dict) -> None:
    client = EngineClient(
        eth_url=cfg["eth_rpc_url"],
        engine_url=cfg["engine_rpc_url"],
        jwt_secret_hex=cfg.get("jwt_secret_hex"),
    )

    output_path = Path(cfg["output_file"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    head_hash = cfg["initial_block_hash"]
    safe_hash = cfg["initial_block_hash"]
    finalized_hash = cfg["initial_block_hash"]

    new_payload_version = cfg.get("engine_new_payload_version", "V5")
    fcu_version = cfg.get("engine_fcu_version", "V3")
    chain_id = int(cfg["chain_id"])
    private_key = cfg["private_key_hex"]
    tx_tpl = cfg["tx_template"]
    parent_beacon_block_root = cfg.get(
        "parent_beacon_block_root",
        "0x" + "00" * 32,
    )

    sender_address = Account.from_key(private_key).address
    head_block = client.call("eth_getBlockByHash", [head_hash, False])
    if head_block is None:
        raise RuntimeError(f"Head block {head_hash} not found")
    timestamp = int(head_block["timestamp"], 16)
    nonce = int(client.call("eth_getTransactionCount", [sender_address, head_hash]), 16)

    with output_path.open("a") as out_f:
        for i in range(int(cfg["num_blocks"])):
            timestamp += 1
            raw_txs = []
            for _ in range(int(cfg["txs_per_block"])):
                raw_txs.append(build_signed_tx(private_key, chain_id, nonce, tx_tpl))
                nonce += 1

            for raw in raw_txs:
                client.send_raw_tx(raw)

            attrs = {
                "parentHash": head_hash,
                "timestamp": hex(timestamp),
                "feeRecipient": cfg["fee_recipient"],
                "prevRandao": cfg["prev_randao"],
                "withdrawals": cfg.get("withdrawals", []),
                "parentBeaconBlockRoot": parent_beacon_block_root,
            }
            payload = client.build_block(attrs)
            if payload is None:
                raise RuntimeError("testing_buildBlockV1 returned null")

            new_payload_req = client.new_payload_request(
                payload,
                new_payload_version,
                parent_beacon_block_root,
                [],
            )
            out_f.write(json.dumps(new_payload_req) + "\n")
            out_f.flush()
            client.send(new_payload_req)

            new_head = payload["blockHash"]
            fcu_req = client.fcu_request(
                {
                    "headBlockHash": new_head,
                    "safeBlockHash": safe_hash,
                    "finalizedBlockHash": finalized_hash,
                },
                fcu_version,
            )
            out_f.write(json.dumps(fcu_req) + "\n")
            out_f.flush()
            client.send(fcu_req)

            print(f"[{i + 1}/{cfg['num_blocks']}] head={new_head} ts={timestamp} nonce_next={nonce}")

            head_hash = new_head


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args()
    run(load_config(args.config))


if __name__ == "__main__":
    main()
