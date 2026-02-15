import asyncio
import subprocess
import requests
from bleak import BleakClient

# ---------------- CONFIGURAZIONE ----------------
MAC_ADDRESS = "48:87:2D:6C:FB:0C"  # MAC BLE reale
SOGLIA = 40.0
TIMER = 2  # secondi
ESP32_IP = "192.168.1.36"  # IP reale ESP32-CAM

# Stato del timer per evitare scatti multipli
timer_attivo = False

# ---------------- AVVIO BLE_READ IN NUOVO TERMINALE ----------------
print("🚀 Avvio ble_read.py in nuovo terminale...")

# Percorso assoluto al Python del venv
PYTHON_VENV = "/home/pi/raspberry-ble/raspberry-ble/venv/bin/python"

subprocess.Popen([
    "lxterminal",
    "--command",
    f"{PYTHON_VENV} /home/pi/raspberry-ble/raspberry-ble/ble_read.py; exec bash"
])

# ---------------- FUNZIONE PER INVIO FOTO ----------------
async def invia_foto():
    global timer_attivo
    try:
        print(f"📸 Timer di {TIMER}s avviato...")
        await asyncio.sleep(TIMER)
        print("🎯 Inviando comando /capture alla CAM...")
        url = f"http://{ESP32_IP}/capture"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("✅ Foto scattata con successo!")
        else:
            print(f"⚠️ Errore HTTP: {response.status_code}")
    except requests.RequestException as e:
        print(f"⚠️ Errore connessione ESP32: {e}")
    finally:
        timer_attivo = False  # Reset timer

# ---------------- FUNZIONE DI CALLBACK BLE ----------------
def notification_handler(sender, data):
    global timer_attivo
    try:
        distanza = float(data.decode().strip())
        print(f"Distanza letta: {distanza}")
        if distanza < SOGLIA and not timer_attivo:
            timer_attivo = True
            asyncio.create_task(invia_foto())
    except ValueError:
        print(f"Dato ricevuto non valido: {data}")

# ---------------- LOOP PRINCIPALE ----------------
async def main():
    print(f"🔎 Connessione al dispositivo BLE {MAC_ADDRESS}...")
    async with BleakClient(MAC_ADDRESS) as client:
        print("✔️ Connesso al BLE!")
        # Handle BLE reale dal tuo dispositivo (assicurati sia corretto)
        HANDLE = 0x0025  
        await client.start_notify(HANDLE, notification_handler)
        print("🎯 In ascolto dei valori BLE...")
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            await client.stop_notify(HANDLE)
            print("⛔ Interrotto")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Script principale interrotto")
