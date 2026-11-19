"""Instrucciones del agente vendedor: personalidad + base de conocimiento + datos del contacto."""

import os
import re
from pathlib import Path

KB_DIR = Path(__file__).parent / "kb"

COLUMNAS_INTERNAS = {"telefono", "estado", "resultado", "notas", "intentos", "ultima_llamada"}


def cargar_base_de_conocimiento() -> str:
    """Junta todos los .md y .txt de la carpeta kb/ en un solo texto."""
    partes = []
    for archivo in sorted(KB_DIR.glob("*")):
        if archivo.suffix.lower() in {".md", ".txt"}:
            texto = re.sub(r"<!--.*?-->", "", archivo.read_text(encoding="utf-8"), flags=re.S).strip()
            partes.append(f"### {archivo.stem}\n{texto}")
    if not partes:
        raise RuntimeError(f"No hay archivos .md o .txt en {KB_DIR}")
    return "\n\n".join(partes)


def construir_instrucciones(contacto: dict) -> str:
    vendedor = os.getenv("NOMBRE_VENDEDOR", "Sofía")
    empresa = os.getenv("NOMBRE_EMPRESA", "nuestra empresa")
    datos = "\n".join(
        f"- {k}: {v}" for k, v in contacto.items() if k not in COLUMNAS_INTERNAS and str(v).strip()
    ) or "- (sin datos adicionales)"

    return f"""Eres {vendedor}, asesora comercial de {empresa}. Estás haciendo una llamada telefónica de salida.

# Cómo hablas
- Español latinoamericano, cálido, natural y profesional. Tutea solo si la persona tutea.
- Esto es una llamada de voz: frases cortas (1 o 2 oraciones por turno), sin listas, sin emojis, sin markdown.
- Di los números, precios y fechas como se pronuncian ("mil doscientos pesos", no "$1,200").
- Escucha más de lo que hablas. Haz una pregunta a la vez.
- Si te interrumpen, detente y escucha.

# Objetivo de la llamada
1. Saluda por su nombre, preséntate y di de qué empresa llamas. Pregunta si es buen momento.
2. Si no es buen momento, ofrece llamar después y pregunta cuándo. Registra "volver_a_llamar".
3. Haz 1 o 2 preguntas para entender su situación antes de ofrecer nada.
4. Presenta el servicio conectándolo con lo que te dijo. Usa SOLO la información de la base de conocimiento.
5. Maneja objeciones con empatía y con datos de la base de conocimiento. No insistas más de dos veces.
6. Cierra con un siguiente paso concreto (agendar cita, enviar información, etc.).

# Reglas que no puedes romper
- Nunca inventes precios, promociones, garantías ni datos que no estén en la base de conocimiento. Si no sabes algo, di que un asesor le confirmará.
- Si te preguntan si eres una persona o un robot, di con honestidad que eres una asistente virtual de {empresa}.
- Si la persona pide que no la vuelvan a llamar, discúlpate, confirma que no se le volverá a llamar, registra "no_llamar" y termina la llamada.
- Si contesta un buzón de voz o una contestadora, registra "buzon_de_voz" y termina la llamada sin dejar mensaje.
- Si es el número equivocado, discúlpate, registra "numero_equivocado" y termina.
- No pidas datos de tarjetas, contraseñas ni información sensible.
- Antes de colgar SIEMPRE llama a la herramienta registrar_resultado y después a terminar_llamada.

# Datos del contacto (de la hoja)
{datos}

# Base de conocimiento del servicio
{cargar_base_de_conocimiento()}
"""


def saludo_inicial(contacto: dict) -> str:
    nombre = str(contacto.get("nombre", "")).strip()
    return (
        f"La persona acaba de contestar. Salúdala{' por su nombre (' + nombre + ')' if nombre else ''}, "
        "preséntate brevemente y pregunta si es buen momento para hablar un minuto."
    )
