from datetime import date

import pytest

from facturacion.config import Configuracion
from facturacion.integraciones.exportacion_contable import asientos, exportar_csv
from facturacion.modelos import Cliente, EstadoFactura, Factura, LineaFactura, MedioPago, Producto, Pago
from facturacion.repositorios.memoria import RepositorioFacturas


def _factura_emitida(
    *,
    total: str = "100.00",
    subtotal: str = "84.03",
    impuestos: str = "15.97",
    cliente_id: str = "cli-1",
    cliente_nit: str = "900000001",
) -> Factura:
    cliente = Cliente(id=cliente_id, nombre="Cliente Prueba", nit=cliente_nit)
    producto = Producto(
        codigo="P1",
        descripcion="Producto prueba",
        precio_unitario=84.03,
        tasa_iva=0.19,
    )
    factura = Factura(
        serie="FV",
        cliente=cliente,
        lineas=[LineaFactura(producto=producto, cantidad=1)],
        folio=1,
        estado=EstadoFactura.TIMBRADA,
        subtotal=subtotal,
        descuentos="0",
        impuestos=impuestos,
        total=total,
    )
    factura.fecha_emision = __import__("datetime").datetime(2026, 1, 15, 10, 30, 0)
    factura.pagos.append(Pago(medio=MedioPago.EFECTIVO, monto=100, fecha=__import__("datetime").datetime(2026, 1, 15, 10, 31, 0)))
    return factura


def test_C1_asientos_usan_las_cuentas_configuradas_desde_entorno():
    config = Configuracion.desde_entorno(
        {
            "FACTURACION_CUENTA_CAJA": "120001",
            "FACTURACION_CUENTA_BANCOS": "120002",
            "FACTURACION_CUENTA_INGRESOS": "420001",
            "FACTURACION_CUENTA_IVA": "240001",
            "FACTURACION_CUENTA_CLIENTES": "130001",
        }
    )

    factura = _factura_emitida()

    lineas = asientos(factura, config=config)

    assert [linea["cuenta"] for linea in lineas] == ["120001", "420001", "240001"]


def test_C2_asientos_usan_las_cuentas_por_defecto_si_no_hay_variables():
    config = Configuracion.desde_entorno({})

    factura = _factura_emitida()

    lineas = asientos(factura, config=config)

    assert [linea["cuenta"] for linea in lineas] == ["110505", "413524", "240802"]


def test_C2_exportar_csv_tambien_arrastra_las_cuentas_por_defecto():
    config = Configuracion.desde_entorno({})
    repo = RepositorioFacturas()
    factura = _factura_emitida()
    repo.guardar_factura(factura)

    csv = exportar_csv(repo, date(2026, 1, 1), date(2026, 1, 31), config=config)

    assert "110505" in csv
    assert "413524" in csv
    assert "240802" in csv


@pytest.mark.parametrize(
    "entorno, variable, valor_invalido",
    [
        ({"FACTURACION_CUENTA_IVA": ""}, "FACTURACION_CUENTA_IVA", ""),
        ({"FACTURACION_CUENTA_IVA": "24A802"}, "FACTURACION_CUENTA_IVA", "24A802"),
    ],
)
def test_C3_rechaza_cuentas_invalidas_al_cargar_configuracion(entorno, variable, valor_invalido):
    with pytest.raises(ValueError, match=variable):
        Configuracion.desde_entorno(entorno)

    assert valor_invalido is not None
