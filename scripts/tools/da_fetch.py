import os
import sys
import json
import time
import requests
from web3 import Web3
from dotenv import load_dotenv

# Reuse the flow's epoch constants logic (copied locally to avoid importing main script)
VOTING_EPOCH_DURATION_SECONDS = 90
FIRST_VOTING_ROUND_START_TS = 1658429073

def compute_voting_round_id(block_timestamp: int) -> int:
    return (block_timestamp - FIRST_VOTING_ROUND_START_TS) // VOTING_EPOCH_DURATION_SECONDS

def rpc_call(url, method, params):
    try:
        resp = requests.post(url, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }, timeout=30)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def extract_request_bytes_from_tx(rpc_url: str, tx_hash: str) -> str:
    """Decode the abiEncodedRequest (bytes) from the transaction input of requestAttestation(bytes)."""
    tx = rpc_call(rpc_url, "eth_getTransactionByHash", [tx_hash])
    result = tx.get("result") or {}
    inp = result.get("input")
    if not inp or not inp.startswith("0x"):
        raise RuntimeError("tx input not available for decoding")
    # Strip selector (first 4 bytes -> 8 hex chars)
    data = inp[2:]
    if len(data) < 8 + 64 + 64:
        raise RuntimeError("tx input too short")
    data = data[8:]
    # Next 32 bytes is offset, next 32 bytes is length
    offset_hex = data[:64]
    length_hex = data[64:128]
    try:
        length = int(length_hex, 16)
    except Exception:
        raise RuntimeError(f"invalid length in tx input: {length_hex}")
    # Bytes content starts after those 64+64 = 128 hex chars
    bytes_hex = data[128:128 + length * 2]
    if len(bytes_hex) < length * 2:
        raise RuntimeError("tx input bytes content truncated")
    return "0x" + bytes_hex

def prepare_request(verifier_base: str, api_key: str, tx_hash: str):
    body = {
        "attestationType": "0x45564d5472616e73616374696f6e000000000000000000000000000000000000",  # pad32("EVMTransaction")
        "sourceId":        "0x7465737445544800000000000000000000000000000000000000000000000000",  # pad32("testETH")
        "requestBody": {
            "transactionHash": tx_hash,
            "requiredConfirmations": "1",
            "provideInput": True,
            "listEvents": True,
            "logIndices": []
        }
    }
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    url = f"{verifier_base}/verifier/eth/EVMTransaction/prepareRequest"
    r = requests.post(url, headers=headers, json=body, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"prepareRequest HTTP {r.status_code}: {r.text}")
    data = r.json()
    if "abiEncodedRequest" not in data:
        raise RuntimeError(f"prepareRequest missing abiEncodedRequest: {data}")
    return data["abiEncodedRequest"]

def fetch_da(da_api: str, voting_round_id: int, abi_encoded_request: str):
    """Primary: v1 raw endpoint."""
    payload = {
        "votingRoundId": int(voting_round_id),
        "requestBytes": abi_encoded_request if abi_encoded_request.startswith("0x") else "0x" + abi_encoded_request
    }
    url = f"{da_api}/api/v1/fdc/proof-by-request-round-raw"
    r = requests.post(url, json=payload, timeout=30)
    return r.status_code, r.text

def fetch_da_v0(da_api: str, voting_round_id: int, abi_encoded_request: str):
    """Fallback: v0 endpoint from Getting Started."""
    payload = {
        "votingRoundId": int(voting_round_id),
        "requestBytes": abi_encoded_request if abi_encoded_request.startswith("0x") else "0x" + abi_encoded_request
    }
    url = f"{da_api}/api/v0/fdc/get-proof-round-id-bytes"
    r = requests.post(url, json=payload, timeout=30)
    return r.status_code, r.text

def try_da_with_round_window(da_api: str, base_round: int, abi_encoded_request: str, window: int = 10, backoff_sec: float = 1.0):
    """Try DA fetch starting at base_round and scanning forward up to +window; for each round try v1 raw, then v0."""
    attempts = []
    for offset in range(0, window + 1):
        rid = base_round + offset
        if rid < 0:
            continue
        # v1 raw
        code, text = fetch_da(da_api, rid, abi_encoded_request)
        attempts.append((rid, "v1", code, text))
        if code == 200:
            return rid, code, text, attempts
        # v0 fallback
        code0, text0 = fetch_da_v0(da_api, rid, abi_encoded_request)
        attempts.append((rid, "v0", code0, text0))
        if code0 == 200:
            return rid, code0, text0, attempts
        time.sleep(backoff_sec)
    return None, None, None, attempts

