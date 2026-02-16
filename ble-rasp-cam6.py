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
lcd.write_string("Inizializzazione")
lcd.cursor_pos = (1, 0)
lcd.write_string(f"IP: {CAMERA_IP}")

# ---------- STATO ----------
timer_attivo = False
ultima_distanza = None

# Funzione helper per LCD
async def lcd_update(line1, line2=None):
    lcd.cursor_pos = (0, 0)
    lcd.write_string(" " * LCD_COLS)
    lcd.cursor_pos = (0, 0)
    lcd.write_string(line1[:LCD_COLS])
    if line2:
        lcd.cursor_pos = (1, 0)
        lcd.write_string(" " * LCD_COLS)
        lcd.cursor_pos = (1, 0)
        lcd.write_string(line2[:LCD_COLS])

async def invia_comando_camera():
    global timer_attivo
    print(f"📸 TRIGGER! Scatto in corso...")
    await lcd_update("Trigger! Foto...", f"IP: {CAMERA_IP}")

    url = f"http://{CAMERA_IP}/capture"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                print("✅ Foto aggiornata con UN SOLO trigger!")
                await lcd_update("Foto OK!", f"IP: {CAMERA_IP}")
            else:
                print(f"⚠️ Problema ESP: {response.status_code}")
                await lcd_update("Errore ESP", f"IP: {CAMERA_IP}")
    except Exception as e:
        print(f"❌ Errore rete: {e}")
        await lcd_update("Errore rete", f"IP: {CAMERA_IP}")

    await asyncio.sleep(3)
    timer_attivo = False

def notification_handler(sender, data):
    global timer_attivo, ultima_distanza
    try:
        distanza = float(data.decode().strip())
        asyncio.create_task(lcd_update(f"Distanza: {distanza:.1f}cm", f"IP: {CAMERA_IP}"))

        if ultima_distanza is not None and not timer_attivo:
            if ultima_distanza > SOGLIA_DISTANZA and distanza < SOGLIA_DISTANZA:
                timer_attivo = True
                asyncio.create_task(invia_comando_camera())
        ultima_distanza = distanza
    except:
        pass

async def run_ble_loop():
    while True:
        try:
            print(f"🔍 Connessione a {MAC_ADDRESS}...")
            await lcd_update("Connetto BLE...", f"IP: {CAMERA_IP}")
            async with BleakClient(MAC_ADDRESS) as client:
                print("✅ Sensore Pronto.")
                await lcd_update("Sensore pronto!", f"IP: {CAMERA_IP}")
                await client.start_notify(CHAR_UUID, notification_handler)
                while True:
                    await asyncio.sleep(1)
        except Exception as e:
            print(f"💥 Errore BLE: {e}")
            await lcd_update("Errore BLE!", f"IP: {CAMERA_IP}")
            await asyncio.sleep(5)  # Riprova la connessione

# ---------- Avvio manuale loop ----------
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(run_ble_loop())
finally:
    loop.close()
