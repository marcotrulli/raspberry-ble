import asyncio
import httpx
from bleak import BleakClient

MAC_ADDRESS = "48:87:2D:6C:FB:0C"
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
SOGLIA_DISTANZA = 40.0
CAMERA_IP = "192.168.1.36"
TIMER_SCATTO = 0.5
PAUSA_SICUREZZA = 3

timer_attivo = False
ultima_distanza = None

async def invia_comando_camera():
    global timer_attivo
    print("📸 TRIGGER! Scatto in corso...")
    url = f"http://{CAMERA_IP}/capture"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                print("✅ Foto scattata!")
            else:
                print(f"⚠️ Risposta ESP: {response.status_code}")
    except Exception as e:
        print(f"❌ Errore rete: {e}")
    await asyncio.sleep(PAUSA_SICUREZZA)
    timer_attivo = False
    print("🔄 Pronto per nuovo rilevamento\n")

async def main():
    global ultima_distanza, timer_attivo
    print(f"🔍 Connessione a {MAC_ADDRESS}...")

    try:
        async with BleakClient(MAC_ADDRESS) as client:
            print("✅ Sensore Pronto.")

            while True:
                try:
                    value = await client.read_gatt_char(CHAR_UUID)
                    text = value.decode().strip()

                    if text == '':
                        await asyncio.sleep(0.1)
                        continue

                    distanza = float(text)
                    print(f"📡 Distanza: {distanza}")

                    if ultima_distanza is not None and not timer_attivo:
                        if ultima_distanza > SOGLIA_DISTANZA and distanza < SOGLIA_DISTANZA:
                            timer_attivo = True
                            asyncio.create_task(invia_comando_camera())

                    ultima_distanza = distanza
                    await asyncio.sleep(0.3)

                except Exception as e:
                    print(f"⚠️ Errore lettura BLE: {e}")
                    await asyncio.sleep(0.3)

    except Exception as e:
        print(f"💥 Errore connessione: {e}")

if __name__ == "__main__":
    asyncio.run(main())
