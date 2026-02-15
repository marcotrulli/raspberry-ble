import asyncio
import subprocess
import requests
from datetime import datetime

# ---------- CONFIGURAZIONE ----------
BLE_READ_PATH = "/home/pi/raspberry-ble/raspberry-ble/ble_read.py"  # percorso assoluto
CAM_IP = "192.168.1.36"  # IP della ESP32-CAM
SOGLIA = 40.0  # distanza soglia
TIMER_SCATTO = 2  # secondi prima dello scatto foto

# Flag per evitare scatti multipli
scatto_in_corso = False

# ---------- AVVIO BLE_READ IN NUOVO TERMINALE ----------
def avvia_ble_read():
    print("🚀 Avvio ble_read.py in nuovo terminale...")
    subprocess.Popen([
        "lxterminal",
        "--hold",
        "-e",
        f"python3 {BLE_READ_PATH}"
    ])

# ---------- FUNZIONE PER SCATTARE FOTO ----------
def scatta_foto():
    try:
        url = f"http://{CAM_IP}/capture"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"foto_{timestamp}.jpg"
            with open(filename, "wb") as f:
                f.write(r.content)
            print(f"📸 Foto scattata e salvata come {filename}")
        else:
            print("Errore HTTP dalla cam:", r.status_code)
    except requests.exceptions.RequestException as e:
        print("Errore richiesta ESP32:", e)

# ---------- LETTURA DATI BLE DAL FILE BLE_READ ----------
async def leggi_distanze_ble():
    # Usa subprocess per leggere in tempo reale l'output di ble_read.py
    proc = await asyncio.create_subprocess_exec(
        "python3", BLE_READ_PATH,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    return proc

# ---------- FUNZIONE PRINCIPALE ----------
async def main():
    global scatto_in_corso
    # Avvia il terminale separato con ble_read.py
    avvia_ble_read()

    print("🔔 In ascolto dei valori BLE...")

    # Crea processo BLE in pipe
    proc = await leggi_distanze_ble()
    
    while True:
        try:
            # legge una riga dall'output BLE
            line = await proc.stdout.readline()
            if not line:
                await asyncio.sleep(0.1)
                continue
            line_str = line.decode().strip()
            
            # Conversione in float
            try:
                distanza = float(line_str)
                print(f"Distanza letta: {distanza}")

                if distanza < SOGLIA and not scatto_in_corso:
                    print(f"⚠️ Soglia {SOGLIA} raggiunta, timer di {TIMER_SCATTO}s avviato...")
                    scatto_in_corso = True
                    await asyncio.sleep(TIMER_SCATTO)
                    scatta_foto()
                    scatto_in_corso = False

            except ValueError:
                print(f"Dato non valido ricevuto dal BLE: {line_str}")

        except asyncio.CancelledError:
            print("Script principale interrotto")
            break

# ---------- AVVIO SCRIPT ----------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Script interrotto dall'utente")
