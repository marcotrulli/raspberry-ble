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
numero_scatti = 0

# Coda per comunicazione BLE -> display
distanza_queue = asyncio.Queue()

# ---------- FUNZIONE DISPLAY ----------
def lcd_update_sync(line1, line2=None):
    """Aggiorna il display cancellando le righe per evitare residui"""
    lcd.cursor_pos = (0, 0)
    lcd.write_string(" " * LCD_COLS)
    lcd.cursor_pos = (0, 0)
    lcd.write_string(line1[:LCD_COLS])

    if line2:
        lcd.cursor_pos = (1, 0)
        lcd.write_string(" " * LCD_COLS)
        lcd.cursor_pos = (1, 0)
        lcd.write_string(line2[:LCD_COLS])
    
    # piccolo delay per il refresh completo del display
    time.sleep(0.02)

async def lcd_task():
    """Task che legge la coda e aggiorna il display in tempo reale"""
    while True:
        distanza = await distanza_queue.get()
        lcd_update_sync(f"Distanza: {distanza:.1f}cm", f"IP: {CAMERA_IP}")
        distanza_queue.task_done()

# ---------- FUNZIONE FOTO ----------
async def invia_comando_camera():
    global timer_attivo, numero_scatti
    numero_scatti += 1
    lcd_update_sync("Trigger! Foto...", f"IP: {CAMERA_IP}")
    url = f"http://{CAMERA_IP}/capture"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10)
            if resp.status_code == 200:
                lcd_update_sync(f"Foto OK! Nr:{numero_scatti}", f"IP: {CAMERA_IP}")
            else:
                lcd_update_sync("Errore ESP", f"IP: {CAMERA_IP}")
    except:
        lcd_update_sync("Errore rete", f"IP: {CAMERA_IP}")
    await asyncio.sleep(3)
    timer_attivo = False

# ---------- HANDLER BLE ----------
def notification_handler(sender, data):
    global timer_attivo, ultima_distanza
    try:
        distanza = float(data.decode().strip())
        # Inserisce nella coda, il task LCD aggiorna
        asyncio.create_task(distanza_queue.put(distanza))

        if ultima_distanza is not None and not timer_attivo:
            if ultima_distanza > SOGLIA_DISTANZA and distanza < SOGLIA_DISTANZA:
                timer_attivo = True
                asyncio.create_task(invia_comando_camera())
        ultima_distanza = distanza
    except:
        pass

# ---------- LOOP BLE ----------
async def run_ble_loop():
    while True:
        try:
            lcd_update_sync("Connetto BLE...", f"IP: {CAMERA_IP}")
            async with BleakClient(MAC_ADDRESS) as client:
                lcd_update_sync("Sensore pronto!", f"IP: {CAMERA_IP}")
                await client.start_notify(CHAR_UUID, notification_handler)
                # Avvia task LCD in parallelo
                lcd_worker = asyncio.create_task(lcd_task())
                while True:
                    await asyncio.sleep(1)
        except Exception as e:
            lcd_update_sync("Errore BLE!", f"IP: {CAMERA_IP}")
            await asyncio.sleep(5)  # ritenta connessione

# ---------- AVVIO LOOP ----------
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(run_ble_loop())
finally:
    loop.close()
