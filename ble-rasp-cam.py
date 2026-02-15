import asyncio
import subprocess
import requests
import time
from bleak import BleakClient

# ---------- CONFIG BLE ----------
MAC_ADDRESS = "48:87:2D:6C:FB:0C"
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
SOG_LIA = 40.0  # soglia distanza
CAMERA_IP = "192.168.1.XXX"  # sostituisci con IP reale ESP32-CAM

# ---------- VARIABILI GLOBALI ----------
timer_attivo = False

# ---------- FUNZIONE NOTIFICA BLE ----------
def notification_handler(sender, data):
    global timer_attivo
    try:
        distanza = float(data.decode().strip())
        print(f"Distanza letta: {distanza}")
    except Exception as e:
        print(f"Dato ricevuto non valido: {data} {e}")
        return

    if distanza < SOG_LIA and not timer_attivo:
        print(f"⚠️ Soglia {SOG_LIA} raggiunta, timer di 2s avviato...")
        timer_attivo = True
        asyncio.create_task(invia_comando_camera())

# ---------- FUNZIONE PER INVIARE COMANDO ALLA CAMERA ----------
async def invia_comando_camera():
    global timer_attivo
    await asyncio.sleep(2)  # timer 2 secondi
    try:
        r = requests.get(f"http://{CAMERA_IP}/capture", timeout=5)
        if r.status_code == 200:
            print("📸 Foto scattata con successo!")
        else:
            print(f"Errore HTTP: {r.status_code}")
    except Exception as e:
        print(f"Errore richiesta camera: {e}")
    timer_attivo = False

# ---------- MAIN ASYNC ----------
async def main():
    # Avvio ble_read.py in nuovo terminale con venv
    print("🚀 Avvio ble_read.py in nuovo terminale...")
    subprocess.Popen([
        "lxterminal", "-e",
        f"bash -c 'source {subprocess.os.getcwd()}/venv/bin/activate; python3 ble_read.py; exec bash'"
    ])

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
            print("Script principale interrotto")
            await client.stop_notify(CHAR_UUID)

# ---------- AVVIO ----------
if __name__ == "__main__":
    asyncio.run(main())
