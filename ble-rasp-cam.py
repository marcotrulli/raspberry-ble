# ble-rasp-cam.py
import asyncio
import requests
from bleak import BleakClient

# ---------- CONFIGURAZIONE ----------
CAM_IP = "192.168.1.36"       # IP della tua ESP32-CAM
SOGLIA = 40.0                  # distanza sotto la quale scatta la foto
DELAY = 2                      # secondi di attesa dopo soglia
MAC_ADDRESS = "48:87:2D:6C:FB:0C"  # MAC del tuo dispositivo BLE
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"  # UUID caratteristica BLE

# ---------- STATO GLOBALE ----------
foto_scattata = False
timer_attivo = False
valore_corrente = 0.0

# ---------- FUNZIONI ----------
async def timer_check():
    """Timer di 2 secondi prima di scattare la foto"""
    global foto_scattata, timer_attivo, valore_corrente
    await asyncio.sleep(DELAY)
    if valore_corrente <= SOGLIA:
        try:
            url = f"http://{CAM_IP}/capture"
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                print("📸 Foto scattata!")
                with open("ultima_foto.jpg", "wb") as f:
                    f.write(r.content)
            else:
                print("Errore HTTP:", r.status_code)
        except requests.exceptions.RequestException as e:
            print("Errore richiesta ESP32:", e)
        foto_scattata = True
    timer_attivo = False

def handle_data(sender, data):
    """Callback chiamato ogni volta che arriva un nuovo dato BLE"""
    global foto_scattata, timer_attivo, valore_corrente
    try:
        valore = float(data.decode().strip())
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

# ---------- ESECUZIONE PRINCIPALE ----------
async def main():
    print(f"🔗 Connessione al dispositivo BLE {MAC_ADDRESS}...")
    try:
        async with BleakClient(MAC_ADDRESS) as client:
            if client.is_connected:
                print("✅ Connesso al BLE!")

                # Abbonati agli aggiornamenti della caratteristica BLE
                await client.start_notify(CHAR_UUID, handle_data)

                print("🎧 In ascolto dei valori BLE...")
                # Loop infinito per mantenere la connessione attiva
                while True:
                    await asyncio.sleep(1)

            else:
                print("❌ Impossibile connettersi al BLE")

    except asyncio.CancelledError:
        print("Script principale interrotto")
    except Exception as e:
        print("Errore BLE:", e)

# ---------- AVVIO ----------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Script interrotto dall'utente")
    except Exception as e:
        print("Errore imprevisto:", e)
