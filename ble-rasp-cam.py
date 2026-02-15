import asyncio
import requests
from bleak import BleakClient

# ---------- CONFIGURAZIONE ----------
MAC_ADDRESS = "48:87:2D:6C:FB:0C"      # MAC del tuo dispositivo BLE
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
ESP32_CAM_IP = "192.168.1.36"          # IP della ESP32-CAM
SOGLIA = 40                             # soglia per scattare la foto
DELAY = 2                               # ritardo in secondi prima dello scatto

# ---------- VARIABILI GLOBALI ----------
foto_scattata = False        # True se abbiamo già scattato fino al prossimo reset
timer_attivo = False         # True se il timer dei 2 secondi è già partito
valore_corrente = None

# ---------- FUNZIONE CHE SCATTA FOTO ----------
def scatta_foto():
    global foto_scattata
    try:
        url = f"http://{ESP32_CAM_IP}/capture"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            print("✅ Foto scattata sulla cam!")
            foto_scattata = True   # blocca ulteriori scatti fino a reset
        else:
            print("❌ Errore HTTP:", r.status_code)
    except Exception as e:
        print("❌ Errore richiesta ESP32:", e)

# ---------- TASK ASINCRONO DEL TIMER ----------
async def timer_check():
    global timer_attivo, valore_corrente
    await asyncio.sleep(DELAY)
    # Dopo 2 secondi controlla ancora la soglia
    if valore_corrente is not None and valore_corrente <= SOGLIA:
        scatta_foto()
    timer_attivo = False  # timer finito

# ---------- CALLBACK BLE ----------
def handle_data(sender, data):
    global foto_scattata, timer_attivo, valore_corrente
    try:
        valore = int(data.decode().strip())
        valore_corrente = valore
        print(f"Distanza letta: {valore}")

        if valore <= SOGLIA:
            # Se non abbiamo già scattato e non c'è un timer attivo, partiamo il timer
            if not foto_scattata and not timer_attivo:
                print(f"⚡ Soglia {SOGLIA} raggiunta, timer di {DELAY}s avviato...")
                timer_attivo = True
                asyncio.create_task(timer_check())
        else:
            # Se il valore torna sopra soglia, resetta lo scatto
            if foto_scattata:
                print("🔄 Valore sopra soglia, reset scatto")
            foto_scattata = False
    except Exception as e:
        print("Dato ricevuto non valido:", data, e)

# ---------- MAIN LOOP ASINCRONO ----------
async def main():
    print("Connessione in corso al dispositivo BLE...")
    async with BleakClient(MAC_ADDRESS) as client:
        print("Connesso al BLE!")
        await client.start_notify(CHAR_UUID, handle_data)
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
