"""Validaciones de datos de entrada: NIT, correo y cantidades."""

from __future__ import annotations

import re

_RE_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Pesos del digito de verificacion del NIT colombiano, de derecha a izquierda.
_PESOS_NIT = (3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71)

# NIT generico para ventas a quien no da sus datos.
NIT_CONSUMIDOR_FINAL = "222222222222"


def normalizar_nit(nit: str | None) -> str:
    """Quita formato del NIT para comparar duplicados sin importar puntos, espacios o guion."""
    return "".join(ch for ch in (nit or "") if ch.isdigit())


def digito_verificacion(nit: str) -> int:
    """Digito de verificacion de un NIT sin guion ni puntos."""
    digitos = [int(d) for d in reversed(nit)]
    suma = sum(d * p for d, p in zip(digitos, _PESOS_NIT))
    residuo = suma % 11
    return residuo if residuo < 2 else 11 - residuo


def validar_nit(nit: str) -> bool:
    """Acepta `900123456` o `900123456-8`; si trae digito de verificacion, lo comprueba."""
    limpio = normalizar_nit(nit)
    if limpio == NIT_CONSUMIDOR_FINAL:
        return True
    numero, _, dv = (nit or "").replace(".", "").replace(" ", "").partition("-")
    if not numero.isdigit() or not 6 <= len(numero) <= 15:
        return False
    if dv:
        return dv.isdigit() and int(dv) == digito_verificacion(numero)
    return True


def validar_correo(correo: str | None) -> bool:
    return bool(_RE_CORREO.match(correo or ""))


def validar_cantidad(cantidad: object) -> bool:
    """Una cantidad vendible es un entero positivo. `True` no cuenta como 1."""
    return isinstance(cantidad, int) and not isinstance(cantidad, bool) and cantidad > 0
