import httpx
import csv
import io
import json
from datetime import datetime
from products import get_duracion

SHEET_ID = "1Cg1SBYIq2kiPYI-D8mKKlvt1dLC8Zz045jIWpK3Ho0k"
BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyR_tjw8Gl4dMGhoGbUGPy_k0LKCcs0FJHlxfE2vNcDJED3LWhAeVYGDOQ_trR58Nyj/exec"


# =============================
# 📦 CATALOGO
# =============================
async def get_catalogo() -> str:
    url = BASE_URL + "&sheet=Catalogo"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10)

    reader = csv.reader(io.StringIO(response.text))
    rows = list(reader)

    productos = []

    for row in rows:
        # Saltar filas con menos de 10 columnas
        if len(row) < 10:
            continue
        # La columna A (índice 0) debe empezar con R
        if not str(row[0]).strip().startswith("R"):
            continue
        # ✅ FIX: Estado está en índice 9 (columna J), no 10
        if row[9].strip().lower() != "activo":
            continue

        precio_raw = row[6].replace("$", "").replace(".", "").replace(",", "").strip()

        try:
            precio_fmt = "${:,}".format(int(precio_raw)).replace(",", ".")
        except:
            precio_fmt = row[6]

        productos.append(
            f"- {row[2]} | Pres: {row[3]} | Marca: {row[4]} | "
            f"Sabor: {row[5]} | Precio: {precio_fmt} | "
            f"Stock: {row[7]} uds | Ref: {row[8]}"
        )

    if not productos:
        return "No hay productos disponibles en este momento."

    print(f"[CATALOGO OK] {len(productos)} productos cargados")
    return "\n".join(productos)


# =============================
# 🧾 REGISTRAR PEDIDO
# =============================
async def registrar_pedido(
    telefono: str,
    nombre: str,
    referencia: str,
    producto: str,
    presentacion: str,
    marca: str,
    sabor: str,
    cantidad: int,
    precio: int,
    ubicacion: str,
) -> bool:

    try:
        now = datetime.now()

        data = {
            "telefono": telefono,
            "nombre": nombre,
            "referencia": referencia,
            "producto": producto,
            "presentacion": presentacion,
            "marca": marca,
            "sabor": sabor,
            "cantidad": cantidad,
            "precio": precio,
            "ubicacion": ubicacion,
            "fecha": now.strftime("%Y-%m-%d"),
            "hora": now.strftime("%H:%M:%S"),
            "dias_duracion": get_duracion(producto),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                APPS_SCRIPT_URL,
                content=json.dumps(data),
                headers={"Content-Type": "application/json"},
                follow_redirects=True,
                timeout=15.0,
            )

        print(f"[PEDIDO RAW] {response.status_code} - {response.text[:100]}")

        result = response.json()

        if result.get("status") == "ok":
            print(f"[PEDIDO OK] {result.get('pedido', '')}")
            return True

        print(f"[PEDIDO ERROR] {result}")
        return False

    except Exception as e:
        print(f"[ERROR PEDIDO] {e}")
        return False


# =============================
# 🔁 FOLLOW-UP
# =============================
async def get_pedidos() -> list:
    url = BASE_URL + "&sheet=Pedidos"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10)

    reader = csv.reader(io.StringIO(response.text))
    rows = list(reader)

    pedidos = []

    for row in rows:
        if len(row) < 18 or row[0] == "# Pedido":
            continue

        producto = row[7].strip()

        pedidos.append(
            {
                "telefono": row[3].strip(),
                "nombre": row[4].strip(),
                "producto": producto,
                "fecha": f"{row[1]}T{row[2]}",
                "dias_duracion": get_duracion(producto),
                "f3": row[15].strip(),
                "f_final": row[16].strip(),
                "f_extra": row[17].strip(),
            }
        )

    print(f"[PEDIDOS OK] {len(pedidos)} pedidos")
    return pedidos