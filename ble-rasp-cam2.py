import asyncio
import httpx
from bleak import BleakClient

# ---------- CONFIGURAZIONE DISPOSITIVI ----------
MAC_ADDRESS = "48:87:2D:6C:FB:0C"      # MAC BLE del sensore
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb" # UUID Caratteristica
SOGLIA_DISTANZA = 40.0                # Soglia in cm per attivare lo scatto
CAMERA_IP = "192.168.1.36"            # IP dell'ESP32-CAM
TIMER_SCATTO = 2                      # Ritardo prima della foto (secondi)

# ---------- STATO SISTEMA ----------
timer_attivo = False

# ---------- LOGICA FOTOCAMERA (ASYNC) ----------
async def invia_comando_camera():
    global timer_attivo
    
    print(f"⏳ Attendendo {TIMER_SCATTO}s prima di scattare...")
    await asyncio.sleep(TIMER_SCATTO)
    
    url = f"http://{CAMERA_IP}/capture"
    
    try:
        # Usiamo httpx per una richiesta non-blocking
        async with httpx.AsyncClient() as client:
            print(f"📸 Invio segnale di scatto a {CAMERA_IP}...")
            response = await client.get(url, timeout=10.0)
            
            if response.status_code == 200:
                print("✅ Fatto! Foto salvata correttamente.")
            else:
                print(f"⚠️ L'ESP32 ha risposto con errore: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Errore di rete con ESP32-CAM: {e}")
    
    # Rilascia il lock per permettere nuovi scatti
    timer_attivo = False
    print("🔄 Sistema pronto per un nuovo rilevamento.")

# ---------- GESTORE DATI BLE ----------
def notification_handler(sender, data):
    global timer_attivo
    
    try:
        # Decodifica il valore ricevuto (stringa -> float)
        string_data = data.decode().strip()
        distanza = float(string_data)
        
        # Stampa continua delle distanze nel terminale
        print(f"📡 Distanza attuale: {distanza} cm")

        # Verifica soglia e se il sistema non è già occupato a scattare
        if distanza < SOGLIA_DISTANZA and not timer_attivo:
            print(f"🚨 ALERT: Oggetto rilevato a {distanza} cm!")
            timer_attivo = True
            # Avvia il task della camera in background
            asyncio.create_task(invia_comando_camera())

    except ValueError:
        # Gestisce eventuali pacchetti sporchi o non numerici
        pass 
    except Exception as e:
        print(f"❓ Errore imprevisto nei dati: {e}")

# ---------- FUNZIONE PRINCIPALE ----------
async def main():
    print("--- SISTEMA INTEGRATO BLE + CAMERA AVVIATO ---")
    print(f"🔍 Ricerca dispositivo: {MAC_ADDRESS}")

    try:
        async with BleakClient(MAC_ADDRESS) as client:
            if client.is_connected:
                print(f"✅ Connesso a {MAC_ADDRESS}!")
                
                # Avvia l'ascolto delle notifiche
                await client.start_notify(CHAR_UUID, notification_handler)
                print(f"🎧 In ascolto su {CHAR_UUID}. Premere Ctrl+C per fermare.")

                # Loop infinito per mantenere attiva la connessione
                while True:
                    await asyncio.sleep(1)
            else:
                print("❌ Connessione fallita. Verifica che il sensore sia acceso.")

    except Exception as e:
        print(f"💥 Errore durante l'esecuzione: {e}")

# ---------- RUN ----------
if __name__ == "__main__":
    try:
        # Installazione automatica di httpx se mancante (opzionale, manuale è meglio)
        # pip install httpx bleak
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Spegnimento del sistema in corso...")
