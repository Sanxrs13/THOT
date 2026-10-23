import os
import json
import Guardado
from Parte_principal import (
    Estudiante, Docente, Director, Coordinador, Admin,
    Aula, Laboratorio, Materia, Curso, Horario,
    NotificadorConsola, ServicioAsignaciones,
)


class SistemaEspacios:
    TIPOS_USUARIO = {
        "1": ("Estudiante", Estudiante),
        "2": ("Docente", Docente),
        "3": ("Director", Director),
        "4": ("Coordinador", Coordinador),
        "5": ("Admin", Admin),
    }

    def __init__(self):
        self.usuarios = []
        self.espacios = []
        self.materias = []
        self.cursos = []
        self.horarios = []
        self.ruta_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos.json")
        self.servicio = ServicioAsignaciones(NotificadorConsola())

    def leer_texto(self, mensaje):
        return input(mensaje).strip()

    def leer_entero(self, mensaje):
        while True:
            valor = input(mensaje).strip()
            try:
                return int(valor)
            except ValueError:
                print("  Debe ingresar un numero entero.")

    def leer_si_no(self, mensaje):
        while True:
            valor = input(mensaje + " (s/n): ").strip().lower()
            if valor in ("s", "si"):
                return True
            if valor in ("n", "no"):
                return False
            print("  Responda s o n.")

    def elegir(self, lista, titulo, describir):
        if not lista:
            print(f"  No hay {titulo} registrados todavia.")
            return None
        print(f"\n  {titulo}:")
        for i, item in enumerate(lista, start=1):
            print(f"    {i}. {describir(item)}")
        while True:
            n = self.leer_entero("  Elija el numero: ")
            if 1 <= n <= len(lista):
                return lista[n - 1]
            print("  Numero fuera de rango.")

    def ok(self, mensaje):
        print(f"\n  [OK] {mensaje}")

    def error(self, e):
        print(f"\n  [ERROR] {e}")

    def d_usuario(self, u):
        return f"{u} - {u.correo}"

    def d_materia(self, m):
        lab = "usa laboratorio" if m.requiere_laboratorio() else "sin laboratorio"
        return f"{m.nombre} (codigo {m.codigo}, {m.carrera}, {lab})"

    def d_curso(self, c):
        return f"Paralelo {c.paralelo} - semestre {c.semestre} - periodo {c.periodo}"

    def d_horario(self, h):
        return f"{h.periodo}: {h.hora_inicio}:00 a {h.hora_fin}:00 ({h.duracion()} h)"

    def registrar_usuario(self):
        print("\nRegistrar usuario")
        for k, (nombre, _) in self.TIPOS_USUARIO.items():
            print(f"  {k}. {nombre}")
        tipo = self.leer_texto("Tipo: ")
        if tipo not in self.TIPOS_USUARIO:
            print("  Tipo no valido.")
            return
        nombre_tipo, clase = self.TIPOS_USUARIO[tipo]
        try:
            u = clase(self.leer_texto("Correo: "), self.leer_texto("Nombre: "), self.leer_texto("Contrasena: "))
            self.usuarios.append(u)
            self.ok(f"{nombre_tipo} registrado: {u}")
        except ValueError as e:
            self.error(e)

    def registrar_espacio(self):
        print("\n--- Registrar espacio de estudio ---")
        print("  1. Aula")
        print("  2. Laboratorio")
        tipo = self.leer_texto("Tipo: ")
        if tipo not in ("1", "2"):
            print("  Tipo no valido.")
            return
        try:
            edificio = self.leer_texto("Codigo del edificio: ")
            capacidad = self.leer_entero("Capacidad (minimo 30): ")
            codigo_aula = self.leer_entero("Codigo del aula (3 digitos): ")
            if tipo == "1":
                e = Aula(edificio, capacidad, codigo_aula)
            else:
                maquinas = self.leer_entero("Numero de maquinas: ")
                e = Laboratorio(edificio, capacidad, codigo_aula, maquinas)
            self.espacios.append(e)
            self.ok(f"Espacio registrado: {e.descripcion()}")
        except ValueError as e:
            self.error(e)

    def registrar_materia(self):
        print("\n--- Registrar materia ---")
        try:
            nombre = self.leer_texto("Nombre: ")
            carrera = self.leer_texto("Carrera: ")
            codigo = self.leer_entero("Codigo: ")
            usar_lab = self.leer_si_no("Usa laboratorio?")
            m = Materia(nombre, carrera, codigo, usar_lab)
            self.materias.append(m)
            self.ok(f"Materia registrada: {self.d_materia(m)}")
        except ValueError as e:
            self.error(e)

    def registrar_curso(self):
        print("\nRegistrar curso")
        try:
            c = Curso(self.leer_texto("Paralelo: "), self.leer_texto("Semestre: "), self.leer_texto("Periodo: "))
            self.cursos.append(c)
            self.ok(f"Curso registrado: {self.d_curso(c)}")
        except ValueError as e:
            self.error(e)

    def registrar_horario(self):
        print("\n--- Registrar horario ---")
        try:
            periodo = self.leer_texto("Periodo: ")
            inicio = self.leer_entero("Hora de inicio (desde 7): ")
            fin = self.leer_entero("Hora de fin (hasta 19): ")
            h = Horario(periodo, inicio, fin)
            self.horarios.append(h)
            self.ok(f"Horario registrado: {self.d_horario(h)}")
        except ValueError as e:
            self.error(e)

    def crear_asignacion(self):
        print("\n--- Crear asignacion ---")
        docentes = [u for u in self.usuarios if isinstance(u, Docente)]
        docente = self.elegir(docentes, "Docentes", self.d_usuario)
        if not docente: return
        materia = self.elegir(self.materias, "Materias", self.d_materia)
        if not materia: return
        curso = self.elegir(self.cursos, "Cursos", self.d_curso)
        if not curso: return
        horario = self.elegir(self.horarios, "Horarios", self.d_horario)
        if not horario: return
        espacio = self.elegir(self.espacios, "Espacios", lambda e: e.descripcion())
        if not espacio: return
        try:
            self.servicio.asignar(docente, materia, curso, horario, espacio)
            self.ok("Asignacion creada.")
        except ValueError as e:
            self.error(e)

    def mostrar_lista(self, titulo, lista, describir):
        print(f"\n{titulo} ({len(lista)})")
        if not lista:
            print("  (vacio)")
        for i, item in enumerate(lista, start=1):
            print(f"  {i}. {describir(item)}")

    def ver_todo(self):
        print("\n ESTADO ACTUAL ")
        self.mostrar_lista("USUARIOS", self.usuarios, self.d_usuario)
        self.mostrar_lista("ESPACIOS", self.espacios, lambda e: e.descripcion())
        self.mostrar_lista("MATERIAS", self.materias, self.d_materia)
        self.mostrar_lista("CURSOS", self.cursos, self.d_curso)
        self.mostrar_lista("HORARIOS", self.horarios, self.d_horario)
        self.mostrar_lista(
            "ASIGNACIONES", self.servicio.asignaciones,
            lambda a: (f"{a.docente.nombre} | {a.materia.nombre} | paralelo {a.curso.paralelo} | "
                       f"{self.d_horario(a.horario)} | {a.espacio.descripcion()}"),
        )

    def iniciar_sesion(self):
        print("\n Iniciar sesion ")
        correo = self.leer_texto("Correo: ")
        clave = self.leer_texto("Contrasena: ")
        for u in self.usuarios:
            if u.correo == correo and u.validar_contrasena(clave):
                self.ok(f"Bienvenido {u}")
                return
        self.error("Correo o contrasena incorrectos.")

    def cargar_ejemplo(self):
        try:
            self.usuarios.extend([
                Estudiante("ana@mail.com", "Ana", "1234"),
                Docente("luis@mail.com", "Luis", "1234"),
                Director("dir@mail.com", "Diana", "1234"),
                Coordinador("coord@mail.com", "Carlos", "1234"),
                Admin("admin@mail.com", "Root", "1234"),
            ])
            self.espacios.extend([Aula("A", 35, 101), Laboratorio("B", 40, 201, 25)])
            self.materias.extend([Materia("Programacion", "Sistemas", 1, True), Materia("Matematica", "Sistemas", 2, False)])
            self.cursos.append(Curso("A", "1", "2026-1"))
            self.horarios.extend([Horario("2026-1", 8, 10), Horario("2026-1", 9, 11)])
            self.ok("Datos de ejemplo cargados. Use la opcion 7 para verlos.")
        except ValueError as e:
            self.error(e)

    def guardar_datos(self):
        try:
            Guardado.guardar(self.ruta_json, self.usuarios, self.espacios, self.materias, self.cursos, self.horarios, self.servicio.asignaciones)
        except OSError as e:
            self.error(f"No se pudo guardar el json: {e}")

    def cargar_datos(self):
        try:
            datos = Guardado.cargar(self.ruta_json)
        except ValueError as e:
            self.error(f"No se pudo leer datos.json: {e}")
            return
        if datos is None:
            print("  (No hay datos guardados, se empieza vacio.)")
            return
        self.usuarios[:] = datos["usuarios"]
        self.espacios[:] = datos["espacios"]
        self.materias[:] = datos["materias"]
        self.cursos[:] = datos["cursos"]
        self.horarios[:] = datos["horarios"]
        self.servicio.asignaciones[:] = datos["asignaciones"]
        self.ok(f"Datos cargados desde {self.ruta_json} ({len(self.usuarios)} usuarios, {len(self.servicio.asignaciones)} asignaciones).")

    def borrar_datos(self):
        if not self.leer_si_no("Seguro que desea borrar TODOS los datos (memoria y json)?"):
            return
        for lista in (self.usuarios, self.espacios, self.materias, self.cursos, self.horarios, self.servicio.asignaciones):
            lista.clear()
        if os.path.exists(self.ruta_json):
            os.remove(self.ruta_json)
        self.ok("Todos los datos fueron borrados.")

    def iniciar(self):
        self.cargar_datos()
        acciones = {
            "1": self.registrar_usuario,
            "2": self.registrar_espacio,
            "3": self.registrar_materia,
            "4": self.registrar_curso,
            "5": self.registrar_horario,
            "6": self.crear_asignacion,
            "7": self.ver_todo,
            "8": self.iniciar_sesion,
            "9": self.cargar_ejemplo,
            "10": self.borrar_datos,
        }
        
        menu = """
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

        while True:
            print(menu)
            try:
                opcion = input("Opcion: ").strip()
            except EOFError:
                break
            if opcion == "0":
                print("Hasta luego.")
                break
            
            accion = acciones.get(opcion)
            if accion:
                accion()
                if opcion != "10":
                    self.guardar_datos()
            else:
                print("  Opcion no valida.")


if __name__ == "__main__":
    app = SistemaEspacios()
    app.iniciar()
