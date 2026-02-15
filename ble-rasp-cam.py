#!/usr/bin/env python3
import asyncio
import subprocess
import requests
import time

# Percorso del file ble_read.py
BLE_READ_PATH = "/home/pi/raspberry-ble/raspberry-ble/ble_read.py"

# IP della ESP32-CAM
CAM_IP = "192.168.1.36"

# Soglia distanza
SOGLIA = 40.0

# Timer per scatto (in secondi)
TIMER_SCATTO = 2.0

# Flag per evitare scatti continui
scatto_in_corso = False

# Avvio ble_read.py in un nuovo terminale separato
print("🚀 Avvio ble_read.py in nuovo terminale...")
subprocess.Popen([
    "lxterminal",
    "--command",
    f"bash -c 'python3 {BLE_READ_PATH}; exec bash'"
])

print("🎬 In ascolto dei valori BLE...")

async def leggi_ble_stream():
    global scatto_in_corso

    # Avvia ble_read.py come processo figlio e cattura stdout
    process = await asyncio.create_subprocess_exec(
        "python3", BLE_READ_PATH,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    while True:
        try:
            # Legge una riga alla volta dallo stdout
            riga = await process.stdout.readline()
            if not riga:
                await asyncio.sleep(0.1)
                continue

            riga = riga.decode().strip()
            if not riga:
                continue

            try:
                distanza = float(riga)
                print(f"Distanza letta: {distanza}")

                if distanza < SOGLIA:
                    if not scatto_in_corso:
                        scatto_in_corso = True
                        print(f"⚠️ Soglia {SOGLIA} raggiunta, timer di {TIMER_SCATTO}s avviato...")
                        await asyncio.sleep(TIMER_SCATTO)
                        # Invio richiesta alla CAM
                        try:
                            url = f"http://{CAM_IP}/capture"
                            r = requests.get(url, timeout=10)
                            if r.status_code == 200:
                                with open("ultima_foto.jpg", "wb") as f:
                                    f.write(r.content)
                                print("📸 Foto scattata!")
                            else:
                                print("Errore HTTP:", r.status_code)
                        except requests.exceptions.RequestException as e:
                            print("Errore richiesta ESP32-CAM:", e)
                        scatto_in_corso = False
                else:
                    scatto_in_corso = False

            except ValueError:
                print(f"Dato non valido da BLE: {riga}")

        except KeyboardInterrupt:
            print("🛑 Script principale interrotto")
            process.terminate()
            break

async def main():
    await leggi_ble_stream()

if __name__ == "__main__":
    asyncio.run(main())
