# Vendedor telefónico con IA (LiveKit + Claude)

Un agente de voz que **llama por teléfono** a los contactos de una **hoja de Google Sheets** y
**vende un servicio** usando la información de una **base de conocimiento** (carpeta `kb/`).
Al terminar cada llamada escribe en la hoja el resultado y un resumen.

```
Google Sheets ──► dialer.py ──(dispatch)──► LiveKit Cloud ──SIP──► Twilio/Telnyx ──► teléfono
      ▲                                         │
      └───────── resultado + notas ◄──── agent.py (Deepgram → Claude → ElevenLabs)
```

| Archivo | Qué hace |
|---|---|
| `agent.py` | El agente: marca el número, conversa y registra el resultado. |
| `dialer.py` | Lee la hoja y lanza las llamadas una por una, en horario permitido. |
| `prompts.py` | Personalidad, reglas de venta y carga de la base de conocimiento. |
| `sheets.py` | Lectura y escritura en Google Sheets. |
| `kb/` | Información del servicio (`.md` o `.txt`). **Reemplaza el ejemplo.** |

## 1. Instalación

```bash
cd voice-caller
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # y llena las claves
```

Cuentas que necesitas:
- **LiveKit Cloud** (cloud.livekit.io, plan gratis): URL, API key y secret.
- **Anthropic** (API key de Claude).
- **Deepgram** (voz a texto) y **ElevenLabs** (texto a voz; elige una voz en español y copia su ID).
- **Twilio o Telnyx** con un número de teléfono (para marcar).
- **Google Cloud**: una cuenta de servicio con acceso a la hoja.

## 2. Prueba sin teléfono (empieza aquí)

```bash
python agent.py console
```

Hablas con el vendedor por el micrófono de tu computadora, sin hoja ni llamadas. Úsalo para
ajustar la base de conocimiento y el tono. Las transcripciones se guardan en `transcripciones/`.

## 3. Conectar el teléfono (trunk SIP de salida)

1. En Twilio: *Elastic SIP Trunking* → crea un trunk, en **Termination** define un URI
   (p. ej. `mi-trunk.pstn.twilio.com`) y una credencial (usuario y contraseña). Asocia tu número al trunk.
   (En Telnyx es equivalente: una *SIP Connection* con credenciales y tu número.)
2. Instala la CLI de LiveKit (`lk`) y crea `outbound-trunk.json`:
   ```json
   {
     "trunk": {
       "name": "salida",
       "address": "mi-trunk.pstn.twilio.com",
       "numbers": ["+52XXXXXXXXXX"],
       "authUsername": "usuario",
       "authPassword": "contraseña"
     }
   }
   ```
3. `lk sip outbound create outbound-trunk.json` → copia el ID (`ST_...`) a `SIP_OUTBOUND_TRUNK_ID` en `.env`.

## 4. Preparar la hoja de Google Sheets

1. En Google Cloud Console: crea un proyecto, activa **Google Sheets API**, crea una
   **cuenta de servicio** y descarga su llave JSON como `service-account.json` en esta carpeta.
2. Crea la hoja (puedes importar `contactos_plantilla.csv`) y **compártela como Editor** con el
   correo de la cuenta de servicio (`...@...iam.gserviceaccount.com`).
3. Copia el ID de la hoja (lo que va entre `/d/` y `/edit` en la URL) a `GOOGLE_SHEET_ID`.

Columnas: `nombre`, `telefono` y las que quieras (`empresa`, `ciudad`, etc.; el agente las usa
como contexto). Las columnas `estado`, `resultado`, `notas`, `intentos` y `ultima_llamada` las llena el sistema
(si faltan, se crean solas).

## 5. Primera llamada real

En una terminal, el worker:
```bash
python agent.py dev
```
En otra, revisa a quién llamaría y luego llama **solo a tu propio número** (pon tu número en la fila 2):
```bash
python dialer.py --dry-run
python dialer.py --fila 2 --ignorar-horario
```
Cuando funcione, corre la lista: `python dialer.py --limite 5` y después `python dialer.py`.

## Resultados posibles en la hoja

`interesado`, `cita_agendada`, `venta_cerrada`, `volver_a_llamar`, `no_interesado`, `no_llamar`,
`buzon_de_voz`, `numero_equivocado`, `no_contesto`, `sin_resultado`, `numero_invalido`.

`volver_a_llamar`, `no_contesto` y `sin_resultado` se vuelven a intentar en la siguiente corrida
(hasta `MAX_INTENTOS`). Las personas marcadas como `no_llamar` no vuelven a recibir llamadas.

## Ajustes

- **Latencia**: el modelo se elige con `CLAUDE_MODEL`. Si las respuestas tardan demasiado en la llamada, prueba
  `claude-sonnet-5-5` o `claude-haiku-5-5`.
- **Horario**: `HORA_INICIO`, `HORA_FIN` y `ZONA_HORARIA` (lunes a sábado).
- **Personaje**: `NOMBRE_VENDEDOR` y `NOMBRE_EMPRESA`. Las reglas de venta están en `prompts.py`.
- **Base de conocimiento**: va completa dentro de las instrucciones. Funciona bien hasta unas
  decenas de páginas; si crece mucho, conviene una búsqueda (RAG).

## Aviso legal

Las llamadas automatizadas con IA están reguladas (p. ej. TCPA en EE. UU.; en México, el REPEP de
PROFECO y la ley de protección de datos). Llama solo a contactos con consentimiento, respeta los
horarios y las solicitudes de no llamar. El agente dice que es una asistente virtual si se lo preguntan.
