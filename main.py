from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse
from twilio.rest import Client
import uvicorn
import re
import time

from config import config
from database import get_history, save_messages, is_human_mode, set_human_mode, clear_history, is_new_session
from ai_engine import get_ai_response
from sheets import registrar_pedido
from followup import router as followup_router

app = FastAPI(title="WhatsApp AI Bot — LONGEVITÉ")
app.include_router(followup_router)

twilio_client = Client(config.TWILIO_SID, config.TWILIO_TOKEN)

VENDEDOR = "whatsapp:+573102897401"  # Número del asesor principal

# ── Cache anti-duplicados ──────────────────────────────────────────────────────
# Guarda (phone, texto_del_mensaje) → timestamp de la última vez que se procesó
# Si llega el mismo mensaje del mismo número en menos de 30 segundos, se ignora.
_processed_messages: dict = {}
DEDUP_WINDOW_SECONDS = 30


def _is_duplicate(phone: str, text: str) -> bool:
    key = phone + "|" + text
    now = time.time()
    last = _processed_messages.get(key)
    if last and (now - last) < DEDUP_WINDOW_SECONDS:
        return True
    _processed_messages[key] = now
    # Limpiar entradas viejas para no crecer infinito
    cutoff = now - DEDUP_WINDOW_SECONDS * 2
    for k in list(_processed_messages.keys()):
        if _processed_messages[k] < cutoff:
            del _processed_messages[k]
    return False


def send_whatsapp(to: str, body: str):
    twilio_client.messages.create(
        body=body,
        from_="whatsapp:" + config.TWILIO_NUMBER,
        to=to
    )


def parse_pedido(reply: str):
    """
    Busca y parsea la línea PEDIDO_CONFIRMAR en la respuesta del bot.
    Formato: PEDIDO_CONFIRMAR|nombre|identificacion|codigo|producto|cantidad|precio|direccion|barrio|ciudad
    Retorna un dict con los campos o None si no se puede parsear.
    """
    for linea in reply.split("\n"):
        linea = linea.strip()
        if not linea.startswith("PEDIDO_CONFIRMAR"):
            continue

        print("[PEDIDO LINEA RAW] " + linea)

        # Limpiar caracteres raros
        linea = re.sub(r"[*_`]", "", linea).strip()
        partes = [p.strip() for p in linea.split("|")]

        if len(partes) < 10:
            print("[ERROR PARSE] Solo " + str(len(partes)) + " partes, se esperaban 10")
            return None

        try:
            precio_raw = partes[6].replace("$", "").replace(".", "").replace(",", "").strip()
            precio = int(precio_raw)
        except ValueError:
            print("[ERROR PARSE] Precio inválido: " + partes[6])
            return None

        try:
            cantidad = int(partes[5])
        except ValueError:
            cantidad = 1

        return {
            "nombre":         partes[1],
            "identificacion": partes[2],
            "codigo":         partes[3],
            "producto":       partes[4],
            "cantidad":       cantidad,
            "precio":         precio,
            "direccion":      partes[7],
            "barrio":         partes[8],
            "ciudad":         partes[9],
        }

    return None


@app.get("/health")
def health_check():
    return {"status": "ok", "bot": config.EMPRESA}