# ---- Systems Manager round resolution via Contract Registry ----
REGISTRY_ABI = [
    {
        "inputs":[{"internalType":"string","name":"name","type":"string"}],
        "name":"getContractAddressByName",
        "outputs":[{"internalType":"address","name":"","type":"address"}],
        "stateMutability":"view","type":"function"
    }
]
# Try multiple plausible names per docs/guides
SYSTEMS_MANAGER_NAMES = ["FlareSystemsManager", "SystemsManager", "FdcSystemsManager"]

# Minimal ABIs to try
FSM_ABI_VARIANTS = [
    # Variant A: getters for first/round duration
    [
        {"name":"firstVotingRoundStartTs","inputs":[],"outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
        {"name":"roundDurationSec","inputs":[],"outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    ],
    # Variant B: get-prefixed
    [
        {"name":"getFirstVotingRoundStartTs","inputs":[],"outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
        {"name":"getRoundDurationSec","inputs":[],"outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    ],
    # Variant C: direct current round
    [
        {"name":"getCurrentVotingEpochId","inputs":[],"outputs":[{"type":"uint32"}],"stateMutability":"view","type":"function"},
    ]
]

def resolve_systems_manager(w3: Web3, registry_addr: str) -> str | None:
    reg = w3.eth.contract(address=w3.to_checksum_address(registry_addr), abi=REGISTRY_ABI)
    for name in SYSTEMS_MANAGER_NAMES:
        try:
            addr = reg.functions.getContractAddressByName(name).call()
            if int(addr, 16) != 0:
                return w3.to_checksum_address(addr)
        except Exception:
            continue
    return None

def read_round_params_or_current(w3: Web3, fsm_addr: str) -> dict:
    """Try to read (first, duration), else current round, from Systems Manager."""
    # Try A
    try:
        c = w3.eth.contract(address=fsm_addr, abi=FSM_ABI_VARIANTS[0])
        first = int(c.functions.firstVotingRoundStartTs().call())
        dur = int(c.functions.roundDurationSec().call())
        if first > 0 and dur > 0:
            return {"first": first, "duration": dur}
    except Exception:
        pass
    # Try B
    try:
        c = w3.eth.contract(address=fsm_addr, abi=FSM_ABI_VARIANTS[1])
        first = int(c.functions.getFirstVotingRoundStartTs().call())
        dur = int(c.functions.getRoundDurationSec().call())
        if first > 0 and dur > 0:
            return {"first": first, "duration": dur}
    except Exception:
        pass
    # Try C: current round only
    try:
        c = w3.eth.contract(address=fsm_addr, abi=FSM_ABI_VARIANTS[2])
        cur = int(c.functions.getCurrentVotingEpochId().call())
        return {"current": cur}
    except Exception:
        pass
    return {}

def compute_base_round_from_systems_manager(w3: Web3, registry_addr: str, block_ts: int) -> tuple[int | None, dict]:
    fsm = resolve_systems_manager(w3, registry_addr)
    if not fsm:
        return None, {"error": "SystemsManager not found in registry"}
    info = read_round_params_or_current(w3, fsm)
    if "first" in info and "duration" in info:
        base = max(0, (block_ts - info["first"]) // info["duration"])
        return int(base), {"fsm": fsm, **info}
    if "current" in info:
        return int(info["current"]), {"fsm": fsm, **info}
    return None, {"fsm": fsm, "error": "Unable to read round params or current round"}

def main():
    load_dotenv()
    if len(sys.argv) < 2:
        print("Usage: python scripts/tools/da_fetch.py 0x<tx_hash>")
        sys.exit(1)

    tx_hash = sys.argv[1]
    rpc_url = os.getenv("RPC_URL") or "https://coston2-api.flare.network/ext/C/rpc"
    verifier_base = os.getenv("VERIFIER_EVM_BASE") or "https://fdc-verifiers-testnet.flare.network"
    da_api = os.getenv("DA_LAYER_API") or "https://ctn2-data-availability.flare.network"
    api_key = os.getenv("FDC_API_KEY") or "00000000-0000-0000-0000-000000000000"

    print(f"== DA fetch helper ==")
    print(f"tx: {tx_hash}")
    print(f"rpc: {rpc_url}")
    print(f"verifier: {verifier_base}")
    print(f"da: {da_api}")

    # 1) Get receipt and block timestamp
    print("\n--- eth_getTransactionReceipt ---")
    rec = rpc_call(rpc_url, "eth_getTransactionReceipt", [tx_hash])
    print(json.dumps(rec, indent=2))

    result = rec.get("result") or {}
    status_hex = result.get("status")
    block_num_hex = result.get("blockNumber")
    if not block_num_hex:
        print("\nNo blockNumber in receipt (tx pending?). Exiting.")
        sys.exit(2)

    # 2) Get block to fetch timestamp
    print("\n--- eth_getBlockByNumber ---")
    block = rpc_call(rpc_url, "eth_getBlockByNumber", [block_num_hex, False])
    print(json.dumps(block, indent=2))

    ts_hex = (block.get("result") or {}).get("timestamp")
    if not ts_hex:
        print("\nNo timestamp in block. Exiting.")
        sys.exit(3)

    block_ts = int(ts_hex, 16)
    print(f"\nblockNumber: {int(block_num_hex, 16)}  timestamp: {block_ts}  status: {status_hex}")

    # 3) Obtain abiEncodedRequest deterministically for same tx
    # Try verifier first; if it returns non-standard body (e.g., {"status":"INVALID"}),
    # fall back to decoding the tx input which contains the bytes argument.
    abi_req = None
    print("\n--- prepareRequest (verifier) ---")
    try:
        abi_req = prepare_request(verifier_base, api_key, tx_hash)
        print(f"abiEncodedRequest (len={len(abi_req)}): {abi_req[:100]}...")
    except Exception as e:
        print(f"prepareRequest failed or invalid ({e}); falling back to tx input decode")
        abi_req = extract_request_bytes_from_tx(rpc_url, tx_hash)
        print(f"abiEncodedRequest (from tx input) (len={len(abi_req)}): {abi_req[:100]}...")

    # 4) Compute voting round (authoritative via Systems Manager when possible)
    # Registry address is available in the main project .env as FLARE_CONTRACT_REGISTRY; if not set, try the common Coston2 registry.
    registry_addr = os.getenv("FLARE_CONTRACT_REGISTRY") or "0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019"
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        base_round, meta = compute_base_round_from_systems_manager(w3, registry_addr, block_ts)
        if base_round is not None:
            print(f"\nVoting round (from Systems Manager): {base_round}")
            if "first" in meta and "duration" in meta:
                print(f"firstVotingRoundStartTs={meta['first']} roundDurationSec={meta['duration']}")
            else:
                print(f"currentVotingEpochId={meta.get('current')}")
            vr = base_round
        else:
            print(f"\nSystems Manager round unavailable ({meta}); falling back to simplified computation.")
            vr = compute_voting_round_id(block_ts)
            print(f"Voting round (fallback): {vr}")
    except Exception as e:
        print(f"\nSystems Manager lookup failed ({e}); using fallback computation.")
        vr = compute_voting_round_id(block_ts)
        print(f"Voting round (fallback): {vr}")

    # 5) Fetch DA proof (try computed round, then +0..+10 with backoff)
    print("\n--- DA proof-by-request-round (v1 raw, fallback v0; scan +0..+10) ---")
    good_rid, code, text, attempts = try_da_with_round_window(da_api, vr, abi_req, window=10, backoff_sec=1.0)
    if code == 200:
        print(f"SUCCESS at votingRoundId={good_rid}")
        print(f"HTTP {code}\n{text}")
    else:
        print("No proof found within +10 rounds. Attempts summary:")
        for rid, ver, c, t in attempts:
            snippet = t[:120] if isinstance(t, str) else str(t)[:120]
            print(f"  round {rid} ({ver}): HTTP {c} - {snippet}{'...' if len(snippet) == 120 else ''}")
        print("Note: Proofs typically become available 1–3 rounds after submission; retry after a short delay.")
        sys.exit(4)

if __name__ == "__main__":
    main()
