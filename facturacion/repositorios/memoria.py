"""Almacenamiento en memoria.

En produccion se cambia por una base de datos con la misma interfaz: los servicios
solo conocen estos metodos, no como se guardan los datos.
"""

from __future__ import annotations

from datetime import date
from typing import Generic, Iterator, TypeVar

from facturacion.errores import FacturaNoEncontrada
from facturacion.modelos import Cliente, EstadoFactura, Factura, NotaCredito, Producto
from facturacion.utilidades.validaciones import normalizar_nit

T = TypeVar("T")


class RepositorioMemoria(Generic[T]):
    """Diccionario con la interfaz minima que necesitan los servicios."""

    def __init__(self) -> None:
        self._datos: dict[str, T] = {}

    def guardar(self, clave: str, objeto: T) -> None:
        self._datos[clave] = objeto

    def obtener(self, clave: str) -> T | None:
        return self._datos.get(clave)

    def existe(self, clave: str) -> bool:
        return clave in self._datos

    def eliminar(self, clave: str) -> None:
        self._datos.pop(clave, None)

    def listar(self) -> list[T]:
        return list(self._datos.values())

    def __iter__(self) -> Iterator[T]:
        return iter(self.listar())

    def __len__(self) -> int:
        return len(self._datos)


class RepositorioClientes(RepositorioMemoria[Cliente]):
    def guardar_cliente(self, cliente: Cliente) -> None:
        self.guardar(cliente.id, cliente)

    def por_nit(self, nit: str) -> Cliente | None:
        nit_normalizado = normalizar_nit(nit)
        return next((c for c in self.listar() if normalizar_nit(c.nit) == nit_normalizado), None)


class RepositorioProductos(RepositorioMemoria[Producto]):
    def guardar_producto(self, producto: Producto) -> None:
        self.guardar(producto.codigo, producto)


class RepositorioFacturas(RepositorioMemoria[Factura]):
    def guardar_factura(self, factura: Factura) -> None:
        self.guardar(factura.identificador, factura)

    def obtener_factura(self, identificador: str) -> Factura:
        factura = self.obtener(identificador)
        if factura is None:
            raise FacturaNoEncontrada(f"No existe la factura {identificador}.")
        return factura

    def por_cliente(self, cliente_id: str) -> list[Factura]:
        return [f for f in self.listar() if f.cliente.id == cliente_id]

    def por_estado(self, estado: EstadoFactura) -> list[Factura]:
        return [f for f in self.listar() if f.estado == estado]

    def del_dia(self, dia: date) -> list[Factura]:
        return [f for f in self.listar() if f.fecha_emision and f.fecha_emision.date() == dia]


class RepositorioNotasCredito(RepositorioMemoria[NotaCredito]):
    def guardar_nota(self, nota: NotaCredito) -> None:
        self.guardar(f"{nota.serie}-{nota.folio}", nota)

    def de_factura(self, identificador: str) -> list[NotaCredito]:
        return [n for n in self.listar() if n.factura_origen == identificador]