@app.post("/webhook")
async def webhook(From: str = Form(...), Body: str = Form(...)):
    phone = From
    text  = Body.strip()
    print("[MSG] " + phone + ": " + text)

    # ── Anti-duplicados: ignorar si el mismo mensaje llega dos veces en 30s ───
    if _is_duplicate(phone, text):
        print("[DUPLICADO] Ignorado: " + phone + " — " + text[:50])
        return PlainTextResponse("", status_code=200)

    # ── Comandos del vendedor ──────────────────────────────────────
    if text.startswith("/bot-on"):
        partes = text.split(" ")
        if len(partes) == 2:
            numero = partes[1].strip()
            if not numero.startswith("whatsapp:"):
                numero = "whatsapp:" + numero
            set_human_mode(numero, False)
            send_whatsapp(phone, "Bot reactivado para " + numero)
            return PlainTextResponse("", status_code=200)

    if text.startswith("/bot-off"):
        partes = text.split(" ")
        if len(partes) == 2:
            numero = partes[1].strip()
            if not numero.startswith("whatsapp:"):
                numero = "whatsapp:" + numero
            set_human_mode(numero, True)
            send_whatsapp(phone, "Bot desactivado para " + numero)
            return PlainTextResponse("", status_code=200)

    if text.startswith("/reset"):
        partes = text.split(" ")
        numero = partes[1].strip() if len(partes) == 2 else phone
        if not numero.startswith("whatsapp:"):
            numero = "whatsapp:" + numero
        clear_history(numero)
        send_whatsapp(phone, "Historial borrado para " + numero)
        return PlainTextResponse("", status_code=200)

    # ── Modo humano activo ─────────────────────────────────────────
    if is_human_mode(phone):
        print("[HUMANO] " + phone + " bot desactivado")
        return PlainTextResponse("", status_code=200)

    # ── Nueva sesión: limpiar historial del día anterior ──────────
    if is_new_session(phone):
        print("[NUEVA SESION] Limpiando historial de " + phone)
        clear_history(phone)

    # ── Palabras clave para transferir a asesor ────────────────────
    triggers = ["humano", "asesor", "persona", "agente"]
    if any(w in text.lower() for w in triggers):
        set_human_mode(phone, True)
        reply = "Un asesor se comunicará contigo pronto. 🌿"
        send_whatsapp(phone, reply)
        save_messages(phone, text, reply)
        alerta = ("🌿 CLIENTE NECESITA ASESOR\n"
                  "Número: " + phone.replace("whatsapp:", "") + "\n"
                  "Mensaje: " + text + "\n\n"
                  "Cuando termines escribe:\n"
                  "/bot-on " + phone.replace("whatsapp:", ""))
        send_whatsapp(VENDEDOR, alerta)
        return PlainTextResponse("", status_code=200)

    # ── Flujo principal IA ─────────────────────────────────────────
    try:
        history = get_history(phone)
        reply   = await get_ai_response(phone, text, history)

        # Transferencia a humano detectada por la IA
        if "TRANSFERIR_HUMANO" in reply:
            set_human_mode(phone, True)
            reply = "No tengo esa información. Un asesor te contactará pronto. 🌿"
            alerta = ("🌿 CLIENTE NECESITA ASESOR\n"
                      "Número: " + phone.replace("whatsapp:", "") + "\n"
                      "Cuando termines escribe:\n"
                      "/bot-on " + phone.replace("whatsapp:", ""))
            send_whatsapp(VENDEDOR, alerta)
            save_messages(phone, text, reply)
            send_whatsapp(phone, reply)
            print("[OK] Transferido a humano: " + phone)
            return PlainTextResponse("", status_code=200)

        # Pedido detectado
        elif "PEDIDO_CONFIRMAR" in reply:
            pedido = parse_pedido(reply)

            if pedido is None:
                print("[ERROR PEDIDO] No se pudo parsear la línea técnica")
                reply = "Hubo un problema procesando tu pedido. Un asesor te ayudará pronto."
                alerta = ("⚠️ PEDIDO FALLIDO — REQUIERE ATENCIÓN MANUAL\n"
                          "Número: " + phone.replace("whatsapp:", "") + "\n"
                          "El bot no pudo parsear el pedido correctamente.")
                send_whatsapp(VENDEDOR, alerta)
                save_messages(phone, text, reply)
                send_whatsapp(phone, reply)
                return PlainTextResponse("", status_code=200)

            total = pedido["cantidad"] * pedido["precio"]

            ok = await registrar_pedido(
                phone,
                pedido["nombre"],
                pedido["identificacion"],
                pedido["codigo"],
                pedido["producto"],
                pedido["cantidad"],
                pedido["precio"],
                pedido["direccion"],
                pedido["barrio"],
                pedido["ciudad"],
            )

            if ok:
                reply = ("✅ Pedido registrado exitosamente.\n\n"
                         "Producto: "   + pedido["producto"]   + "\n"
                         "Cantidad: "   + str(pedido["cantidad"]) + "\n"
                         "Dirección: "  + pedido["direccion"]  + "\n"
                         "Barrio: "     + pedido["barrio"]     + "\n"
                         "Ciudad: "     + pedido["ciudad"]     + "\n"
                         "Total: $"     + "{:,}".format(total).replace(",", ".") + "\n\n"
                         "Un asesor te enviará los datos de pago pronto. 🌿")
            else:
                reply = "Hubo un problema registrando tu pedido. Un asesor te ayudará pronto."
                alerta = ("⚠️ PEDIDO FALLIDO — ERROR EN SHEETS\n"
                          "Número: " + phone.replace("whatsapp:", "") + "\n"
                          "Cliente: " + pedido["nombre"] + "\n"
                          "Producto: " + pedido["producto"])
                send_whatsapp(VENDEDOR, alerta)

            save_messages(phone, text, reply)
            send_whatsapp(phone, reply)
            print("[OK] Pedido procesado para " + phone)
            return PlainTextResponse("", status_code=200)

        # Respuesta normal
        save_messages(phone, text, reply)
        send_whatsapp(phone, reply)
        print("[OK] Respuesta enviada a " + phone)

    except Exception as e:
        print("[ERROR] " + str(e))
        send_whatsapp(phone, "Tuve un problema técnico. Intenta en unos minutos.")

    return PlainTextResponse("", status_code=200)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, reload=True)