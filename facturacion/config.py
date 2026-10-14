"""Configuracion de la facturacion, leida del entorno con valores por defecto.

Nada de valores de negocio escritos en el codigo de los servicios: la serie, el
IVA, los tiempos de espera del servicio de impuestos y los datos del emisor viven
aqui y se pueden cambiar por variable de entorno sin tocar nada mas.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping


@dataclass(frozen=True)
class Configuracion:
    # Serie de las facturas y de las notas de credito.
    serie_facturas: str = "FV"
    serie_notas_credito: str = "NC"
    # Tasa general de IVA. Cada producto puede tener la suya (0 % para exentos).
    tasa_iva_general: Decimal = Decimal("0.19")
    # Tiempo maximo que se espera al servicio de impuestos en cada intento, y cuantos
    # intentos se hacen antes de dar el timbrado por fallido.
    timeout_timbrado_s: float = 1.5
    reintentos_timbrado: int = 2
    # Plazo legal para anular una factura timbrada.
    dias_maximos_anulacion: int = 30
    # Datos del emisor que van en el XML y en el PDF.
    nit_emisor: str = "900123456"
    razon_social_emisor: str = "Tienda Ejemplo S.A.S."
    remitente_correo: str = "facturacion@tienda.example"
    # Cuentas contables usadas por la exportacion de ventas.
    cuenta_caja: str = "110505"
    cuenta_bancos: str = "111005"
    cuenta_ingresos: str = "413524"
    cuenta_iva: str = "240802"
    cuenta_clientes: str = "130505"

    @classmethod
    def _leer_cuenta(cls, entorno: Mapping[str, str], nombre: str, por_defecto: str) -> str:
        valor = entorno.get(nombre, por_defecto)
        if valor == "" or not valor.isdigit():
            raise ValueError(f"La variable {nombre} es invalida: debe contener solo digitos.")
        return valor

    @classmethod
    def desde_entorno(cls, entorno: Mapping[str, str] | None = None) -> "Configuracion":
        """Lee la configuracion de las variables FACTURACION_*; lo que falte, por defecto."""
        e = os.environ if entorno is None else entorno
        base = cls()
        return cls(
            serie_facturas=e.get("FACTURACION_SERIE", base.serie_facturas),
            serie_notas_credito=e.get("FACTURACION_SERIE_NC", base.serie_notas_credito),
            tasa_iva_general=Decimal(e.get("FACTURACION_IVA", str(base.tasa_iva_general))),
            timeout_timbrado_s=float(e.get("FACTURACION_TIMEOUT_TIMBRADO_S", base.timeout_timbrado_s)),
            reintentos_timbrado=int(e.get("FACTURACION_REINTENTOS_TIMBRADO", base.reintentos_timbrado)),
            dias_maximos_anulacion=int(e.get("FACTURACION_DIAS_ANULACION", base.dias_maximos_anulacion)),
            nit_emisor=e.get("FACTURACION_NIT_EMISOR", base.nit_emisor),
            razon_social_emisor=e.get("FACTURACION_RAZON_SOCIAL", base.razon_social_emisor),
            remitente_correo=e.get("FACTURACION_REMITENTE", base.remitente_correo),
            cuenta_caja=cls._leer_cuenta(e, "FACTURACION_CUENTA_CAJA", base.cuenta_caja),
            cuenta_bancos=cls._leer_cuenta(e, "FACTURACION_CUENTA_BANCOS", base.cuenta_bancos),
            cuenta_ingresos=cls._leer_cuenta(e, "FACTURACION_CUENTA_INGRESOS", base.cuenta_ingresos),
            cuenta_iva=cls._leer_cuenta(e, "FACTURACION_CUENTA_IVA", base.cuenta_iva),
            cuenta_clientes=cls._leer_cuenta(e, "FACTURACION_CUENTA_CLIENTES", base.cuenta_clientes),
        )
