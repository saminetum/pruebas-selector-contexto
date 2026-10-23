"""Composicion de la aplicacion: aqui se crean y se conectan todos los servicios.

Es el unico lugar que sabe que implementacion se usa de cada pieza. Las pruebas
pasan un servicio de impuestos y un correo simulados; en produccion se pasan los
reales, y ningun servicio cambia.
"""

from __future__ import annotations

from dataclasses import dataclass

from facturacion.config import Configuracion
from facturacion.integraciones.correo import ClienteCorreo, CorreoEnMemoria
from facturacion.integraciones.servicio_impuestos import ClienteServicioImpuestos, ServicioImpuestosSimulado
from facturacion.repositorios.memoria import (
    RepositorioClientes,
    RepositorioFacturas,
    RepositorioNotasCredito,
    RepositorioProductos,
)
from facturacion.seguridad.autenticacion import Autenticador
from facturacion.servicios.anulacion import ServicioAnulacion
from facturacion.servicios.auditoria import RegistroAuditoria
from facturacion.servicios.clientes import ServicioClientes
from facturacion.servicios.emision import ServicioEmision
from facturacion.servicios.fidelizacion import ProgramaPuntos
from facturacion.servicios.inventario import ServicioInventario
from facturacion.servicios.notas_credito import ServicioNotasCredito
from facturacion.servicios.notificaciones import ServicioNotificaciones
from facturacion.servicios.numeracion import GeneradorFolios
from facturacion.servicios.pagos import ServicioPagos
from facturacion.servicios.timbrado import ServicioTimbrado


@dataclass
class Aplicacion:
    config: Configuracion
    facturas: RepositorioFacturas
    auditoria: RegistroAuditoria
    autenticador: Autenticador
    clientes: ServicioClientes
    inventario: ServicioInventario
    emision: ServicioEmision
    timbrado: ServicioTimbrado
    pagos: ServicioPagos
    anulacion: ServicioAnulacion
    notas_credito: ServicioNotasCredito
    notificaciones: ServicioNotificaciones
    programa_puntos: ProgramaPuntos


def construir_aplicacion(
    config: Configuracion | None = None,
    *,
    servicio_impuestos: ClienteServicioImpuestos | None = None,
    correo: ClienteCorreo | None = None,
) -> Aplicacion:
    config = config or Configuracion()
    servicio_impuestos = servicio_impuestos or ServicioImpuestosSimulado()
    correo = correo or CorreoEnMemoria()

    facturas = RepositorioFacturas()
    auditoria = RegistroAuditoria()
    inventario = ServicioInventario(RepositorioProductos())
    programa_puntos = ProgramaPuntos(auditoria)

    return Aplicacion(
        config=config,
        facturas=facturas,
        auditoria=auditoria,
        autenticador=Autenticador(),
        clientes=ServicioClientes(RepositorioClientes()),
        inventario=inventario,
        emision=ServicioEmision(
            facturas, GeneradorFolios(config.serie_facturas), inventario, auditoria, config, programa_puntos
        ),
        timbrado=ServicioTimbrado(servicio_impuestos, facturas, auditoria, config),
        pagos=ServicioPagos(facturas, auditoria),
        anulacion=ServicioAnulacion(facturas, inventario, servicio_impuestos, auditoria, config),
        notas_credito=ServicioNotasCredito(
            RepositorioNotasCredito(), GeneradorFolios(config.serie_notas_credito), auditoria
        ),
        notificaciones=ServicioNotificaciones(correo, config),
        programa_puntos=programa_puntos,
    )
