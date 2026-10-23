"""Emision de facturas: del carrito a una factura con folio y totales.

Emitir no es timbrar. La factura emitida ya tiene folio y existencias reservadas,
pero todavia no tiene validez fiscal: la obtiene cuando el servicio de impuestos la
timbra (servicios/timbrado.py).
"""

from __future__ import annotations

from decimal import Decimal

from facturacion.config import Configuracion
from facturacion.errores import EstadoInvalido, FacturaInvalida
from facturacion.modelos import Cliente, EstadoFactura, Factura, LineaFactura
from facturacion.repositorios.memoria import RepositorioFacturas
from facturacion.servicios.auditoria import RegistroAuditoria
from facturacion.servicios.calculos import aplicar_descuento_porcentual, calcular_totales
from facturacion.servicios.fidelizacion import ProgramaPuntos
from facturacion.servicios.inventario import ServicioInventario
from facturacion.servicios.numeracion import GeneradorFolios
from facturacion.utilidades.fechas import ahora
from facturacion.utilidades.validaciones import validar_cantidad

DESCUENTO_FRECUENTE = Decimal("0.05")


class ServicioEmision:
    def __init__(
        self,
        facturas: RepositorioFacturas,
        folios: GeneradorFolios,
        inventario: ServicioInventario,
        auditoria: RegistroAuditoria,
        config: Configuracion,
        programa_puntos: ProgramaPuntos,
    ) -> None:
        self._facturas = facturas
        self._folios = folios
        self._inventario = inventario
        self._auditoria = auditoria
        self._config = config
        self._programa_puntos = programa_puntos

    def _aplicar_descuento_frecuente(self, cliente: Cliente, lineas: list[LineaFactura]) -> list[LineaFactura]:
        if not self._programa_puntos.es_frecuente(cliente.id):
            return list(lineas)
        return [aplicar_descuento_porcentual(linea, DESCUENTO_FRECUENTE) for linea in lineas]

    def crear_borrador(self, cliente: Cliente, lineas: list[LineaFactura]) -> Factura:
        """Una factura sin folio, con sus totales calculados, para mostrar al cliente."""
        for linea in lineas:
            if not validar_cantidad(linea.cantidad):
                raise FacturaInvalida(
                    f"Cantidad no valida para {linea.producto.codigo}: {linea.cantidad}."
                )
        lineas_con_descuento = self._aplicar_descuento_frecuente(cliente, lineas)
        factura = Factura(serie=self._config.serie_facturas, cliente=cliente, lineas=lineas_con_descuento)
        return calcular_totales(factura)

    def emitir(self, borrador: Factura) -> Factura:
        """Reserva inventario, asigna folio y deja la factura lista para timbrar.

        El folio se asigna despues de reservar: si no hay existencias, no se consume
        un folio que despues habria que justificar ante el fisco.
        """
        if borrador.estado != EstadoFactura.BORRADOR:
            raise EstadoInvalido(
                f"Solo se emite un borrador; la factura esta {borrador.estado.value}."
            )
        calcular_totales(borrador)
        self._inventario.reservar(borrador.lineas)
        borrador.folio = self._folios.siguiente()
        borrador.fecha_emision = ahora()
        borrador.estado = EstadoFactura.EMITIDA
        self._facturas.guardar_factura(borrador)
        self._auditoria.registrar(
            "factura_emitida",
            factura=borrador.identificador,
            cliente=borrador.cliente.id,
            total=str(borrador.total),
        )
        return borrador
