import asyncio
import httpx
from bleak import BleakClient
from RPLCD.i2c import CharLCD
import time

# ---------- CONFIGURAZIONE ---------- 
MAC_ADDRESS = "48:87:2D:6C:FB:0C"
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
SOGLIA_DISTANZA = 40.0
CAMERA_IP = "192.168.1.36"
TIMER_SCATTO = 0.5

# ---------- CONFIGURAZIONE LCD I2C ----------
I2C_ADDR = 0x27
LCD_COLS = 16
LCD_ROWS = 2
lcd = CharLCD('PCF8574', I2C_ADDR, cols=LCD_COLS, rows=LCD_ROWS)
lcd.clear()
lcd.write_string("Inizializzazione")

# ---------- STATO ----------
timer_attivo = False
ultima_distanza = None

async def invia_comando_camera():
    global timer_attivo
    print(f"📸 TRIGGER! Scatto in corso...")
    
    lcd.clear()
    lcd.write_string("Trigger! Foto...")

    url = f"http://{CAMERA_IP}/capture"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                print("✅ Foto aggiornata con UN SOLO trigger!")
                lcd.clear()
                lcd.write_string(f"Foto OK!")
                lcd.cursor_pos = (1, 0)
                lcd.write_string(f"IP: {CAMERA_IP}")
            else:
                print(f"⚠️ Problema ESP: {response.status_code}")
                lcd.clear()
                lcd.write_string("Errore ESP")
                lcd.cursor_pos = (1, 0)
                lcd.write_string(f"IP: {CAMERA_IP}")
    except Exception as e:
        print(f"❌ Errore rete: {e}")
        lcd.clear()
        lcd.write_string("Errore rete")
        lcd.cursor_pos = (1, 0)
        lcd.write_string(f"IP: {CAMERA_IP}")

    await asyncio.sleep(3)
    timer_attivo = False

def notification_handler(sender, data):
    global timer_attivo, ultima_distanza
    try:
        distanza = float(data.decode().strip())
        # Mostra distanza e IP sul LCD
        lcd.clear()
        lcd.write_string(f"Distanza: {distanza:.1f}cm")
        lcd.cursor_pos = (1, 0)
        lcd.write_string(f"IP: {CAMERA_IP}")

        if ultima_distanza is not None and not timer_attivo:
            if ultima_distanza > SOGLIA_DISTANZA and distanza < SOGLIA_DISTANZA:
                timer_attivo = True
                asyncio.create_task(invia_comando_camera())
        ultima_distanza = distanza
    except:
        pass

async def main():
    print(f"🔍 Connessione a {MAC_ADDRESS}...")
    lcd.clear()
    lcd.write_string("Connetto BLE...")
    try:
        async with BleakClient(MAC_ADDRESS) as client:
            print("✅ Sensore Pronto.")
            lcd.clear()
            lcd.write_string("Sensore pronto!")
            lcd.cursor_pos = (1, 0)
            lcd.write_string(f"IP: {CAMERA_IP}")
            await client.start_notify(CHAR_UUID, notification_handler)
            while True:
                await asyncio.sleep(1)
    except Exception as e:
        print(f"💥 Errore: {e}")
        lcd.clear()
        lcd.write_string("Errore BLE!")
        lcd.cursor_pos = (1, 0)
        lcd.write_string(f"IP: {CAMERA_IP}")
        time.sleep(2)
        lcd.clear()
