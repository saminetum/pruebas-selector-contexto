import pytest

from facturacion.errores import ClienteInvalido
from facturacion.modelos import Cliente
from facturacion.servicios.clientes import ServicioClientes


class RepositorioClientesDoble:
    def __init__(self):
        self.clientes = {}

    def guardar_cliente(self, cliente):
        self.clientes[cliente.id] = cliente

    def existe(self, clave):
        return clave in self.clientes

    def obtener(self, clave):
        return self.clientes.get(clave)

    def por_nit(self, nit):
        return next((cliente for cliente in self.clientes.values() if cliente.nit == nit), None)


@pytest.fixture

def repositorio_clientes():
    return RepositorioClientesDoble()


@pytest.fixture

def servicio_clientes(repositorio_clientes):
    return ServicioClientes(repositorio_clientes)


def test_C1_registrar_recorta_espacios_del_nombre_y_lo_guarda(servicio_clientes, repositorio_clientes):
    cliente = Cliente(id="cli-1", nombre="  Tienda La 14  ", nit="900123456", correo="cliente@ejemplo.com")

    cliente_registrado = servicio_clientes.registrar(cliente)

    assert cliente_registrado.nombre == "Tienda La 14"
    assert repositorio_clientes.obtener("cli-1").nombre == "Tienda La 14"


def test_C2_registrar_rechaza_nombre_recortado_de_mas_de_120_caracteres_y_no_lo_guarda(
    servicio_clientes, repositorio_clientes
):
    nombre = "  " + ("a" * 121) + "  "
    cliente = Cliente(id="cli-2", nombre=nombre, nit="900123456", correo="cliente2@ejemplo.com")

    with pytest.raises(ClienteInvalido, match=r"^El nombre del cliente no puede tener mas de 120 caracteres\.$"):
        servicio_clientes.registrar(cliente)

    assert repositorio_clientes.obtener("cli-2") is None


def test_C3_registrar_acepta_nombre_de_exactamente_120_caracteres_recortado(servicio_clientes, repositorio_clientes):
    nombre = "  " + ("b" * 120) + "  "
    cliente = Cliente(id="cli-3", nombre=nombre, nit="900123456", correo="cliente3@ejemplo.com")

    cliente_registrado = servicio_clientes.registrar(cliente)

    assert cliente_registrado.nombre == "b" * 120
    assert repositorio_clientes.obtener("cli-3").nombre == "b" * 120


@pytest.mark.parametrize(
    "cliente, mensaje",
    [
        (Cliente(id="cli-4", nombre="   ", nit="900123456", correo="cliente4@ejemplo.com"), "El cliente necesita un nombre."),
        (Cliente(id="cli-5", nombre="Cliente", nit="NIT-INVALIDO", correo="cliente5@ejemplo.com"), "El NIT NIT-INVALIDO no es valido."),
        (Cliente(id="cli-6", nombre="Cliente", nit="900123456", correo="correo-invalido"), "El correo correo-invalido no es valido."),
    ],
)
def test_C4_validaciones_existentes_siguen_rechazando_y_no_guardan(servicio_clientes, repositorio_clientes, cliente, mensaje):
    with pytest.raises(ClienteInvalido, match=f"^{mensaje.replace('.', '\\.')}$"):
        servicio_clientes.registrar(cliente)

    assert repositorio_clientes.obtener(cliente.id) is None


def test_C4_registrar_sigue_rechazando_id_repetido_y_no_modifica_el_repositorio(servicio_clientes, repositorio_clientes):
    primero = Cliente(id="cli-7", nombre="Cliente Uno", nit="900123456", correo="cliente1@ejemplo.com")
    repositorio_clientes.guardar_cliente(primero)
    duplicado = Cliente(id="cli-7", nombre="Cliente Dos", nit="900123457", correo="cliente2@ejemplo.com")

    with pytest.raises(ClienteInvalido, match=r"^Ya existe un cliente con id cli-7\.$"):
        servicio_clientes.registrar(duplicado)

    assert repositorio_clientes.obtener("cli-7").nombre == "Cliente Uno"
