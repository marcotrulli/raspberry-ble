import asyncio
import httpx
from bleak import BleakClient

# ---------- CONFIGURAZIONE ----------
MAC_ADDRESS = "48:87:2D:6C:FB:0C"  # MAC BLE DX-BT24
CHAR_UUID_TX = "0000ffe1-0000-1000-8000-00805f9b34fb"  # UUID corretto TX
SOGLIA = 40.0
CAMERA_IP = "192.168.1.36"  # IP ESP32-CAM

ultima_distanza = None
timer_attivo = False

async def invia_comando_camera():
    global timer_attivo
    print(f"📸 TRIGGER! Scatto in corso...")

    url = f"http://{CAMERA_IP}/capture"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                print("✅ Foto scattata correttamente")
            else:
                print(f"⚠️ Problema ESP32-CAM: {response.status_code}")
    except Exception as e:
        print(f"❌ Errore rete: {e}")

    await asyncio.sleep(3)  # pausa sicurezza
    timer_attivo = False

def clean_float(data):
    try:
        text = data.decode("utf-8").strip()
        return float(text)
    except Exception:
        return None

def notification_handler(sender, data):
    global ultima_distanza, timer_attivo
    distanza = clean_float(data)
    if distanza is None:
        print("Dato BLE non valido:", data)
        return

    print("Distanza ricevuta:", distanza)

    # Trigger solo se passa sopra->sotto soglia
    if ultima_distanza is not None and not timer_attivo:
        if ultima_distanza > SOGLIA and distanza < SOGLIA:
            timer_attivo = True
            asyncio.create_task(invia_comando_camera())

    ultima_distanza = distanza

async def main():
    print(f"🔍 Connessione a {MAC_ADDRESS}...")
    try:
        async with BleakClient(MAC_ADDRESS) as client:
            print("✅ Connesso al sensore BLE.")
            await client.start_notify(CHAR_UUID_TX, notification_handler)
            while True:
                await asyncio.sleep(1)
    except Exception as e:
        print(f"💥 Errore connessione BLE: {e}")

if __name__ == "__main__":
    asyncio.run(main())
