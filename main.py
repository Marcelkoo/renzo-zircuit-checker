import aiohttp
import json
import asyncio
from beautifultable import BeautifulTable
import random

async def fetch_zircuit(session, wallet, proxy):
    url = f"https://claim.zircuit.com/api/claim/{wallet}"
    async with session.get(url, proxy=proxy) as response:
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = await response.json()
            claimable_amount = int(data.get("claimableAmount", 0)) / 1e18
            print(f"Zircuit: Wallet: {wallet}, Response: {data}, Claimable Amount: {claimable_amount}")
            return wallet, claimable_amount
        else:
            text = await response.text()
            print(f"Zircuit: Wallet: {wallet}, Unexpected Content-Type: {content_type}, Response: {text}")
            return wallet, 0

async def fetch_renzo(session, wallet, proxy):
    url = f"https://claim.renzoprotocol.com/api/eligibility-checker/{wallet}"
    async with session.get(url, proxy=proxy) as response:
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = await response.json()
            if "data" in data:
                eligible_data = data["data"]
                print(f"Renzo: Wallet: {wallet}, Response: {data}, RezTokens: {eligible_data.get('rezTokens', 0)}")
                return wallet, eligible_data.get("rezTokens", 0)
            else:
                print(f"Renzo: Wallet: {wallet}, No data in Response: {data}")
                return wallet, 0
        else:
            text = await response.text()
            print(f"Renzo: Wallet: {wallet}, Unexpected Content-Type: {content_type}, Response: {text}")
            return wallet, 0

async def fetch_wallet_data(wallet, proxies):
    proxy = random.choice(proxies)
    async with aiohttp.ClientSession() as session:
        zircuit_task = fetch_zircuit(session, wallet, f"http://{proxy}")
        renzo_task = fetch_renzo(session, wallet, f"http://{proxy}")
        zircuit_result, renzo_result = await asyncio.gather(zircuit_task, renzo_task)
        return wallet, zircuit_result[1], renzo_result[1]

async def main():
    with open("proxy.txt") as f:
        proxies = [line.strip() for line in f]

    with open("wallets.txt") as f:
        wallets = [line.strip() for line in f]

    tasks = [fetch_wallet_data(wallet, proxies) for wallet in wallets]
    
    results = await asyncio.gather(*tasks)

    table = BeautifulTable()
    table.columns.header = ["Wallet", "Zircuit", "Renzo"]

    for wallet, zircuit, renzo in results:
        table.rows.append([wallet, zircuit, renzo])

    print(table)

if __name__ == "__main__":
    asyncio.run(main())
