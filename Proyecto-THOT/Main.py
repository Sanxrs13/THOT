import os

import json
import Guardado
from Parte_principal import (
    Estudiante, Docente, Director, Coordinador, Admin,
    Aula, Laboratorio, Materia, Curso, Horario,
    NotificadorConsola, ServicioAsignaciones,
)

usuarios = []
espacios = []
materias = []
cursos = []
horarios = []

RUTA_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos.json")

servicio = ServicioAsignaciones(NotificadorConsola())

TIPOS_USUARIO = {
    "1": ("Estudiante", Estudiante),
    "2": ("Docente", Docente),
    "3": ("Director", Director),
    "4": ("Coordinador", Coordinador),
    "5": ("Admin", Admin),
}


def leer_texto(mensaje):
    return input(mensaje).strip()


def leer_entero(mensaje):
    while True:
        valor = input(mensaje).strip()
        try:
            return int(valor)
        except ValueError:
            print("  Debe ingresar un numero entero.")


def leer_si_no(mensaje):
    while True:
        valor = input(mensaje + " (s/n): ").strip().lower()
        if valor in ("s", "si"):
            return True
        if valor in ("n", "no"):
            return False
        print("  Responda s o n.")


def elegir(lista, titulo, describir):
    """Muestra una lista numerada y devuelve el elemento elegido (o None)."""
    if not lista:
        print(f"  No hay {titulo} registrados todavia.")
        return None
    print(f"\n  {titulo}:")
    for i, item in enumerate(lista, start=1):
        print(f"    {i}. {describir(item)}")
    while True:
        n = leer_entero("  Elija el numero: ")
        if 1 <= n <= len(lista):
            return lista[n - 1]
        print("  Numero fuera de rango.")


def ok(mensaje):
    print(f"\n  [OK] {mensaje}")


def error(e):
    print(f"\n  [ERROR] {e}")


def d_usuario(u):
    return f"{u} - {u.correo}"


def d_materia(m):
    lab = "usa laboratorio" if m.requiere_laboratorio() else "sin laboratorio"
    return f"{m.nombre} (codigo {m.codigo}, {m.carrera}, {lab})"


def d_curso(c):
    return f"Paralelo {c.paralelo} - semestre {c.semestre} - periodo {c.periodo}"


def d_horario(h):
    return f"{h.periodo}: {h.hora_inicio}:00 a {h.hora_fin}:00 ({h.duracion()} h)"

def registrar_usuario():
    print("\nRegistrar usuario ")
    for k, (nombre, _) in TIPOS_USUARIO.items():
        print(f"  {k}. {nombre}")
    tipo = leer_texto("Tipo: ")
    if tipo not in TIPOS_USUARIO:
        print("  Tipo no valido.")
        return
    nombre_tipo, clase = TIPOS_USUARIO[tipo]
    try:
        u = clase(leer_texto("Correo: "), leer_texto("Nombre: "), leer_texto("Contrasena: "))
        usuarios.append(u)
        ok(f"{nombre_tipo} registrado: {u}")
    except ValueError as e:
        error(e)


def registrar_espacio():
    print("\n--- Registrar espacio de estudio ---")
    print("  1. Aula")
    print("  2. Laboratorio")
    tipo = leer_texto("Tipo: ")
    if tipo not in ("1", "2"):
        print("  Tipo no valido.")
        return
    try:
        edificio = leer_texto("Codigo del edificio: ")
        capacidad = leer_entero("Capacidad (minimo 30): ")
        codigo_aula = leer_entero("Codigo del aula (3 digitos): ")
        if tipo == "1":
            e = Aula(edificio, capacidad, codigo_aula)
        else:
            maquinas = leer_entero("Numero de maquinas: ")
            e = Laboratorio(edificio, capacidad, codigo_aula, maquinas)
        espacios.append(e)
        ok(f"Espacio registrado: {e.descripcion()}")
    except ValueError as e:
        error(e)


def registrar_materia():
    print("\n--- Registrar materia ---")
    try:
        nombre = leer_texto("Nombre: ")
        carrera = leer_texto("Carrera: ")
        codigo = leer_entero("Codigo: ")
        usar_lab = leer_si_no("Usa laboratorio?")
        m = Materia(nombre, carrera, codigo, usar_lab)
        materias.append(m)
        ok(f"Materia registrada: {d_materia(m)}")
    except ValueError as e:
        error(e)


def registrar_curso():
    print("\n Registrar curso ")
    try:
        c = Curso(leer_texto("Paralelo: "), leer_texto("Semestre: "), leer_texto("Periodo: "))
        cursos.append(c)
        ok(f"Curso registrado: {d_curso(c)}")
    except ValueError as e:
        error(e)


def registrar_horario():
    print("\n--- Registrar horario ---")
    try:
        periodo = leer_texto("Periodo: ")
        inicio = leer_entero("Hora de inicio (desde 7): ")
        fin = leer_entero("Hora de fin (hasta 19): ")
        h = Horario(periodo, inicio, fin)
        horarios.append(h)
        ok(f"Horario registrado: {d_horario(h)}")
    except ValueError as e:
        error(e)


