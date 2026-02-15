import asyncio
from bleak import BleakClient

MAC_ADDRESS = "48:87:2D:6C:FB:0C"
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

def handle_data(sender, data):
    try:
        print("Distanza:", data.decode().strip())
    except:
        print("Dato ricevuto:", data)

async def main():
    print("Connessione in corso...")
    async with BleakClient(MAC_ADDRESS) as client:
        print("Connesso al DX-BT24!")
        await client.start_notify(CHAR_UUID, handle_data)

        while True:
            await asyncio.sleep(1)

asyncio.run(main())
