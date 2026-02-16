import asyncio
import httpx
from bleak import BleakClient
from RPLCD.i2c import CharLCD
import time

# ---------- CONFIGURAZIONE ----------
MAC_ADDRESS = "48:87:2D:6C:FB:0C"      # MAC del sensore BLE
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
CAMERA_IP = "192.168.1.36"

I2C_ADDR = 0x27
LCD_COLS = 16
LCD_ROWS = 2
lcd = CharLCD('PCF8574', I2C_ADDR, cols=LCD_COLS, rows=LCD_ROWS)
lcd.write_string("Inizializzazione")
lcd.cursor_pos = (1, 0)
lcd.write_string(f"IP: {CAMERA_IP}")

# ---------- STATO ----------
timer_attivo = False
numero_scatti = 0

# ---------- FUNZIONE DISPLAY ----------
def lcd_update(line1, line2=None):
    """Aggiorna il display pulendo le righe per evitare residui"""
    lcd.cursor_pos = (0, 0)
    lcd.write_string(" " * LCD_COLS)
    lcd.cursor_pos = (0, 0)
    lcd.write_string(line1[:LCD_COLS])

    if line2:
        lcd.cursor_pos = (1, 0)
        lcd.write_string(" " * LCD_COLS)
        lcd.cursor_pos = (1, 0)
        lcd.write_string(line2[:LCD_COLS])
    
    # piccolo delay per refresh completo
    time.sleep(0.02)

# ---------- FUNZIONE FOTO ----------
async def scatta_foto(distanza):
    """Scatta la foto sulla ESP32-CAM e aggiorna il display"""
    global timer_attivo, numero_scatti
    numero_scatti += 1
    lcd_update(f"Trigger! Foto!", f"IP:{CAMERA_IP}")

    url = f"http://{CAMERA_IP}/capture"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10)
            if resp.status_code == 200:
                lcd_update(f"Foto OK! Nr:{numero_scatti}", f"IP:{CAMERA_IP}")
                print(f"📸 Foto scattata! Totale: {numero_scatti}")
            else:
                lcd_update("Errore ESP", f"IP:{CAMERA_IP}")
                print(f"⚠️ Errore ESP32: {resp.status_code}")
    except Exception as e:
        lcd_update("Errore rete", f"IP:{CAMERA_IP}")
        print(f"❌ Errore rete: {e}")

    await asyncio.sleep(3)
    timer_attivo = False

# ---------- HANDLER BLE ----------
def notification_handler(sender, data):
    global timer_attivo
    try:
        distanza = float(data.decode().strip())
        print(f"Distanza ricevuta: {distanza:.1f} cm")

        if not timer_attivo:
            timer_attivo = True
            # Lancia il trigger in background
            asyncio.create_task(scatta_foto(distanza))

    except Exception as e:
        print(f"Errore lettura BLE: {e}")

# ---------- LOOP BLE ----------
async def run_ble():
    while True:
        try:
            lcd_update("Connetto BLE...", f"IP:{CAMERA_IP}")
            async with BleakClient(MAC_ADDRESS) as client:
                lcd_update("Sensore pronto!", f"IP:{CAMERA_IP}")
                print("✅ Sensore BLE connesso")
                await client.start_notify(CHAR_UUID, notification_handler)

                while True:
                    await asyncio.sleep(1)  # loop principale in attesa di notifiche

        except Exception as e:
            lcd_update("Errore BLE!", f"IP:{CAMERA_IP}")
            print(f"💥 Errore BLE: {e}")
            await asyncio.sleep(5)  # ritenta la connessione

# ---------- AVVIO LOOP ----------
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run_ble())
    finally:
        loop.close()
