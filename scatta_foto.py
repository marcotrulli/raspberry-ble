import requests

ESP32_CAM_IP = "192.168.1.36"  # IP della tua ESP32-CAM

def scatta_foto():
    try:
        url = f"http://{ESP32_CAM_IP}/capture"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            print("📸 Foto scattata sulla cam!")
        else:
            print("Errore HTTP:", r.status_code)
    except Exception as e:
        print("Errore richiesta ESP32:", e)

if __name__ == "__main__":
    comando = input("Scrivi 'foto' per scattare: ").strip().lower()
    if comando == "foto":
        scatta_foto()
    else:
        print("Comando non riconosciuto.")
