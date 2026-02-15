import asyncio
import httpx
from bleak import BleakClient

# ---------- CONFIGURAZIONE ----------

MAC_ADDRESS = "48:87:2D:6C:FB:0C"      # MAC BLE del sensore
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb" # UUID Caratteristica

SOGLIA_DISTANZA = 40.0                # Soglia in cm per attivare lo scatto
CAMERA_IP = "192.168.1.36"            # IP ESP32-CAM
TIMER_SCATTO = 2                      # Ritardo prima della foto (secondi)

# ---------- STATO SISTEMA ----------
timer_attivo = False
ultima_distanza = None  # Per rilevare fronte di discesa

# ---------- FUNZIONE INVIO FOTO ----------
async def invia_comando_camera():
    global timer_attivo

    print(f"⏳ Attendendo {TIMER_SCATTO}s prima di scattare...")
    await asyncio.sleep(TIMER_SCATTO)

    url = f"http://{CAMERA_IP}/capture"

    try:
        async with httpx.AsyncClient() as client:
            print(f"📸 Invio segnale di scatto a {CAMERA_IP}...")
            response = await client.get(url, timeout=10.0)

            if response.status_code == 200:
                print("✅ Foto aggiornata correttamente sull’ESP32-CAM")
            else:
                print(f"⚠️ ESP32 ha risposto con errore: {response.status_code}")

    except Exception as e:
        print(f"❌ Errore rete con ESP32-CAM: {e}")

    # Rilascia lock
    timer_attivo = False
    print("🔄 Sistema pronto per nuovo rilevamento")

# ---------- HANDLER BLE ----------
def notification_handler(sender, data):
    global timer_attivo, ultima_distanza

    try:
        string_data = data.decode().strip()
        distanza = float(string_data)
        print(f"📡 Distanza attuale: {distanza} cm")

        # FRONT DROP: solo quando distanza passa da sopra soglia a sotto soglia
        if ultima_distanza is not None:
            if ultima_distanza > SOGLIA_DISTANZA and distanza < SOGLIA_DISTANZA and not timer_attivo:
                print(f"🚨 Oggetto rilevato a {distanza} cm!")
                timer_attivo = True
                asyncio.create_task(invia_comando_camera())

        ultima_distanza = distanza

    except ValueError:
        pass  # pacchetti non numerici
    except Exception as e:
        print(f"❓ Errore imprevisto nei dati: {e}")

# ---------- FUNZIONE PRINCIPALE ----------
async def main():
    print("--- SISTEMA BLE + ESP32-CAM AVVIATO ---")
    print(f"🔍 Ricerca dispositivo: {MAC_ADDRESS}")

    try:
        async with BleakClient(MAC_ADDRESS) as client:
            if client.is_connected:
                print(f"✅ Connesso a {MAC_ADDRESS}")
                await client.start_notify(CHAR_UUID, notification_handler)
                print(f"🎧 In ascolto su {CHAR_UUID}. Premere Ctrl+C per fermare.")

                while True:
                    await asyncio.sleep(1)
            else:
                print("❌ Connessione fallita. Verifica il sensore.")

    except Exception as e:
        print(f"💥 Errore durante l’esecuzione: {e}")

# ---------- RUN ----------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Spegnimento sistema in corso...")
