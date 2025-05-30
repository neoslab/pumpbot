import requests

def get_solana_balance(wallet_address, rpc_url="https://api.mainnet-beta.solana.com"):
    headers = {"Content-Type": "application/json"}
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [wallet_address]
    }

    try:
        response = requests.post(rpc_url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json().get("result", {})
        lamports = result.get("value", 0)
        sol = lamports / 1_000_000_000  # Convert lamports to SOL
        return sol
    except Exception as e:
        print(f"Error fetching balance: {e}")
        return None

def extractholders_tested(token_address):
    url = f"https://frontend-api-v3.pump.fun/coins/top-holders/{token_address}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
    }
    try:
        r = requests.get(url, timeout=5, headers=headers)
        r.raise_for_status()
        wallets = r.json()
        holders = wallets.get("topHolders", {}).get("value", [])
        if holders:
            return [entry["address"] for entry in holders if "address" in entry]
        return []
    except Exception as e:
        print("!!! TESTED FUNCTION ERROR:", e)
        return []

if __name__ == "__main__":
    holders = extractholders_tested("7LF9jowq86mreygJrVpeCtxBAdShZzbkweEXkhC3pump")
    for wallet in enumerate(holders, start=1):
        balance = get_solana_balance("7LF9jowq86mreygJrVpeCtxBAdShZzbkweEXkhC3pump")
        print(f"{wallet}: {balance}")