def crear_asignacion():
    print("\n--- Crear asignacion ---")
    docentes = [u for u in usuarios if isinstance(u, Docente)]
    docente = elegir(docentes, "Docentes", d_usuario)
    if not docente:
        return
    materia = elegir(materias, "Materias", d_materia)
    if not materia:
        return
    curso = elegir(cursos, "Cursos", d_curso)
    if not curso:
        return
    horario = elegir(horarios, "Horarios", d_horario)
    if not horario:
        return
    espacio = elegir(espacios, "Espacios", lambda e: e.descripcion())
    if not espacio:
        return
    try:
        servicio.asignar(docente, materia, curso, horario, espacio)
        ok("Asignacion creada.")
    except ValueError as e:
        error(e)


def mostrar_lista(titulo, lista, describir):
    print(f"\n{titulo} ({len(lista)})")
    if not lista:
        print("  (vacio)")
    for i, item in enumerate(lista, start=1):
        print(f"  {i}. {describir(item)}")


def ver_todo():
    print("\n ESTADO ACTUAL ")
    mostrar_lista("USUARIOS", usuarios, d_usuario)
    mostrar_lista("ESPACIOS", espacios, lambda e: e.descripcion())
    mostrar_lista("MATERIAS", materias, d_materia)
    mostrar_lista("CURSOS", cursos, d_curso)
    mostrar_lista("HORARIOS", horarios, d_horario)
    mostrar_lista(
        "ASIGNACIONES", servicio.asignaciones,
        lambda a: (f"{a.docente.nombre} | {a.materia.nombre} | paralelo {a.curso.paralelo} | "
                   f"{d_horario(a.horario)} | {a.espacio.descripcion()}"),
    )


def iniciar_sesion():
    print("\n Iniciar sesion ")
    correo = leer_texto("Correo: ")
    clave = leer_texto("Contrasena: ")
    for u in usuarios:
        if u.correo == correo and u.validar_contrasena(clave):
            ok(f"Bienvenido {u}")
            return
    error("Correo o contrasena incorrectos.")


def cargar_ejemplo():
    """Carga datos de prueba para ver rapido como funciona todo."""
    try:
        usuarios.extend([
            Estudiante("ana@mail.com", "Ana", "1234"),
            Docente("luis@mail.com", "Luis", "1234"),
            Director("dir@mail.com", "Diana", "1234"),
            Coordinador("coord@mail.com", "Carlos", "1234"),
            Admin("admin@mail.com", "Root", "1234"),
        ])
        espacios.extend([Aula("A", 35, 101), Laboratorio("B", 40, 201, 25)])
        materias.extend([Materia("Programacion", "Sistemas", 1, True),
                         Materia("Matematica", "Sistemas", 2, False)])
        cursos.append(Curso("A", "1", "2026-1"))
        horarios.extend([Horario("2026-1", 8, 10), Horario("2026-1", 9, 11)])
        ok("Datos de ejemplo cargados. Use la opcion 7 para verlos.")
    except ValueError as e:
        error(e)

def guardar_datos():
    try:
        Guardado.guardar(RUTA_JSON, usuarios, espacios, materias, cursos, horarios,
                         servicio.asignaciones)
    except OSError as e:
        error(f"No se pudo guardar el json: {e}")


def cargar_datos():
    try:
        datos = Guardado.cargar(RUTA_JSON)
    except ValueError as e:
        error(f"No se pudo leer datos.json: {e}")
        return
    if datos is None:
        print("  (No hay datos guardados, se empieza vacio.)")
        return
    usuarios[:] = datos["usuarios"]
    espacios[:] = datos["espacios"]
    materias[:] = datos["materias"]
    cursos[:] = datos["cursos"]
    horarios[:] = datos["horarios"]
    servicio.asignaciones[:] = datos["asignaciones"]
    ok(f"Datos cargados desde {RUTA_JSON} "
       f"({len(usuarios)} usuarios, {len(servicio.asignaciones)} asignaciones).")


def borrar_datos():
    if not leer_si_no("Seguro que desea borrar TODOS los datos (memoria y json)?"):
        return
    for lista in (usuarios, espacios, materias, cursos, horarios, servicio.asignaciones):
        lista.clear()
    if os.path.exists(RUTA_JSON):
        os.remove(RUTA_JSON)
    ok("Todos los datos fueron borrados.")

MENU = """
=============== SISTEMA DE ESPACIOS DE ESTUDIO ===============
  1. Registrar usuario
  2. Registrar espacio (aula / laboratorio)
  3. Registrar materia
  4. Registrar curso
  5. Registrar horario
  6. Crear asignacion
  7. Ver todo
  8. Iniciar sesion
  9. Cargar datos de ejemplo
  10. Borrar todos los datos
  0. Salir
==============================================================="""

ACCIONES = {
    "1": registrar_usuario,
    "2": registrar_espacio,
    "3": registrar_materia,
    "4": registrar_curso,
    "5": registrar_horario,
    "6": crear_asignacion,
    "7": ver_todo,
    "8": iniciar_sesion,
    "9": cargar_ejemplo,
    "10": borrar_datos,
}


def main():
    cargar_datos()
    while True:
        print(MENU)
        try:
            opcion = input("Opcion: ").strip()
        except EOFError:
            break
        if opcion == "0":
            print("Hasta luego.")
            break
        accion = ACCIONES.get(opcion)
        if accion:
            accion()
            if opcion != "10":
                guardar_datos()  
        else:
            print("  Opcion no valida.")


if __name__ == "__main__":
    main()