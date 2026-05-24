#!/usr/bin/env python3
"""
GrünBECK Realtime Monitor - 10s UPDATES
✅ Continuous table output
✅ 10-second polling interval
"""

import asyncio
from datetime import datetime
from pygruenbeck_cloud import PyGruenbeckCloud

USERNAME = "YOUR_EMAIL"
PASSWORD = "YOUR_PASSWORD"
DEVICE_ID = "softliQ.SE/YOUR_SERIAL_NUMBER"

TRACKED_FIELDS = [
    'mrescapa1', 'mresidcap1', 'mflow1', 'mregstatus', 
    'msaltrange', 'msaltusage', 'mcountwater1', 'mlime', 'mcountreg'
]

async def realtime_sequence(gb, token):
    """5-step sequence for data polling"""
    BASE_URL = "https://prod-eu-gruenbeck-api.azurewebsites.net/api/devices"
    API_VERSION = "2024-05-02"
    url_base = f"{BASE_URL}/{DEVICE_ID}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "pygruenbeck_cloud",
        "Accept": "application/json",
    }
    
    steps = [
        ("POST", "/realtime/refresh"),
        ("POST", "/realtime/enter"),
        ("GET",  "/update"),
        ("POST", "/realtime/leave"),
        ("POST", "/realtime/off")
    ]
    
    update_data = None
    for method, endpoint in steps:
        url = f"{url_base}{endpoint}?api-version={API_VERSION}"
        try:
            if method == "GET":
                async with gb.session.get(url, headers=headers) as resp:
                    if endpoint == "/update":
                        update_data = await resp.json()
            else:
                async with gb.session.post(url, headers=headers, json={}) as resp:
                    pass
        except:
            pass
    
    return update_data

def print_header():
    """Prints a clear table header"""
    header = f"{'CYCLE':<10} {'TIMESTAMP':<12} | " + " | ".join([f"{f[:10]:<10}" for f in TRACKED_FIELDS])
    print(header)
    print("-" * len(header))

def print_tracked_values(data, cycle):
    """Prints values on a new line with high-precision water meter readings"""
    ts = datetime.now().strftime("%H:%M:%S")
    
    # Adjusted spacing to account for the wider mcountwater1 field
    row_start = f"{cycle:<8} {ts:<10} | "
    
    values = []
    for field in TRACKED_FIELDS:
        val = data.get(field, "N/A")
        try:
            if field == 'mrescapa1':
                val = f"{float(val):>7.0f}L"
            elif field == 'mcountwater1':
                # Increased to 3 decimal places
                val = f"{float(val):>9.3f}m³" 
            elif field == 'msaltusage':
                val = f"{float(val):>7.1f}kg"
            elif field == 'mlime':
                val = f"{float(val):>7.0f}kg"
            else:
                val = str(val)[:10].center(10)
        except (ValueError, TypeError):
            val = str(val)[:10].center(10)
        values.append(val)
 
    # Print as a new line
    print(row_start + " | ".join(values))

async def main():
    print(f"🚀 Starting Monitor - Polling every 10 seconds")
    gb = PyGruenbeckCloud(USERNAME, PASSWORD)
    
    try:
        await gb.login()
        token = gb._auth_token.access_token
        
        print_header()
        cycle = 0
        while True:
            cycle += 1
            update_data = await realtime_sequence(gb, token)
            
            if update_data:
                print_tracked_values(update_data, cycle)
            
            await asyncio.sleep(10)  # CHANGED TO 10 SECONDS
            
    except KeyboardInterrupt:
        print("\n👋 Stopped by user")
    finally:
        await gb.close()

if __name__ == "__main__":
    asyncio.run(main())
