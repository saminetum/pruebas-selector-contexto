from facturacion.errores import ClienteInvalido
from facturacion.modelos import Cliente
from facturacion.repositorios.memoria import RepositorioClientes
from facturacion.servicios.clientes import ServicioClientes


def test_C1_rechaza_nit_duplicado_aunque_cambie_el_formato_y_menciona_al_cliente_existente():
    repo = RepositorioClientes()
    servicio = ServicioClientes(repo)

    cliente_existente = Cliente(id="cli-1", nombre="Acme SAS", nit="900.123.456-7", correo="acme@example.com")
    servicio.registrar(cliente_existente)

    candidato = Cliente(id="cli-2", nombre="Nueva Acme", nit="900 123 456 7", correo="nueva@example.com")

    try:
        servicio.registrar(candidato)
    except ClienteInvalido as exc:
        mensaje = str(exc)
        assert "NIT" in mensaje
        assert "registrado" in mensaje
        assert "Acme SAS" in mensaje or "cli-1" in mensaje
    else:
        raise AssertionError("Se esperaba ClienteInvalido por NIT duplicado normalizado")


def test_C1_rechaza_nit_duplicado_con_digito_de_verificacion_equivalente():
    repo = RepositorioClientes()
    servicio = ServicioClientes(repo)

    cliente_existente = Cliente(id="cli-1", nombre="Comercial ABC", nit="900.123.456-7", correo="abc@example.com")
    servicio.registrar(cliente_existente)

    candidato = Cliente(id="cli-2", nombre="Otro Cliente", nit="9001234567", correo="otro@example.com")

    with __import__("pytest").raises(ClienteInvalido) as excinfo:
        servicio.registrar(candidato)

    mensaje = str(excinfo.value)
    assert "NIT" in mensaje
    assert "registrado" in mensaje
    assert "Comercial ABC" in mensaje or "cli-1" in mensaje


def test_C2_sigue_rechazando_id_duplicado_con_el_mismo_mensaje_actual():
    repo = RepositorioClientes()
    servicio = ServicioClientes(repo)

    servicio.registrar(Cliente(id="cli-1", nombre="Cliente Base", nit="900123456", correo="base@example.com"))

    candidato = Cliente(id="cli-1", nombre="Cliente Duplicado", nit="901234567", correo="dup@example.com")

    with __import__("pytest").raises(ClienteInvalido) as excinfo:
        servicio.registrar(candidato)

    assert str(excinfo.value) == "Ya existe un cliente con id cli-1."
