"""
Servidor web de THOT.

Conecta las paginas HTML/CSS con el sistema en Python y guarda todo en datos.json.

    pip install flask
    python Servidor.py

Luego abrir  http://127.0.0.1:5000
"""
import os
import secrets
import threading
import time
import webbrowser
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, redirect, request, send_from_directory, session

from Guardado import AlmacenJSON
from Parte_principal import NotificadorConsola, ServicioAsignaciones, ServicioAutenticacion
from Permisos import MODULOS, permisos_de, puede
from Sistema import NoEncontrado, Sistema

RAIZ = Path(__file__).resolve().parent
PAGINA_INICIO = "THOT - PaginaInicio.html"
PAGINA_LOGIN = "THOT - IincioSesion.html"

# pagina -> modulo que la protege (las que no estan aqui son publicas)
PAGINAS = {
    "THOT - PaginaHorario.html": "horarios",
    "THOT - PaginaMateria.html": "materias",
    "THOT - PaginaUsuario.html": "usuarios",
    "THOT - PaginaCarrera.html": "carreras",
    "THOT - PaginaFacultad.html": "facultades",
    "THOT - PaginaEspacio.html": "espacios",
    "THOT - PaginaAsignadas.html": "asignadas",
}
PAGINA_DE_MODULO = {m: p for p, m in PAGINAS.items()}


# [D] el sistema se arma aqui con sus dependencias
def crear_sistema(ruta_json):
    almacen = AlmacenJSON(ruta_json)
    servicio = ServicioAsignaciones(NotificadorConsola())
    return Sistema(servicio, ServicioAutenticacion(), almacen, almacen)


def _clave_secreta():
    """La clave que firma las sesiones se crea una vez y se guarda en .clave_secreta."""
    ruta = RAIZ / ".clave_secreta"
    if not ruta.exists():
        ruta.write_text(secrets.token_hex(32))
    return ruta.read_text().strip()


