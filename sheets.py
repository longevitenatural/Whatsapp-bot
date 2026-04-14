import httpx
import csv
import io
import json
from datetime import datetime

SHEET_ID = "1Cg1SBYIq2kiPYI-D8mKKlvt1dLC8Zz045jIWpK3Ho0k"
BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxfoPaC6rB2fQCaZWERSI9ucaIlX6JpbWNU_UBX_hGnoFdkqysKCCMgcy3XzLsspMdt/exec"


# =============================
# 📦 CATALOGO
# Estructura real en Sheets:
# A=CODIGO | B=PRODUCTO | C=DESCRIPCIÓN | D=PRECIO | E=ESTADO
# =============================
async def get_catalogo() -> str:
    url = BASE_URL + "&sheet=Catalogo"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10)

    reader = csv.reader(io.StringIO(response.text))
    rows = list(reader)

    productos = []

    for row in rows:
        if len(row) < 5:
            continue

        codigo      = str(row[0]).strip()
        producto    = str(row[1]).strip()
        descripcion = str(row[2]).strip()
        precio_raw  = str(row[3]).strip()
        estado      = str(row[4]).strip().lower()

        # Saltar encabezados y filas vacías
        if not codigo or codigo.upper() in ("CODIGO", "CATÁLOGO", "CATALOGO"):
            continue

        # Solo productos activos
        if estado != "activo":
            continue

        # Formatear precio
        try:
            precio_num = int(precio_raw.replace("$", "").replace(".", "").replace(",", "").strip())
            precio_fmt = "${:,}".format(precio_num).replace(",", ".")
        except Exception:
            precio_fmt = precio_raw

        # Construir línea del catálogo
        linea = f"- {producto} | Código: {codigo} | Precio: {precio_fmt}"
        if descripcion:
            linea += f" | Descripción: {descripcion}"

        productos.append(linea)

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
    identificacion: str,
    codigo: str,
    producto: str,
    cantidad: int,
    precio: int,
    direccion: str,
    barrio: str,
    ciudad: str,
) -> bool:

    try:
        now = datetime.now()
        total = cantidad * precio

        data = {
            "telefono":       telefono,
            "nombre":         nombre,
            "identificacion": identificacion,
            "codigo":         codigo,
            "producto":       producto,
            "cantidad":       cantidad,
            "precio":         precio,
            "total":          total,
            "direccion":      direccion,
            "barrio":         barrio,
            "ciudad":         ciudad,
            "fecha":          now.strftime("%Y-%m-%d"),
            "hora":           now.strftime("%H:%M:%S"),
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
        if len(row) < 14 or row[0] in ("# Pedido", ""):
            continue

        pedidos.append({
            "telefono": row[3].strip(),
            "nombre":   row[4].strip(),
            "producto": row[6].strip(),
            "fecha":    f"{row[1]}T{row[2]}",
            "f3":       row[14].strip() if len(row) > 14 else "",
            "f_final":  row[15].strip() if len(row) > 15 else "",
        })

    print(f"[PEDIDOS OK] {len(pedidos)} pedidos")
    return pedidos