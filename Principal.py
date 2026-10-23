from abc import ABC, abstractmethod

#clases
#usuarios
#usuario(padre)
class usuario:
    def __init__(self, correo: str, nombre: str, contrasena: str):
        if not nombre.strip():
            raise ValueError("debe ingrese un nombre")
        if "@" not in correo or "." not in correo:
            raise ValueError("Correo no valido") 
        if not contrasena.strip():
            raise ValueError("debe de ingrese la contraseña")
        self.correo = correo.strip()
        self.nombre = nombre.strip()
        self.__contrasena = contrasena.strip()
        
    def validar_contrasena(self, contrasena):
        return self.__contrasena == contrasena     

#todos heredan de usuario correo,nombre y contraseña
#estudiante
class estudiante(usuario):
    def __init__(self, correo, nombre, contrasena):
        super().__init__(correo, nombre, contrasena)

#docente(hijo: usuario)
class decente(usuario):
    def __init__(self, correo, nombre, contrasena):
        super().__init__(correo, nombre, contrasena)
        
#director(hijo: usuario)
class director(usuario):
    def __init__(self, correo, nombre, contrasena):
        super().__init__(correo, nombre, contrasena)
        
#cordinador(hijo: usuario)
class cordinador(usuario):
    def __init__(self, correo, nombre, contrasena):
        super().__init__(correo, nombre, contrasena)

#admin(hijo: cordinador y director)
class admin(director, cordinador):
    def __init__(self, correo, nombre, contrasena):
        super().__init__(correo, nombre, contrasena)

        
#espacios de estudio
#epacio_estudio(padre1)
class espacio_estudio:
    def __init__(self, codigo_edificio: str, capacidad: int):
        if not codigo_edificio.strip():
            raise ValueError("debed dde ingresar un codigo")
        if capacidad <= 29:
            raise ValueError("un curso tiene que tener almenos mayor que 29")
        
        self.codigo_edificio = codigo_edificio.strip()
        self.codigo_edificio = capacidad

#aula(hijo espacio_ estuduio)
class aula(espacio_estudio):
    def __init__(self, codigo_edificio, capacidad, codigo_aula: int):
        if codigo_aula <= 99:
            raise ValueError("el codigo del aula tiene que ser de 3 digitos") 
        super().__init__(codigo_edificio, capacidad)
        self.codigo_aula = codigo_aula
        
#laboratorio(hijo: aula)
class laboratorio(aula):
    def __init__(self, codigo_edificio, capacidad, codigo_aula, numero_maquinas: int):
        if numero_maquinas <= (capacidad/2):
            raise ValueError("tiene que almenos la mitas de maquina por capacidad")
        super().__init__(codigo_edificio, capacidad, codigo_aula)
        self.numero_maquinas = numero_maquinas

#Materia, curso, horario
#materia
class materia:
    def __init__(self,nombre:str, carrera: str, codigo: int,usar_lab : bool):
        if not nombre:
            raise ValueError("debe de ingresar un nombre")
        if not carrera:
            raise ValueError("debe de ingresar una carrera")
        if codigo <= 0:
            raise ValueError("codigo en numeros positivos")
        if not usar_lab:
            raise ValueError("debe de espesificar si utiliza o no laboratorio")
        self.nombre = nombre.strip()
        self.carrera = carrera.strip()
        self.codigo = codigo
        self.usar_lab = usar_lab
        
#curso
class curso:
    def __init__(self, paralelo: str, semestre: str, peridodo: str):
        if not paralelo:
            raise ValueError("debe de ingresar el paralelo")
        if not semestre:
            raise ValueError("debe de ingresar el semestre")
        if not peridodo:
            raise ValueError("debe de ingresar el periodo")
        self.paralelo = paralelo.strip()
        self.semestre = semestre.strip()
        self.periodo = peridodo.strip()
        
#horario
class horario:
    def __init__(self, perido: str, horas_inicio: int, hora_fin: int):
        if horas_inicio < 7:
            raise ValueError("las clases no pueden ser tan trempranas")
        if hora_fin > 19:
            raise ValueError("las clases no pueden ser tan tarde")
        self.periodo = perido.strip()
        self.hora_inicio = horas_inicio
        self.hora_fin = hora_fin
