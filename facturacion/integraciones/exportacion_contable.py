"""Exportacion de las ventas al sistema contable, en CSV.

Un asiento por factura: debito a caja o bancos segun el medio de pago, credito a
ingresos por el subtotal neto y credito a IVA por pagar por el impuesto. El
contador importa este archivo al cierre del mes.
"""

from __future__ import annotations

import csv
import io
from datetime import date

from facturacion.config import Configuracion
from facturacion.modelos import EstadoFactura, Factura, MedioPago
from facturacion.repositorios.memoria import RepositorioFacturas
from facturacion.utilidades.dinero import redondear

COLUMNAS = ("fecha", "comprobante", "cuenta", "tercero", "debito", "credito")


def _cuenta_de_cobro(factura: Factura, medio: MedioPago, config: Configuracion) -> str:
    return config.cuenta_caja if medio == MedioPago.EFECTIVO else config.cuenta_bancos


def asientos(factura: Factura, *, config: Configuracion) -> list[dict[str, str]]:
    """Las lineas contables de una factura. Debitos y creditos siempre cuadran."""
    fecha = factura.fecha_emision.date().isoformat() if factura.fecha_emision else ""
    base = {"fecha": fecha, "comprobante": factura.identificador, "tercero": factura.cliente.nit}
    filas = []
    for pago in factura.pagos:
        filas.append({
            **base,
            "cuenta": _cuenta_de_cobro(factura, pago.medio, config),
            "debito": str(pago.monto),
            "credito": "0",
        })
    if factura.saldo > 0:
        filas.append({**base, "cuenta": config.cuenta_clientes, "debito": str(factura.saldo), "credito": "0"})
    filas.append({**base, "cuenta": config.cuenta_ingresos, "debito": "0",
                  "credito": str(redondear(factura.subtotal - factura.descuentos))})
    filas.append({**base, "cuenta": config.cuenta_iva, "debito": "0", "credito": str(factura.impuestos)})
    return filas


def exportar_csv(facturas: RepositorioFacturas, desde: date, hasta: date, *, config: Configuracion) -> str:
    """CSV con los asientos de las facturas timbradas o pagadas del periodo."""
    salida = io.StringIO()
    escritor = csv.DictWriter(salida, fieldnames=COLUMNAS, lineterminator="\n")
    escritor.writeheader()
    for factura in sorted(facturas.listar(), key=lambda f: (f.serie, f.folio or 0)):
        if factura.estado not in (EstadoFactura.TIMBRADA, EstadoFactura.PAGADA):
            continue
        if factura.fecha_emision and desde <= factura.fecha_emision.date() <= hasta:
            escritor.writerows(asientos(factura, config=config))
    return salida.getvalue()
