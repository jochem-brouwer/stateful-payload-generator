To run: pip install -r requirements.txt, copy config.example.json → config.json, fill in rpc_url, jwt_secret_hex, private_key_hex, chain_id, initial_nonce, initial_block_hash, then python main.py.

Two things to verify against your client: 
The exact argument shape of testing_buildBlockV1:
Passing one object with parentHash, timestamp, feeRecipient, prevRandao, withdrawals, parentBeaconBlockRoot; adjust rpc.py:49-50 if yours differs. 
