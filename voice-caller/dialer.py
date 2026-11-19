"""Lee la hoja de Google Sheets y lanza una llamada por cada contacto pendiente.

Uso:
    python dialer.py --dry-run          # muestra a quién llamaría, sin llamar
    python dialer.py --fila 2           # llama solo a la fila 2 (ideal para la primera prueba)
    python dialer.py --limite 5         # llama a los primeros 5 pendientes
"""

import argparse
import asyncio
import json
import os
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from livekit import api

import sheets

load_dotenv()

AGENT_NAME = os.getenv("AGENT_NAME", "vendedor-telefonico")
ZONA = ZoneInfo(os.getenv("ZONA_HORARIA", "America/Bogota"))
HORA_INICIO = int(os.getenv("HORA_INICIO", "8"))
HORA_FIN = int(os.getenv("HORA_FIN", "18"))
HORA_FIN_SABADO = int(os.getenv("HORA_FIN_SABADO", "15"))
PAUSA = int(os.getenv("PAUSA_ENTRE_LLAMADAS", "10"))
MAX_INTENTOS = int(os.getenv("MAX_INTENTOS", "3"))
ESPERA_MAXIMA = 15 * 60  # segundos que esperamos a que termine una llamada

LLAMAR_DE_NUEVO = {"", "pendiente", "volver_a_llamar", "no_contesto", "sin_resultado"}


def normalizar(telefono: str) -> str | None:
    """Convierte a formato E.164 (+57...). Usa PREFIJO_PAIS si el número no trae '+'."""
    t = re.sub(r"[^\d+]", "", str(telefono))
    if not t:
        return None
    if not t.startswith("+"):
        t = os.getenv("PREFIJO_PAIS", "+57") + t
    return t if re.fullmatch(r"\+\d{8,15}", t) else None


def en_horario() -> bool:
    ahora = datetime.now(ZONA)
    if ahora.weekday() == 6:  # domingo: no se llama
        return False
    fin = min(HORA_FIN, HORA_FIN_SABADO) if ahora.weekday() == 5 else HORA_FIN
    return HORA_INICIO <= ahora.hour < fin


def pendientes(solo_fila: int | None) -> list[tuple[int, dict]]:
    salida = []
    for fila, c in sheets.leer_contactos():
        if solo_fila and fila != solo_fila:
            continue
        estado = str(c.get("estado", "")).strip().lower()
        resultado = str(c.get("resultado", "")).strip().lower()
        intentos = int(c.get("intentos") or 0)
        if resultado == "no_llamar":
            if solo_fila:
                print(f"  fila {fila}: pidió no ser llamado, se omite")
            continue
        if solo_fila:
            salida.append((fila, c))  # si pides una fila concreta, se llama aunque ya tenga estado
        elif estado in {"", "pendiente"} or (estado == "completada" and resultado in LLAMAR_DE_NUEVO and intentos < MAX_INTENTOS):
            salida.append((fila, c))
    return salida


async def lanzar_llamada(lk: api.LiveKitAPI, fila: int, contacto: dict, telefono: str) -> None:
    sala = f"llamada-fila{fila}-{int(time.time())}"
    metadata = {"fila": fila, "telefono": telefono, "contacto": contacto}
    await lk.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(agent_name=AGENT_NAME, room=sala, metadata=json.dumps(metadata, ensure_ascii=False))
    )


async def esperar_fin(fila: int) -> str:
    inicio = time.time()
    while time.time() - inicio < ESPERA_MAXIMA:
        await asyncio.sleep(5)
        datos = await asyncio.to_thread(sheets.leer_fila, fila)
        if datos.get("estado") != "llamando":
            return datos.get("resultado", "")
    await asyncio.to_thread(sheets.actualizar, fila, estado="completada", resultado="sin_resultado",
                            notas="Tiempo de espera agotado; revisar el worker.")
    return "sin_resultado"


async def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="no llama, solo muestra la lista")
    p.add_argument("--fila", type=int, help="llamar solo a esta fila de la hoja")
    p.add_argument("--limite", type=int, default=0, help="máximo de llamadas en esta corrida")
    p.add_argument("--ignorar-horario", action="store_true")
    args = p.parse_args()

    sheets.asegurar_columnas()
    lista = pendientes(args.fila)
    if args.limite:
        lista = lista[: args.limite]
    print(f"{len(lista)} contacto(s) por llamar")

    lk = None if args.dry_run else api.LiveKitAPI()
    try:
        for fila, contacto in lista:
            telefono = normalizar(contacto.get("telefono", ""))
            nombre = contacto.get("nombre", "")
            if not telefono:
                print(f"  fila {fila}: teléfono inválido ({contacto.get('telefono')!r}), se omite")
                sheets.actualizar(fila, estado="completada", resultado="numero_invalido")
                continue
            if args.dry_run:
                print(f"  fila {fila}: {nombre} {telefono}")
                continue
            if not args.ignorar_horario and not en_horario():
                print(f"Fuera de horario ({HORA_INICIO}:00-{HORA_FIN}:00 {ZONA}). Me detengo.")
                break

            intentos = int(contacto.get("intentos") or 0) + 1
            sheets.actualizar(fila, estado="llamando", resultado="", intentos=intentos, ultima_llamada=sheets.ahora())
            print(f"  fila {fila}: llamando a {nombre} {telefono} (intento {intentos})...", flush=True)
            await lanzar_llamada(lk, fila, contacto, telefono)
            resultado = await esperar_fin(fila)
            print(f"  fila {fila}: {resultado}")
            await asyncio.sleep(PAUSA)
    finally:
        if lk:
            await lk.aclose()


if __name__ == "__main__":
    asyncio.run(main())
