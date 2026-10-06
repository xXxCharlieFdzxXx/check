import os
import csv
import threading
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ==========================================
# ⚙️ CONFIGURACIÓN
# ==========================================
API_ID = 30122276
API_HASH = "9d9949b9b1a8279bf0084fe2241ed679"
BOT_TOKEN = "8561628306:AAG7S0S_WPI907KpRMHr5gJCrSlcY6rEE88"
PHONE_NUMBER = "+527351131683"
TARGET_CHAT_ID = -1001019815845

# ⚠️ PEGA AQUÍ TU STRING SESSION
STRING_SESSION = "PEGA_AQUI_TU_STRING_SESSION"

# Archivo CSV local
CSV_PATH = "bin-list-data.csv"

# Memoria en RAM para evitar duplicados
tarjetas_procesadas = set()

# ==========================================
# 🌐 SERVIDOR WEB (Para Render + UptimeRobot)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# 📂 LECTURA DEL CSV DE BIN
# ==========================================
def cargar_bin_desde_csv():
    bin_dict = {}
    try:
        with open(CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=',')
            for row in reader:
                bin_raw = row.get('BIN', '').strip()
                if not bin_raw:
                    continue
                
                bin_num = bin_raw.zfill(6)[:6]
                
                bank = row.get('Issuer', 'Desconocido').strip()
                brand = row.get('Brand', 'N/A').strip()
                card_type = row.get('Type', 'N/A').strip()
                country = row.get('CountryName', '[??]').strip()
                
                bin_dict[bin_num] = {
                    "bank": bank if bank else "Desconocido",
                    "brand": brand if brand else "N/A",
                    "type": card_type if card_type else "N/A",
                    "country": country if country else "[??]"
                }
    except Exception:
        pass # Silencio absoluto en caso de error de lectura
    return bin_dict

BIN_DATA = {}

# ==========================================
# 🔍 BÚSQUEDA DE BIN
# ==========================================
def obtener_info_bin(bin_numero):
    bin_numero = str(bin_numero).strip()[:6].zfill(6)
    info = BIN_DATA.get(bin_numero)
    
    if info:
        bank = info.get("bank", "Desconocido")
        brand = info.get("brand", "N/A")
        card_type = info.get("type", "N/A")
        country = info.get("country", "[??]")
        
        info_str = f"{brand}-{card_type.capitalize()}" if brand != "N/A" and card_type != "N/A" else "N/A-N/A"
        return {"bank": bank, "info": info_str, "country": country}
    else:
        return {"bank": "Desconocido", "info": "N/A-N/A", "country": "[??]"}

# ==========================================
# 🤖 LÓGICA DEL BOT DE TELEGRAM
# ==========================================
client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

@client.on(events.NewMessage)
async def handler(event):
    if event.chat_id == TARGET_CHAT_ID:
        mensaje = event.message.text
        
        if "|" in mensaje:
            cc_data = mensaje.split("|")
            if len(cc_data) >= 4:
                numero_tarjeta = cc_data[0]
                bin_tarjeta = numero_tarjeta[:6]
                
                # Filtro de duplicados
                if numero_tarjeta in tarjetas_procesadas:
                    return
                tarjetas_procesadas.add(numero_tarjeta)
                
                # Obtener info del BIN
                info_bin = obtener_info_bin(bin_tarjeta)
                
                # Chequear la CC (Pon tu lógica real aquí)
                respuesta_cc = "Approved OK" 
                
                # Armar el mensaje
                mensaje_final = f"""
➤ Bank: {info_bin['bank']}
➤ Info: {info_bin['info']}
➤ Country: {info_bin['country']}
━━━━━━━━━

➤ Cc: {numero_tarjeta}
➤ Gate: Auth
➤ Response: {respuesta_cc}
"""
                # Enviar a Telegram
                await event.reply(mensaje_final)

async def iniciar_bot():
    await client.start(phone=PHONE_NUMBER)
    await client.run_until_disconnected()

# ==========================================
# 🚀 INICIO
# ==========================================
if __name__ == "__main__":
    BIN_DATA = cargar_bin_desde_csv()
    
    hilo_web = threading.Thread(target=run_flask)
    hilo_web.daemon = True
    hilo_web.start()
    
    client.loop.run_until_complete(iniciar_bot())