def crear_app(ruta_json=None):
    ruta_json = ruta_json or str(RAIZ / "datos.json")
    sistema = crear_sistema(ruta_json)
    if not sistema.cargar():
        sistema.cargar_ejemplo()
        print("\n  Primer arranque: se creo datos.json con datos de ejemplo.")
        print("  Usuarios de prueba (contrasena: Thot2026):")
        for u in sistema.usuarios:
            print(f"    {u.tipo:<14} {u.correo}")
        print()

    app = Flask(__name__, static_folder=None)
    app.secret_key = _clave_secreta()
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                      JSON_AS_ASCII=False)
    app.json.ensure_ascii = False
    app.sistema = sistema
    intentos = {}           # identificador -> (fallos, bloqueado_hasta)

    # ---------------------------------------------------------------- utilidades
    def usuario_actual():
        cedula = session.get("cedula")
        if not cedula:
            return None
        try:
            return sistema.usuario(cedula)
        except NoEncontrado:
            session.clear()
            return None

    def requiere(modulo, accion="ver"):
        def decorador(f):
            @wraps(f)
            def interno(*a, **kw):
                u = usuario_actual()
                if u is None:
                    return jsonify(error="Debe iniciar sesion"), 401
                if not puede(u.tipo, modulo, accion):
                    return jsonify(error="No tiene permiso para esta accion"), 403
                return f(*a, **kw)
            return interno
        return decorador

    def cuerpo():
        d = request.get_json(silent=True)
        if not isinstance(d, dict):
            raise ValueError("Peticion no valida")
        return d

    @app.errorhandler(ValueError)
    def _valor(e):
        return jsonify(error=str(e)), 400

    @app.errorhandler(NoEncontrado)
    def _noenc(e):
        return jsonify(error=str(e)), 404

    @app.after_request
    def _sin_cache(resp):
        if request.path.startswith("/api/") or request.path.startswith("/Interfaz/"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

    # ---------------------------------------------------------------- paginas
    @app.get("/")
    def raiz():
        return redirect("/Interfaz/" + PAGINA_INICIO)

    @app.get("/Interfaz/<path:nombre>")
    def pagina(nombre):
        modulo = PAGINAS.get(nombre)
        if modulo:
            u = usuario_actual()
            if u is None:
                return redirect("/Interfaz/" + PAGINA_LOGIN)
            if not puede(u.tipo, modulo):
                permitidas = [m for m in MODULOS if puede(u.tipo, m)]
                if not permitidas:
                    return redirect("/Interfaz/" + PAGINA_LOGIN)
                return redirect("/Interfaz/" + PAGINA_DE_MODULO[permitidas[0]])
        return send_from_directory(RAIZ / "Interfaz", nombre)

    @app.get("/Estilo/<path:nombre>")
    def estilo(nombre):
        return send_from_directory(RAIZ / "Estilo", nombre)

    @app.get("/Imagenes/<path:nombre>")
    def imagen(nombre):
        return send_from_directory(RAIZ / "Imagenes", nombre)

    # ---------------------------------------------------------------- sesion
    def info_sesion(u):
        return {"cedula": u.cedula, "nombre": u.nombre, "correo": u.correo, "rol": u.tipo,
                "nivel": u.nivel, "carreraCodigo": u.carrera.codigo, "facultadCodigo": u.facultad.codigo,
                "permisos": {m: sorted(a) for m, a in permisos_de(u.tipo).items()},
                "paginaInicial": "/Interfaz/" + PAGINA_DE_MODULO[
                    next(m for m in MODULOS if puede(u.tipo, m))]}

    @app.post("/api/login")
    def login():
        d = cuerpo()
        ident = str(d.get("usuario", "")).strip().lower()
        clave = str(d.get("contrasena", ""))
        fallos, hasta = intentos.get(ident, (0, 0))
        if hasta > time.time():
            return jsonify(error=f"Demasiados intentos. Espere {int(hasta - time.time()) + 1} segundos."), 429
        with sistema.cerrojo:
            u = sistema.autenticador.autenticar(sistema.usuarios, ident, clave)
        if u is None:
            fallos += 1
            intentos[ident] = (fallos, time.time() + 30 if fallos >= 5 else 0)
            if fallos >= 5:
                intentos[ident] = (0, time.time() + 30)
            return jsonify(error="Usuario o contrasena incorrectos"), 401
        intentos.pop(ident, None)
        session.clear()
        session["cedula"] = u.cedula
        return jsonify(info_sesion(u))

    @app.post("/api/logout")
    def logout():
        session.clear()
        return jsonify(ok=True)

    @app.get("/api/sesion")
    def sesion():
        u = usuario_actual()
        if u is None:
            return jsonify(error="Debe iniciar sesion"), 401
        return jsonify(info_sesion(u))

    # ---------------------------------------------------------------- CRUD generico
    # Las listas de facultades, carreras y espacios las necesitan varias paginas (selects),
    # por eso quien tenga cualquier acceso a esas paginas o a materias/usuarios/horarios puede leerlas.
    def lectura_catalogo(f):
        @wraps(f)
        def interno(*a, **kw):
            u = usuario_actual()
            if u is None:
                return jsonify(error="Debe iniciar sesion"), 401
            if not permisos_de(u.tipo):
                return jsonify(error="No tiene permiso"), 403
            return f(*a, **kw)
        return interno

    # --- facultades
    @app.get("/api/facultades")
    @lectura_catalogo
    def facultades_listar():
        return jsonify([sistema.v_facultad(f) for f in sistema.facultades])

    @app.post("/api/facultades")
    @requiere("facultades", "gestionar")
    def facultades_crear():
        return jsonify(sistema.v_facultad(sistema.crear_facultad(cuerpo()))), 201

    @app.put("/api/facultades/<codigo>")
    @requiere("facultades", "gestionar")
    def facultades_editar(codigo):
        return jsonify(sistema.v_facultad(sistema.editar_facultad(codigo, cuerpo())))

    @app.delete("/api/facultades/<codigo>")
    @requiere("facultades", "gestionar")
    def facultades_eliminar(codigo):
        sistema.eliminar_facultad(codigo)
        return jsonify(ok=True)

    # --- carreras
    @app.get("/api/carreras")
    @lectura_catalogo
    def carreras_listar():
        return jsonify([sistema.v_carrera(c) for c in sistema.carreras])

    @app.post("/api/carreras")
    @requiere("carreras", "gestionar")
    def carreras_crear():
        return jsonify(sistema.v_carrera(sistema.crear_carrera(cuerpo()))), 201

    @app.put("/api/carreras/<codigo>")
    @requiere("carreras", "gestionar")
    def carreras_editar(codigo):
        return jsonify(sistema.v_carrera(sistema.editar_carrera(codigo, cuerpo())))

    @app.delete("/api/carreras/<codigo>")
    @requiere("carreras", "gestionar")
    def carreras_eliminar(codigo):
        sistema.eliminar_carrera(codigo)
        return jsonify(ok=True)

    # --- usuarios
    @app.get("/api/usuarios")
    @requiere("usuarios")
    def usuarios_listar():
        return jsonify([sistema.v_usuario(u) for u in sistema.usuarios])

    @app.get("/api/docentes")
    @requiere("horarios", "gestionar")
    def docentes_listar():
        return jsonify([sistema.v_usuario(u) for u in sistema.usuarios if u.tipo == "Docente"])

    @app.post("/api/usuarios")
    @requiere("usuarios", "gestionar")
    def usuarios_crear():
        return jsonify(sistema.v_usuario(sistema.crear_usuario(cuerpo()))), 201

    @app.put("/api/usuarios/<cedula>")
    @requiere("usuarios", "gestionar")
    def usuarios_editar(cedula):
        u = sistema.editar_usuario(cedula, cuerpo())
        if session.get("cedula") == cedula:       # si se edita a si mismo, la sesion sigue al nuevo numero
            session["cedula"] = u.cedula
        return jsonify(sistema.v_usuario(u))

    @app.delete("/api/usuarios/<cedula>")
    @requiere("usuarios", "gestionar")
    def usuarios_eliminar(cedula):
        if session.get("cedula") == cedula:
            raise ValueError("No puede eliminar su propio usuario")
        sistema.eliminar_usuario(cedula)
        return jsonify(ok=True)

    # --- materias
    @app.get("/api/materias")
    @lectura_catalogo
    def materias_listar():
        return jsonify([sistema.v_materia(m) for m in sistema.materias])

    @app.post("/api/materias")
    @requiere("materias", "gestionar")
    def materias_crear():
        return jsonify(sistema.v_materia(sistema.crear_materia(cuerpo()))), 201

    @app.put("/api/materias/<codigo>")
    @requiere("materias", "gestionar")
    def materias_editar(codigo):
        return jsonify(sistema.v_materia(sistema.editar_materia(codigo, cuerpo())))

    @app.delete("/api/materias/<codigo>")
    @requiere("materias", "gestionar")
    def materias_eliminar(codigo):
        sistema.eliminar_materia(codigo)
        return jsonify(ok=True)

    # --- espacios
    @app.get("/api/espacios")
    @lectura_catalogo
    def espacios_listar():
        return jsonify([sistema.v_espacio(e) for e in sistema.espacios])

    @app.post("/api/espacios")
    @requiere("espacios", "gestionar")
    def espacios_crear():
        return jsonify(sistema.v_espacio(sistema.crear_espacio(cuerpo()))), 201

    @app.put("/api/espacios/<id>")
    @requiere("espacios", "gestionar")
    def espacios_editar(id):
        return jsonify(sistema.v_espacio(sistema.editar_espacio(id, cuerpo())))

    @app.delete("/api/espacios/<id>")
    @requiere("espacios", "gestionar")
    def espacios_eliminar(id):
        sistema.eliminar_espacio(id)
        return jsonify(ok=True)

    # --- asignaciones (horarios)
    @app.get("/api/asignaciones")
    @requiere("horarios")
    def asignaciones_listar():
        a = request.args
        lista = sistema.listar_asignaciones(a.get("facultad", ""), a.get("carrera", ""), a.get("periodo", ""),
                                            a.get("semestre", ""), a.get("paralelo", ""))
        return jsonify([sistema.v_asignacion(x) for x in lista])

    @app.get("/api/asignaciones/mias")
    @requiere("asignadas")
    def asignaciones_mias():
        """Docente: solo las suyas. Los demas roles con acceso ven todas."""
        u = usuario_actual()
        docente = u.cedula if u.tipo == "Docente" else ""
        lista = sistema.listar_asignaciones(docente=docente)
        return jsonify([sistema.v_asignacion(x) for x in lista])

    @app.post("/api/asignaciones")
    @requiere("horarios", "gestionar")
    def asignaciones_crear():
        return jsonify(sistema.v_asignacion(sistema.crear_asignacion(cuerpo()))), 201

    @app.delete("/api/asignaciones/<id>")
    @requiere("horarios", "gestionar")
    def asignaciones_eliminar(id):
        sistema.eliminar_asignacion(id)
        return jsonify(ok=True)

    @app.errorhandler(404)
    def _404(e):
        if request.path.startswith("/api/"):
            return jsonify(error="Ruta no encontrada"), 404
        return redirect("/Interfaz/" + PAGINA_INICIO)

    return app


if __name__ == "__main__":
    app = crear_app()
    puerto = int(os.environ.get("PORT", 5000))
    threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{puerto}")).start()
    app.run(host="127.0.0.1", port=puerto, debug=False, threaded=True)
