"""Representacion imprimible de la factura, en PDF.

No usa ninguna libreria: escribe un PDF minimo de una pagina con el texto de la
factura. Basta para adjuntarlo a un correo, imprimirlo en la caja y probarlo, y
evita una dependencia pesada en el punto de venta.
"""

from __future__ import annotations

from facturacion.config import Configuracion
from facturacion.modelos import Factura
from facturacion.servicios.calculos import importe_bruto, importe_neto
from facturacion.utilidades.dinero import formatear
from facturacion.utilidades.fechas import formato_iso


def lineas_de_texto(factura: Factura, config: Configuracion) -> list[str]:
    """El contenido de la factura, linea por linea, tal como se imprime."""
    lineas = [
        config.razon_social_emisor,
        f"NIT {config.nit_emisor}",
        f"Factura {factura.identificador}",
        f"Fecha: {formato_iso(factura.fecha_emision) if factura.fecha_emision else '-'}",
        f"Cliente: {factura.cliente.nombre} (NIT {factura.cliente.nit})",
        "",
    ]
    for linea in factura.lineas:
        bruto = importe_bruto(linea)
        neto = importe_neto(linea)
        detalle_descuento = ""
        if linea.descuento:
            detalle_descuento = f"  Descuento: {formatear(linea.descuento)}"
        lineas.append(
            f"{linea.cantidad} x {linea.producto.descripcion}  Bruto: {formatear(bruto)}"
            f"{detalle_descuento}  Neto: {formatear(neto)}"
        )
    lineas += [
        "",
        f"Subtotal: {formatear(factura.subtotal)}",
        f"Descuentos: {formatear(factura.descuentos)}",
        f"IVA: {formatear(factura.impuestos)}",
        f"Total: {formatear(factura.total)}",
    ]
    if factura.timbre is not None:
        lineas.append(f"UUID: {factura.timbre.uuid}")
    return lineas


def _escapar(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def generar_pdf(factura: Factura, config: Configuracion) -> bytes:
    """Un PDF valido de una pagina, con fuente Helvetica y el texto de la factura."""
    texto = lineas_de_texto(factura, config)
    contenido = "BT /F1 10 Tf 14 TL 50 800 Td\n" + "\n".join(
        f"({_escapar(linea)}) '" for linea in texto
    ) + "\nET"
    flujo = contenido.encode("latin-1", errors="replace")
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(flujo)).encode() + b" >>\nstream\n" + flujo + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    salida = bytearray(b"%PDF-1.4\n")
    posiciones = []
    for numero, objeto in enumerate(objetos, start=1):
        posiciones.append(len(salida))
        salida += f"{numero} 0 obj\n".encode() + objeto + b"\nendobj\n"
    inicio_xref = len(salida)
    salida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    for posicion in posiciones:
        salida += f"{posicion:010d} 00000 n \n".encode()
    salida += (
        f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{inicio_xref}\n%%EOF\n"
    ).encode()
    return bytes(salida)


def nombre_archivo_pdf(factura: Factura) -> str:
    return f"{factura.identificador}.pdf"
