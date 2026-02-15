import asyncio
import httpx
from bleak import BleakClient

# ---------- CONFIGURAZIONE ----------
MAC_ADDRESS = "48:87:2D:6C:FB:0C"      # MAC BLE del sensore
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb" # UUID Caratteristica
SOGLIA_DISTANZA = 40.0                # Soglia in cm
CAMERA_IP = "192.168.1.36"            # IP della tua ESP32-CAM
TIMER_SCATTO = 2                      # Ritardo prima dello scatto

# ---------- STATO ----------
timer_attivo = False
ultima_distanza = None

async def invia_comando_camera():
    global timer_attivo
    print(f"⏳ Timer attivo: scatto tra {TIMER_SCATTO}s...")
    await asyncio.sleep(TIMER_SCATTO)

    url = f"http://{CAMERA_IP}/capture"
    try:
        # follow_redirects=False evita di scaricare l'HTML inutilmente
        async with httpx.AsyncClient(follow_redirects=False) as client:
            print("📸 Scatto in corso...")
            response = await client.get(url, timeout=5.0)
            if response.status_code in [200, 303]:
                print("✅ Foto aggiornata con successo!")
            else:
                print(f"⚠️ Risposta inattesa: {response.status_code}")
    except Exception as e:
        print(f"❌ Errore connessione ESP32: {e}")

    timer_attivo = False
    print("🔄 Pronto per nuovo rilevamento.")

def notification_handler(sender, data):
    global timer_attivo, ultima_distanza
    try:
        distanza = float(data.decode().strip())
        print(f"📡 Distanza: {distanza} cm")

        if ultima_distanza is not None:
            # Rileva quando l'oggetto ENTRA nella soglia (Fronte di discesa)
            if ultima_distanza > SOGLIA_DISTANZA and distanza < SOGLIA_DISTANZA and not timer_attivo:
                print(f"🚨 TARGET RILEVATO!")
                timer_attivo = True
                asyncio.create_task(invia_comando_camera())

        ultima_distanza = distanza
    except:
        pass

async def main():
    print(f"🔍 Connessione al sensore {MAC_ADDRESS}...")
    try:
        async with BleakClient(MAC_ADDRESS) as client:
            if client.is_connected:
                print("✅ BLE Connesso!")
                await client.start_notify(CHAR_UUID, notification_handler)
                while True:
                    await asyncio.sleep(1)
    except Exception as e:
        print(f"💥 Errore: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Sistema arrestato.")
