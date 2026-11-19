"""Lectura y escritura de la hoja de Google Sheets con los contactos.

La primera fila de la hoja son los encabezados. Columnas que usa el sistema:
    nombre, telefono, estado, resultado, notas, intentos, ultima_llamada
Cualquier otra columna (empresa, ciudad, producto_actual...) se le pasa al
agente como contexto del contacto.
"""

import os
from datetime import datetime

import gspread

COLUMNAS_SISTEMA = ["nombre", "telefono", "estado", "resultado", "notas", "intentos", "ultima_llamada"]


def _hoja() -> gspread.Worksheet:
    gc = gspread.service_account(filename=os.environ["GOOGLE_SERVICE_ACCOUNT_FILE"])
    libro = gc.open_by_key(os.environ["GOOGLE_SHEET_ID"])
    pestana = os.getenv("GOOGLE_SHEET_TAB")
    return libro.worksheet(pestana) if pestana else libro.sheet1


def asegurar_columnas() -> None:
    """Agrega al final de la fila 1 las columnas del sistema que falten."""
    hoja = _hoja()
    encabezados = hoja.row_values(1)
    faltan = [c for c in COLUMNAS_SISTEMA if c not in encabezados]
    if faltan:
        inicio = len(encabezados) + 1
        if hoja.col_count < inicio + len(faltan) - 1:
            hoja.add_cols(inicio + len(faltan) - 1 - hoja.col_count)
        for i, col in enumerate(faltan):
            hoja.update_cell(1, inicio + i, col)


def leer_contactos() -> list[tuple[int, dict]]:
    """Devuelve [(numero_de_fila, {columna: valor}), ...]."""
    registros = _hoja().get_all_records(default_blank="")
    return [(i + 2, {k.strip().lower(): v for k, v in r.items()}) for i, r in enumerate(registros)]


def leer_fila(fila: int) -> dict:
    hoja = _hoja()
    encabezados = [h.strip().lower() for h in hoja.row_values(1)]
    valores = hoja.row_values(fila)
    valores += [""] * (len(encabezados) - len(valores))
    return dict(zip(encabezados, valores))


def actualizar(fila: int, **campos) -> None:
    """Escribe los campos dados en la fila (solo columnas que existan)."""
    hoja = _hoja()
    encabezados = [h.strip().lower() for h in hoja.row_values(1)]
    celdas = []
    for clave, valor in campos.items():
        if clave in encabezados:
            celdas.append(gspread.Cell(fila, encabezados.index(clave) + 1, str(valor)))
    if celdas:
        hoja.update_cells(celdas)


def ahora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")
