import asyncio
import requests
from bleak import BleakClient
import subprocess
import os
import sys

# ---------- CONFIGURAZIONE ----------
MAC_ADDRESS = "48:87:2D:6C:FB:0C"
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
ESP32_CAM_IP = "192.168.1.36"
SOGLIA = 40
DELAY = 2

# ---------- VARIABILI GLOBALI ----------
foto_scattata = False
timer_attivo = False
valore_corrente = None

# ---------- FUNZIONE CHE SCATTA FOTO ----------
def scatta_foto():
    global foto_scattata
    try:
        url = f"http://{ESP32_CAM_IP}/capture"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            print("✅ Foto scattata sulla cam!")
            foto_scattata = True
        else:
            print("❌ Errore HTTP:", r.status_code)
    except Exception as e:
        print("❌ Errore richiesta ESP32:", e)

# ---------- TASK ASINCRONO DEL TIMER ----------
async def timer_check():
    global timer_attivo, valore_corrente
    await asyncio.sleep(DELAY)
    if valore_corrente is not None and valore_corrente <= SOGLIA:
        scatta_foto()
    timer_attivo = False

# ---------- CALLBACK BLE ----------
def handle_data(sender, data):
    global foto_scattata, timer_attivo, valore_corrente
    try:
        valore = int(data.decode().strip())
        valore_corrente = valore
        print(f"Distanza letta: {valore}")

        if valore <= SOGLIA:
            if not foto_scattata and not timer_attivo:
                print(f"⚡ Soglia {SOGLIA} raggiunta, timer di {DELAY}s avviato...")
                timer_attivo = True
                asyncio.create_task(timer_check())
        else:
            foto_scattata = False
    except Exception as e:
        print("Dato ricevuto non valido:", data, e)

# ---------- AVVIO AUTOMATICO BLE_READ.PY IN UN NUOVO TERMINALE ----------
def avvia_ble_read():
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ble_read.py")
    print(f"Avvio {script_path} in un nuovo terminale...")

    # Usa lxterminal (Raspberry Pi Desktop)
    subprocess.Popen(["lxterminal", "-e", f"python3 {script_path}"])
    # Se hai gnome-terminal, puoi usare:
    # subprocess.Popen(["gnome-terminal", "--", "python3", script_path])
    # Se vuoi xterm:
    # subprocess.Popen(["xterm", "-e", f"python3 {script_path}"])

# ---------- MAIN LOOP ASINCRONO ----------
async def main():
    # Avvia ble_read.py in un nuovo terminale
    avvia_ble_read()

    print("Connessione in corso al dispositivo BLE dal codice principale...")
    async with BleakClient(MAC_ADDRESS) as client:
        print("Connesso al BLE!")
        await client.start_notify(CHAR_UUID, handle_data)
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
