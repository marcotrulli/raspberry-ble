import subprocess
import asyncio
import requests
from bleak import BleakClient
from threading import Timer

# ---------- CONFIG ----------
MAC_ADDRESS = "48:87:2D:6C:FB:0C"
BLE_CHAR = "0000ffe1-0000-1000-8000-00805f9b34fb"
CAM_IP = "192.168.1.36"
SOGLIA = 40.0
TIMER_DELAY = 2  # secondi

timer_attivo = False

# ---------- FUNZIONI CAM ----------
def scatta_foto():
    """Invia richiesta /capture alla cam e salva foto."""
    try:
        r = requests.get(f"http://{CAM_IP}/capture", timeout=10)
        if r.status_code == 200:
            with open("ultima_foto.jpg", "wb") as f:
                f.write(r.content)
            print("🎉 Foto scattata!")
        else:
            print("Errore HTTP cam:", r.status_code)
    except requests.exceptions.RequestException as e:
        print("Errore richiesta ESP32:", e)

def mostra_ultima_foto():
    """Richiama /last per mostrare ultima foto."""
    try:
        r = requests.get(f"http://{CAM_IP}/last", timeout=10)
        if r.status_code == 200:
            with open("ultima_foto_last.jpg", "wb") as f:
                f.write(r.content)
            print("🖼️ Ultima foto aggiornata")
        else:
            print("Errore HTTP /last:", r.status_code)
    except requests.exceptions.RequestException as e:
        print("Errore richiesta /last:", e)

# ---------- TIMER ----------
def start_timer():
    global timer_attivo
    if not timer_attivo:
        timer_attivo = True
        t = Timer(TIMER_DELAY, timer_callback)
        t.start()
        print(f"⚠️ Soglia raggiunta, timer {TIMER_DELAY}s avviato...")

def timer_callback():
    global timer_attivo
    scatta_foto()
    timer_attivo = False

# ---------- BLE ----------
async def leggi_distanza_ble(client):
    """Legge il valore BLE e ritorna distanza float."""
    try:
        data = await client.read_gatt_char(BLE_CHAR)
        value_str = data.decode().strip()
        distanza = float(value_str)
        return distanza
    except Exception:
        return None

# ---------- MAIN ----------
async def main():
    # Avvio ble_read.py in nuovo terminale
    print("🚀 Avvio ble_read.py in nuovo terminale...")
    subprocess.Popen(["lxterminal", "-e", "python3 ble_read.py"])

    print(f"🔌 Connessione al dispositivo BLE {MAC_ADDRESS}...")
    async with BleakClient(MAC_ADDRESS) as client:
        if not client.is_connected:
            print("❌ Connessione BLE fallita!")
            return
        print("✅ Connesso al BLE!")
        print("🎯 In ascolto dei valori BLE...")

        while True:
            distanza = await leggi_distanza_ble(client)
            if distanza is not None:
                print(f"Distanza letta: {distanza}")
                if distanza < SOGLIA:
                    start_timer()
            await asyncio.sleep(0.5)

# ---------- AVVIO ----------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript CAM interrotto")
