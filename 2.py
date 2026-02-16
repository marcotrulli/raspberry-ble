import asyncio
import httpx
from bleak import BleakClient

# ---------- CONFIGURAZIONE ----------
MAC_ADDRESS = "48:87:2D:6C:FB:0C"
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
SOGLIA_DISTANZA = 40.0
CAMERA_IP = "192.168.1.36"
TIMER_SCATTO = 0.5  # Ridotto per essere più immediato

# ---------- STATO ----------
timer_attivo = False
ultima_distanza = None

async def invia_comando_camera():
    global timer_attivo
    print(f"📸 TRIGGER! Scatto in corso...")
    
    url = f"http://{CAMERA_IP}/capture"
    try:
        async with httpx.AsyncClient() as client:
            # Inviamo il comando e aspettiamo la conferma dall'ESP
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                print("✅ Foto aggiornata con UN SOLO trigger!")
            else:
                print(f"⚠️ Problema ESP: {response.status_code}")
    except Exception as e:
        print(f"❌ Errore rete: {e}")

    await asyncio.sleep(3) # Pausa di sicurezza per evitare doppi scatti
    timer_attivo = False

def notification_handler(sender, data):
    global timer_attivo, ultima_distanza
    try:
        distanza = float(data.decode().strip())
        if ultima_distanza is not None and not timer_attivo:
            # Scatta quando l'oggetto scende sotto la soglia
            if ultima_distanza > SOGLIA_DISTANZA and distanza < SOGLIA_DISTANZA:
                timer_attivo = True
                asyncio.create_task(invia_comando_camera())
        ultima_distanza = distanza
    except:
        pass

async def main():
    print(f"🔍 Connessione a {MAC_ADDRESS}...")
    try:
        async with BleakClient(MAC_ADDRESS) as client:
            print("✅ Sensore Pronto.")
            await client.start_notify(CHAR_UUID, notification_handler)
            while True:
                await asyncio.sleep(1)
    except Exception as e:
        print(f"💥 Errore: {e}")

if __name__ == "__main__":
    asyncio.run(main())
