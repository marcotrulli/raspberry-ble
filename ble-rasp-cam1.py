import asyncio
import subprocess
import requests
from bleak import BleakClient
from datetime import datetime

# ---------------- CONFIGURAZIONE ----------------
MAC_ADDRESS = "48:87:2D:6C:FB:0C"          # MAC del dispositivo BLE
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"  # UUID della caratteristica
SOG_LIA = 40.0                              # soglia distanza per scattare foto
CAMERA_IP = "192.168.1.36"                  # IP della ESP32-CAM
TIMER = 2                                   # secondi di attesa prima dello scatto
BLE_READ_PATH = "/home/pi/raspberry-ble/ble_read.py"  # percorso del secondo script
VENV_PATH = "/home/pi/raspberry-ble/venv/bin/activate"  # percorso virtualenv

# ---------------- VARIABILI GLOBALI ----------------
timer_attivo = False

# ---------------- UTILITY ----------------
def log(msg: str):
    """Log con timestamp sul primo terminale solo per info generali."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# ---------------- COMANDO CAMERA ----------------
async def invia_comando_camera():
    """Invia richiesta HTTP alla ESP32-CAM per scattare la foto."""
    global timer_attivo
    await asyncio.sleep(TIMER)  # attesa prima dello scatto
    try:
        response = requests.get(f"http://{CAMERA_IP}/capture", timeout=15)
        if response.status_code == 200:
            log("📸 Foto scattata con successo!")
        else:
            log(f"⚠️ Errore HTTP dalla camera: {response.status_code}")
    except requests.RequestException as e:
        log(f"⚠️ Errore connessione ESP32-CAM: {e}")
    timer_attivo = False

# ---------------- FUNZIONE NOTIFICA BLE ----------------
def notification_handler(sender, data):
    """
    Gestione dei dati BLE. Non stampa le distanze,
    solo attiva il timer per scattare foto se necessario.
    """
    global timer_attivo
    try:
        distanza = float(data.decode().strip())
    except Exception:
        return

    if distanza < SOG_LIA and not timer_attivo:
        timer_attivo = True
        asyncio.create_task(invia_comando_camera())

# ---------------- AVVIO BLE_READ ----------------
def avvia_ble_read():
    """Avvia ble_read.py in un nuovo terminale con venv."""
    log("🚀 Avvio ble_read.py in nuovo terminale...")
    subprocess.Popen([
        "lxterminal", "-e",
        f"bash -c 'source {VENV_PATH}; python3 {BLE_READ_PATH}; exec bash'"
    ])

# ---------------- MAIN ASYNC ----------------
async def main():
    # Avvio secondo terminale per le distanze
    avvia_ble_read()

    log(f"🔌 Connessione al dispositivo BLE {MAC_ADDRESS}...")
    try:
        async with BleakClient(MAC_ADDRESS) as client:
            if client.is_connected:
                log("✅ Connesso al BLE!")
            else:
                log("❌ Connessione fallita!")
                return

            log("🎧 In ascolto dei valori BLE...")
            await client.start_notify(CHAR_UUID, notification_handler)

            # Loop principale
            while True:
                await asyncio.sleep(1)

    except Exception as e:
        log(f"❌ Errore connessione BLE: {e}")

# ---------------- AVVIO SCRIPT ----------------
if __name__ == "__main__":
    asyncio.run(main())
