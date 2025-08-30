import sys
import json
import requests

RPC_URL = "https://coston2-api.flare.network/ext/C/rpc"

def rpc_call(method, params):
    try:
        resp = requests.post(RPC_URL, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }, timeout=30)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/tools/rpc_check.py 0x<tx_hash>")
        sys.exit(1)
    tx_hash = sys.argv[1]

    print("--- eth_getTransactionByHash ---")
    print(json.dumps(rpc_call("eth_getTransactionByHash", [tx_hash]), indent=2))

    print("--- eth_getTransactionReceipt ---")
    print(json.dumps(rpc_call("eth_getTransactionReceipt", [tx_hash]), indent=2))

if __name__ == "__main__":
    main()
