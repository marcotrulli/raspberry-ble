import asyncio
import subprocess
import requests
from bleak import BleakClient

# ---------- CONFIGURAZIONE DISPOSITIVI ----------
MAC_ADDRESS = "48:87:2D:6C:FB:0C"                     # MAC BLE reale
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"    # UUID corretto
SOG_LIA = 40.0                                        # soglia distanza
CAMERA_IP = "192.168.1.36"                            # IP reale ESP32-CAM
TIMER = 2                                             # secondi di attesa prima dello scatto

# ---------- VARIABILI GLOBALI ----------
timer_attivo = False

# ---------- FUNZIONE NOTIFICA BLE ----------
def notification_handler(sender, data):
    global timer_attivo
    try:
        distanza = float(data.decode().strip())
        print(f"Distanza letta: {distanza}")
    except Exception:
        print(f"Dato BLE non valido: {data}")
        return

    if distanza < SOG_LIA and not timer_attivo:
        print(f"⚠️ Soglia {SOG_LIA} superata, timer di {TIMER}s avviato...")
        timer_attivo = True
        asyncio.create_task(invia_comando_camera())

# ---------- FUNZIONE PER INVIARE COMANDO ALLA CAMERA ----------
async def invia_comando_camera():
    global timer_attivo
    await asyncio.sleep(TIMER)
    try:
        response = requests.get(f"http://{CAMERA_IP}/capture", timeout=5)
        if response.status_code == 200:
            print("📸 Foto scattata con successo!")
        else:
            print(f"⚠️ Errore HTTP: {response.status_code}")
    except requests.RequestException as e:
        print(f"⚠️ Errore connessione ESP32-CAM: {e}")
    timer_attivo = False

# ---------- MAIN ASYNC ----------
async def main():
    # Avvio ble_read.py in un nuovo terminale con venv
    print("🚀 Avvio ble_read.py in nuovo terminale...")
    subprocess.Popen([
        "lxterminal", "-e",
        f"bash -c 'source /home/pi/raspberry-ble/raspberry-ble/venv/bin/activate; python3 /home/pi/raspberry-ble/raspberry-ble/ble_read.py; exec bash'"
    ])

    # Connessione al BLE
    print(f"🔌 Connessione al dispositivo BLE {MAC_ADDRESS}...")
    async with BleakClient(MAC_ADDRESS) as client:
        if await client.is_connected():
            print("✅ Connesso al BLE!")
        else:
            print("❌ Connessione fallita!")
            return

        print("🎧 In ascolto dei valori BLE...")
        await client.start_notify(CHAR_UUID, notification_handler)

        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            print("🛑 Script principale interrotto")
            await client.stop_notify(CHAR_UUID)

# ---------- AVVIO SCRIPT ----------
if __name__ == "__main__":
    asyncio.run(main())
