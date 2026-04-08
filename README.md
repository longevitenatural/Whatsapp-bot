# 🤖 WhatsApp AI Bot

Asistente virtual inteligente para WhatsApp construido con **FastAPI**, **Twilio**, **Supabase** y **Groq (LLaMA)**. Responde mensajes automáticamente con IA, guarda el historial de conversaciones y permite transferir a un agente humano.

---

## ✨ Funcionalidades

- 💬 Respuestas automáticas con IA (LLaMA 3.3 70B via Groq)
- 🧠 Memoria de conversación persistente en Supabase
- 👤 Handoff a agente humano con palabras clave
- 📱 Integración oficial con WhatsApp via Twilio
- 🚀 Listo para desplegar en Railway (producción 24/7)
- ⚙️ Personalizable para cualquier empresa

---

## 📋 Requisitos previos

Antes de empezar necesitas crear las siguientes cuentas:

| Servicio | URL | Plan |
|---|---|---|
| Twilio | twilio.com/try-twilio | Gratis ($15 crédito inicial) |
| Groq | console.groq.com | Gratis |
| Supabase | supabase.com | Gratis (500 MB) |
| Railway | railway.app | Gratis ($5/mes crédito) |
| GitHub | github.com | Gratis |

También necesitas tener instalado en tu computador:

- **Python 3.10+** — python.org/downloads
- **Git** — git-scm.com
- **VS Code** (recomendado) — code.visualstudio.com
- **ngrok** (para pruebas locales) — ngrok.com/download

---

## 🗂️ Estructura del proyecto

```
whatsapp-bot/
├── main.py           # Servidor principal FastAPI
├── database.py       # Conexión y funciones de Supabase
├── ai_engine.py      # Lógica de Groq + LLaMA
├── config.py         # Carga de variables de entorno
├── prompts.py        # System prompt personalizable
├── requirements.txt  # Dependencias del proyecto
├── Procfile          # Configuración para Railway
├── .env              # Credenciales (NUNCA subir a GitHub)
└── .gitignore        # Excluye archivos sensibles
```

---

## ⚙️ Instalación paso a paso

### 1. Clonar el repositorio

Abre tu terminal (cmd en Windows) y ejecuta:

```bash
git clone https://github.com/TU_USUARIO/whatsapp-bot.git
cd whatsapp-bot
```

### 2. Crear entorno virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar en Windows:
venv\Scripts\activate

# Activar en Mac/Linux:
source venv/bin/activate
```

Debes ver `(venv)` al inicio de la línea en tu terminal.

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Crear el archivo .env

Crea un archivo llamado `.env` en la raíz del proyecto. En Windows ejecuta:

```bash
notepad .env
```

Cuando pregunte si deseas crearlo di **Sí**. Pega este contenido con tus credenciales reales:

```env
# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_NUMBER=+14155238886

# Groq
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx

