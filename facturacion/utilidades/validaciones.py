"""Validaciones de datos de entrada: NIT, correo y cantidades."""

from __future__ import annotations

import re

_RE_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# NIT generico para ventas a quien no da sus datos.
NIT_CONSUMIDOR_FINAL = "222222222222"


def normalizar_nit(nit: str | None) -> str:
    """Quita formato del NIT para comparar duplicados sin importar puntos, espacios o guion."""
    return "".join(ch for ch in (nit or "") if ch.isdigit())


def validar_nit(nit: str) -> bool:
    """Acepta NIT con o sin separadores y con dígito de verificación opcional."""
    limpio = normalizar_nit(nit)
    if limpio == NIT_CONSUMIDOR_FINAL:
        return True

    numero, _, dv = (nit or "").replace(".", "").replace(" ", "").partition("-")
    if not numero.isdigit() or not 6 <= len(numero) <= 15:
        return False
    if dv and not dv.isdigit():
        return False
    return True


def validar_correo(correo: str | None) -> bool:
    return bool(_RE_CORREO.match(correo or ""))


def validar_cantidad(cantidad: object) -> bool:
    """Una cantidad vendible es un entero positivo. `True` no cuenta como 1."""
    return isinstance(cantidad, int) and not isinstance(cantidad, bool) and cantidad > 0
