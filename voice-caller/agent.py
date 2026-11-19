"""Agente de voz que hace llamadas de venta por teléfono (LiveKit + SIP).

Modos:
    python agent.py console   -> prueba con tu micrófono, sin teléfono ni hoja
    python agent.py dev       -> worker conectado a LiveKit Cloud, espera llamadas de dialer.py
    python agent.py start     -> igual que dev, para producción
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from livekit import api
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RoomInputOptions,
    RunContext,
    WorkerOptions,
    cli,
    function_tool,
    get_job_context,
)
from livekit.plugins import anthropic, deepgram, elevenlabs, silero

import sheets
from prompts import construir_instrucciones, saludo_inicial

load_dotenv()
logger = logging.getLogger("vendedor")
logger.setLevel(logging.INFO)

AGENT_NAME = os.getenv("AGENT_NAME", "vendedor-telefonico")
TRANSCRIPCIONES = Path(__file__).parent / "transcripciones"

RESULTADOS = {
    "interesado",        # quiere más información / propuesta
    "cita_agendada",     # se acordó una cita o demostración
    "venta_cerrada",     # aceptó contratar
    "volver_a_llamar",   # no era buen momento, pidió que se le llame después
    "no_interesado",
    "no_llamar",         # pidió no volver a ser contactado
    "buzon_de_voz",
    "numero_equivocado",
}

CONTACTO_DEMO = {"nombre": "Daniel", "empresa": "Comercial Demo", "ciudad": "Bogotá"}


class Vendedor(Agent):
    def __init__(self, contacto: dict, fila: int | None):
        super().__init__(instructions=construir_instrucciones(contacto))
        self.contacto = contacto
        self.fila = fila
        self.resultado: str | None = None
        self.notas = ""

    @function_tool()
    async def registrar_resultado(self, ctx: RunContext, resultado: str, notas: str) -> str:
        """Guarda el resultado de la llamada. Llámala una vez, justo antes de terminar la llamada.

        Args:
            resultado: Uno de: interesado, cita_agendada, venta_cerrada, volver_a_llamar,
                no_interesado, no_llamar, buzon_de_voz, numero_equivocado.
            notas: Resumen de 1 a 3 frases: qué necesita, objeciones, fecha/hora acordada
                para la cita o para volver a llamar, y cualquier dato útil para el asesor.
        """
        resultado = resultado.strip().lower()
        if resultado not in RESULTADOS:
            return f"Resultado inválido. Usa uno de: {', '.join(sorted(RESULTADOS))}"
        self.resultado, self.notas = resultado, notas
        logger.info("resultado=%s notas=%s", resultado, notas)
        if self.fila:
            await asyncio.to_thread(
                sheets.actualizar, self.fila, estado="completada", resultado=resultado, notas=notas
            )
        return "Resultado guardado. Despídete brevemente y termina la llamada."

    @function_tool()
    async def terminar_llamada(self, ctx: RunContext) -> None:
        """Cuelga el teléfono. Úsala después de despedirte (o de inmediato si es un buzón de voz)."""
        await ctx.wait_for_playout()
        await colgar()


async def colgar() -> None:
    ctx = get_job_context()
    await ctx.api.room.delete_room(api.DeleteRoomRequest(room=ctx.room.name))


async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()

    datos = json.loads(ctx.job.metadata) if ctx.job.metadata else {}
    telefono = datos.get("telefono")
    fila = datos.get("fila")
    contacto = datos.get("contacto") or CONTACTO_DEMO

    agente = Vendedor(contacto, fila)
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-3", language=os.getenv("IDIOMA_STT", "es")),
        llm=anthropic.LLM(model=os.getenv("CLAUDE_MODEL", "claude-opus-5-5")),
        tts=elevenlabs.TTS(
            voice_id=os.environ.get("ELEVEN_VOICE_ID", "hpp4J3VqNfWAUOO0d1Us"),
            model="eleven_flash_v2_5",
            language="es",
        ),
    )

    async def al_terminar() -> None:
        # Guarda la transcripción y, si el agente no registró resultado, lo marca para revisión.
        try:
            TRANSCRIPCIONES.mkdir(exist_ok=True)
            nombre = f"{datetime.now():%Y%m%d-%H%M%S}-fila{fila or 'demo'}.json"
            (TRANSCRIPCIONES / nombre).write_text(
                json.dumps(session.history.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            logger.exception("no se pudo guardar la transcripción")
        if fila and agente.resultado is None:
            await asyncio.to_thread(
                sheets.actualizar, fila, estado="completada", resultado="sin_resultado",
                notas="La llamada terminó sin que el agente registrara resultado (colgó la persona o hubo un corte).",
            )

    ctx.add_shutdown_callback(al_terminar)

    opciones_entrada = RoomInputOptions()
    try:
        from livekit.plugins import noise_cancellation  # solo funciona con LiveKit Cloud
        opciones_entrada = RoomInputOptions(noise_cancellation=noise_cancellation.BVCTelephony())
    except Exception:
        pass

    if not telefono:
        # Modo prueba (console): no se marca a nadie.
        await session.start(agent=agente, room=ctx.room, room_input_options=opciones_entrada)
        await session.generate_reply(instructions=saludo_inicial(contacto))
        return

    inicio_sesion = asyncio.create_task(
        session.start(agent=agente, room=ctx.room, room_input_options=opciones_entrada)
    )
    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=os.environ["SIP_OUTBOUND_TRUNK_ID"],
                sip_call_to=telefono,
                participant_identity=telefono,
                wait_until_answered=True,
            )
        )
    except api.TwirpError as e:
        estado_sip = f"{e.metadata.get('sip_status_code', '')} {e.metadata.get('sip_status', '')}".strip()
        logger.error("no se pudo llamar a %s: %s (%s)", telefono, e.message, estado_sip)
        if fila:
            agente.resultado = "no_contesto"
            await asyncio.to_thread(
                sheets.actualizar, fila, estado="completada", resultado="no_contesto",
                notas=f"No contestó o falló la llamada: {estado_sip or e.message}",
            )
        ctx.shutdown()
        return

    await inicio_sesion
    await ctx.wait_for_participant(identity=telefono)
    await session.generate_reply(instructions=saludo_inicial(contacto))


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name=AGENT_NAME))