# Supabase
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Configuración del bot
EMPRESA_NOMBRE=Mi Empresa SA
MAX_HISTORIAL=20
PORT=8000
```

Guarda con **Ctrl + S**. Al guardar en el bloc de notas:
- Ve a **Archivo → Guardar como**
- Nombre: `.env`
- Tipo: **Todos los archivos (\*.\*)**
- Clic en **Guardar**

> ⚠️ **IMPORTANTE:** Nunca subas el archivo `.env` a GitHub. Contiene tus credenciales privadas.

---

## 🔑 Cómo obtener cada credencial

### Twilio
1. Ve a **console.twilio.com**
2. En la página principal (Console Home) encuentras:
   - **Account SID** — empieza con `AC...`
   - **Auth Token** — clic en el ojito para verlo
3. Para el número sandbox: ve a **Messaging → Try it out → Send a WhatsApp message**
   - El número sandbox de Twilio es siempre: `+14155238886`
   - Actívalo enviando el mensaje que indica Twilio desde tu WhatsApp

### Groq
1. Ve a **console.groq.com**
2. Menú izquierdo → **API Keys**
3. Clic en **Create API Key**
4. Copia la clave que empieza con `gsk_...`

### Supabase
1. Ve a tu proyecto en **supabase.com**
2. Menú izquierdo → **Settings → API**
3. Copia:
   - **Project URL** → va en `SUPABASE_URL`
   - **anon / public key** → va en `SUPABASE_KEY` (NO uses la service_role)

---

## 🗄️ Configurar la base de datos en Supabase

1. Ve a tu proyecto en Supabase
2. Menú izquierdo → **SQL Editor → New query**
3. Pega y ejecuta este SQL:

```sql
CREATE TABLE conversations (
  id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  phone      TEXT NOT NULL,
  role       TEXT NOT NULL CHECK (role IN ('user','assistant')),
  content    TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_phone ON conversations(phone);
CREATE INDEX idx_time  ON conversations(created_at);

CREATE TABLE users (
  phone     TEXT PRIMARY KEY,
  is_human  BOOLEAN DEFAULT FALSE,
  last_seen TIMESTAMPTZ DEFAULT NOW()
);
```

4. Clic en el botón verde **Run**
5. Debe aparecer: **Success. No rows returned** ✅

---

## 🎨 Personalizar el bot para tu empresa

Abre el archivo `prompts.py` y reemplaza los campos en mayúsculas con la información real de la empresa:

```python
INFORMACION DE LA EMPRESA:
- Servicios: [ESCRIBE AQUÍ LOS SERVICIOS Y PRECIOS REALES]
- Horario: [ESCRIBE EL HORARIO REAL]
- Teléfono: [ESCRIBE EL TELÉFONO REAL]
- Dirección: [ESCRIBE LA DIRECCIÓN REAL]
```

También cambia `EMPRESA_NOMBRE` en el archivo `.env`:

```env
EMPRESA_NOMBRE=Nombre Real de la Empresa
```

---

## 🧪 Probar en local con ngrok

### 1. Iniciar el servidor

```bash
python main.py
```

Debe aparecer:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 2. Abrir ngrok en otra terminal

```bash
ngrok http 8000
```

Copia la URL que aparece, algo como:
```
https://abc123def456.ngrok-free.app
```

### 3. Verificar que el servidor responde

Abre en el navegador:
```
https://abc123def456.ngrok-free.app/health
```

Debe mostrar:
```json
{"status": "ok", "bot": "Mi Empresa SA"}
```

### 4. Configurar webhook en Twilio

1. Ve a Twilio → **Messaging → Settings → WhatsApp Sandbox Settings**
2. En **"When a message comes in"** pega:
```
https://abc123def456.ngrok-free.app/webhook
```
3. Método: **HTTP POST**
4. Clic en **Save**

### 5. Probar desde WhatsApp

Envía un mensaje al número sandbox de Twilio **(+1 415 523 8886)** y el bot debe responder en segundos.

---

## 🚀 Desplegar en Railway (producción 24/7)

### 1. Subir código a GitHub

```bash
git init
git add .
git commit -m "WhatsApp AI Bot v1"
git remote add origin https://github.com/TU_USUARIO/whatsapp-bot.git
git branch -M main
git push -u origin main
```

> ⚠️ Para el push GitHub pedirá usuario y un **Personal Access Token** (no tu contraseña). Créalo en: GitHub → Settings → Developer settings → Personal access tokens → Generate new token → marca **repo** → Generate.

### 2. Crear proyecto en Railway

1. Ve a **railway.app** → Login with GitHub
2. Clic en **New Project → Deploy from GitHub repo**
3. Selecciona tu repositorio **whatsapp-bot**
4. Espera 2-3 minutos

### 3. Agregar variables de entorno en Railway

1. En tu proyecto → pestaña **Variables**
2. Agrega exactamente las mismas variables que tienes en tu `.env`:

```
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_WHATSAPP_NUMBER
GROQ_API_KEY
SUPABASE_URL
SUPABASE_KEY
EMPRESA_NOMBRE
MAX_HISTORIAL
PORT
```

### 4. Obtener URL de producción

1. En Railway → **Settings → Domains → Generate Domain**
2. Te da una URL como: `whatsapp-bot-production-xxxx.up.railway.app`

### 5. Verificar que funciona

Abre en el navegador:
```
https://whatsapp-bot-production-xxxx.up.railway.app/health
```

Debe mostrar:
```json
{"status": "ok", "bot": "Mi Empresa SA"}
```

### 6. Actualizar webhook en Twilio

Ve a Twilio → WhatsApp Sandbox Settings y reemplaza la URL de ngrok por:
```
https://whatsapp-bot-production-xxxx.up.railway.app/webhook
```

---

## 👤 Gestión del modo humano

Cuando un usuario escribe **"humano"**, **"asesor"**, **"persona"** o **"agente"** el bot se desactiva y espera que un asesor real atienda.

Para reactivar el bot después de que el asesor termine, ejecuta en Supabase → SQL Editor:

```sql
UPDATE users SET is_human = FALSE WHERE phone = 'whatsapp:+57XXXXXXXXXX';
```

Reemplaza `+57XXXXXXXXXX` con el número real del usuario.

---

## 📊 Consultas útiles en Supabase

```sql
-- Ver todas las conversaciones de hoy
SELECT * FROM conversations
WHERE created_at >= CURRENT_DATE
ORDER BY created_at DESC;

-- Ver usuarios en modo humano (esperando asesor)
SELECT phone, last_seen FROM users
WHERE is_human = TRUE;

-- Ver los usuarios más activos
SELECT phone, COUNT(*) as mensajes
FROM conversations
WHERE role = 'user'
GROUP BY phone
ORDER BY mensajes DESC
LIMIT 10;
```

---

## 🔄 Actualizar el bot después de cambios

Cada vez que modifiques el código ejecuta:

```bash
git add .
git commit -m "descripción del cambio"
git push
```

Railway despliega automáticamente los cambios en 1-2 minutos.

---

## ❗ Errores comunes

| Error | Causa | Solución |
|---|---|---|
| `supabase_url is required` | `.env` no tiene las credenciales | Verifica que el `.env` esté bien creado |
| `supabase.com vs supabase.co` | URL incorrecta | La URL termina en `.co` no `.com` |
| `getaddrinfo failed` | Sin conexión a Supabase | Verifica la URL y la KEY de Supabase |
| Bot no responde en WhatsApp | Webhook mal configurado | Verifica la URL en Twilio Sandbox Settings |
| `TypeError: NoneType` | Variable de entorno vacía | Verifica que todas las variables estén en `.env` |

---

## 📞 Soporte

Si tienes problemas con la implementación contacta al desarrollador.

---

## 📄 Licencia

Este proyecto es de uso privado. No está permitida su redistribución sin autorización del autor.
