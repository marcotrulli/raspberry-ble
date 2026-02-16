import serial
import asyncio
import httpx

SERIAL_PORT = "/dev/ttyUSB0"  # o /dev/ttyAMA0 su Raspberry Pi
BAUDRATE = 9600
SOGLIA_DISTANZA = 40.0
CAMERA_IP = "192.168.1.36"
PAUSA_SICUREZZA = 3

timer_attivo = False
ultima_distanza = None

async def invia_comando_camera():
    global timer_attivo
    print("📸 TRIGGER! Scatto in corso...")
    url = f"http://{CAMERA_IP}/capture"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=10.0)
            if r.status_code == 200:
                print("✅ Foto scattata!")
            else:
                print(f"⚠️ Risposta ESP: {r.status_code}")
    except Exception as e:
        print(f"❌ Errore rete: {e}")

    await asyncio.sleep(PAUSA_SICUREZZA)
    timer_attivo = False
    print("🔄 Pronto per nuovo rilevamento\n")

async def main():
    global ultima_distanza, timer_attivo
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    print(f"🔍 Lettura seriale su {SERIAL_PORT}...")

    while True:
        line = ser.readline().decode().strip()
        if not line:
            await asyncio.sleep(0.1)
            continue
        try:
            distanza = float(line)
            print(f"📡 Distanza: {distanza}")

            if ultima_distanza is not None and not timer_attivo:
                if ultima_distanza > SOGLIA_DISTANZA and distanza < SOGLIA_DISTANZA:
                    timer_attivo = True
                    asyncio.create_task(invia_comando_camera())

            ultima_distanza = distanza
        except Exception as e:
            print(f"⚠️ Errore parsing: {e}")

        await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(main())
