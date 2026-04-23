import time
from typing import Any

import jwt
import requests


class RpcClient:
    def __init__(self, url: str, jwt_secret_hex: str | None = None):
        self.url = url
        self.jwt_secret: bytes | None = (
            bytes.fromhex(jwt_secret_hex.removeprefix("0x")) if jwt_secret_hex else None
        )
        self._id = 0

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.jwt_secret:
            token = jwt.encode({"iat": int(time.time())}, self.jwt_secret, algorithm="HS256")
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def call(self, method: str, params: list):
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params,
        }
        return self.send(request)

    def send(self, request: dict):
        response = requests.post(self.url, json=request, headers=self._headers(), timeout=60)
        response.raise_for_status()
        data = response.json()
        if "error" in data and data["error"] is not None:
            raise RuntimeError(f"RPC error from {request['method']}: {data['error']}")
        return data.get("result")


class EngineClient(RpcClient):
    def send_raw_tx(self, raw_hex: str):
        if not raw_hex.startswith("0x"):
            raw_hex = "0x" + raw_hex
        return self.call("eth_sendRawTransaction", [raw_hex])

    def build_block(self, attrs: dict) -> dict:
        return self.call("testing_buildBlockV1", [attrs])

    def new_payload_request(
        self,
        payload: dict,
        version: str,
        parent_beacon_block_root: str,
        expected_blob_versioned_hashes: list,
    ) -> dict:
        params: list[Any]
        if version in ("V1", "V2"):
            params = [payload]
        elif version == "V3":
            params = [payload, expected_blob_versioned_hashes, parent_beacon_block_root]
        elif version in ("V4", "V5"):
            execution_requests = payload.pop("executionRequests", [])
            params = [
                payload,
                expected_blob_versioned_hashes,
                parent_beacon_block_root,
                execution_requests,
            ]
        else:
            raise ValueError(f"Unknown engine version: {version}")

        return {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": f"engine_newPayload{version}",
            "params": params,
        }

    def fcu_request(self, forkchoice_state: dict, version: str) -> dict:
        return {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": f"engine_forkchoiceUpdated{version}",
            "params": [forkchoice_state, None],
        }
