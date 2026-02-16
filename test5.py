import serial
import asyncio
import httpx

# ---------- CONFIG ----------
SERIAL_PORT = "/dev/serial0"  # HC-05 collegato ai pin GPIO
BAUDRATE = 9600
SOGLIA_DISTANZA = 40.0        # soglia in cm per scattare la foto
CAMERA_IP = "192.168.1.36"    # IP ESP32-CAM
PAUSA_SICUREZZA = 3           # secondi tra scatti

# ---------- STATO ----------
timer_attivo = False
ultima_distanza = None

# ---------- FUNZIONE SCATTO FOTO ----------
async def invia_comando_camera():
    global timer_attivo
    print("📸 TRIGGER! Scatto in corso...")
    url = f"http://{CAMERA_IP}/capture"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                print("✅ Foto scattata!")
            else:
                print(f"⚠️ Risposta ESP: {response.status_code}")
    except Exception as e:
        print(f"❌ Errore rete: {e}")

    await asyncio.sleep(PAUSA_SICUREZZA)
    timer_attivo = False
    print("🔄 Pronto per nuovo rilevamento\n")

# ---------- LOOP PRINCIPALE ----------
async def main():
    global ultima_distanza, timer_attivo
    print(f"🔍 Apertura porta seriale {SERIAL_PORT} a {BAUDRATE} baud...")
    
    try:
        ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    except serial.SerialException as e:
        print(f"💥 Errore apertura seriale: {e}")
        return

    print("✅ Porta seriale pronta, inizio lettura distanze...")

    while True:
        line = ser.readline().decode(errors='ignore').strip()
        if not line:
            await asyncio.sleep(0.1)
            continue

        try:
            distanza = float(line)
            print(f"📡 Distanza: {distanza} cm")

            # Controlla soglia e timer
            if ultima_distanza is not None and not timer_attivo:
                if ultima_distanza > SOGLIA_DISTANZA and distanza < SOGLIA_DISTANZA:
                    timer_attivo = True
                    asyncio.create_task(invia_comando_camera())

            ultima_distanza = distanza

        except ValueError:
            print(f"⚠️ Dato non valido: '{line}'")

        await asyncio.sleep(0.1)  # piccolo delay per non saturare la CPU

# ---------- AVVIO SCRIPT ----------
if __name__ == "__main__":
    asyncio.run(main())
