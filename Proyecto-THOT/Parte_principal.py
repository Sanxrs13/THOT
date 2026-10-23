from abc import ABC, abstractmethod

#clases
#usuarios
#usuario(padre)
class Usuario(ABC):
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

    #metodo abstracto: cada tipo de usuario define su rol
    @abstractmethod
    def rol(self) -> str:
        pass

    def __str__(self):
        return f"{self.nombre} ({self.rol()})"

    #datos del usuario para guardar en json
    def datos(self):
        return {"tipo": type(self).__name__, "correo": self.correo,
                "nombre": self.nombre, "contrasena": self.__contrasena}

#todos heredan de usuario correo,nombre y contraseña
#estudiante
class Estudiante(Usuario):
    def __init__(self, correo, nombre, contrasena):
        super().__init__(correo, nombre, contrasena)

    def rol(self):
        return "estudiante"

#docente(hijo: usuario)
class Docente(Usuario):
    def __init__(self, correo, nombre, contrasena):
        super().__init__(correo, nombre, contrasena)

    def rol(self):
        return "docente"
        
#director(hijo: usuario)
class Director(Usuario):
    def __init__(self, correo, nombre, contrasena):
        super().__init__(correo, nombre, contrasena)

    def rol(self):
        return "director"
        
#cordinador(hijo: usuario)
class Coordinador(Usuario):
    def __init__(self, correo, nombre, contrasena):
        super().__init__(correo, nombre, contrasena)

    def rol(self):
        return "coordinador"

#admin(hijo: cordinador y director)
class Admin(Director, Coordinador):
    def __init__(self, correo, nombre, contrasena):
        super().__init__(correo, nombre, contrasena)

    #herencia multiple: reune lo de director y coordinador
    def rol(self):
        return f"admin ({Director.rol(self)} y {Coordinador.rol(self)})"

        
#espacios de estudio
#epacio_estudio(padre1)
class EspacioEstudio(ABC):
    def __init__(self, codigo_edificio: str, capacidad: int):
        if not codigo_edificio.strip():
            raise ValueError("debed dde ingresar un codigo")
        if capacidad <= 29:
            raise ValueError("un curso tiene que tener almenos mayor que 29")
        
        self.codigo_edificio = codigo_edificio.strip()
        self.capacidad = capacidad

    #metodos abstractos: cada espacio define como se describe y que materias admite
    @abstractmethod
    def descripcion(self) -> str:
        pass

    @abstractmethod
    def admite(self, materia) -> bool:
        pass

#aula(hijo espacio_ estuduio)
class Aula(EspacioEstudio):
    def __init__(self, codigo_edificio, capacidad, codigo_aula: int):
        if codigo_aula <= 99:
            raise ValueError("el codigo del aula tiene que ser de 3 digitos") 
        super().__init__(codigo_edificio, capacidad)
        self.codigo_aula = codigo_aula

    def descripcion(self):
        return f"Aula {self.codigo_aula} del edificio {self.codigo_edificio} (capacidad {self.capacidad})"

    def admite(self, materia):
        return not materia.usar_lab
        
#laboratorio(hijo: aula)
class Laboratorio(Aula):
    def __init__(self, codigo_edificio, capacidad, codigo_aula, numero_maquinas: int):
        if numero_maquinas < (capacidad/2):
            raise ValueError("tiene que almenos la mitas de maquina por capacidad")
        super().__init__(codigo_edificio, capacidad, codigo_aula)
        self.numero_maquinas = numero_maquinas

    def descripcion(self):
        return f"Laboratorio {self.codigo_aula} del edificio {self.codigo_edificio} ({self.numero_maquinas} maquinas)"

    def admite(self, materia):
        return True

#Materia, curso, horario
#materia
class Materia:
    def __init__(self,nombre:str, carrera: str, codigo: int,usar_lab : bool):
        if not nombre.strip():
            raise ValueError("debe de ingresar un nombre")
        if not carrera.strip():
            raise ValueError("debe de ingresar una carrera")
        if codigo <= 0:
            raise ValueError("codigo en numeros positivos")
        if not isinstance(usar_lab, bool):
            raise ValueError("debe de espesificar si utiliza o no laboratorio")
        self.nombre = nombre.strip()
        self.carrera = carrera.strip()
        self.codigo = codigo
        self.usar_lab = usar_lab

    def requiere_laboratorio(self):
        return self.usar_lab
        
#curso
class Curso:
    def __init__(self, paralelo: str, semestre: str, peridodo: str):
        if not paralelo.strip():
            raise ValueError("debe de ingresar el paralelo")
        if not semestre.strip():
            raise ValueError("debe de ingresar el semestre")
        if not peridodo.strip():
            raise ValueError("debe de ingresar el periodo")
        self.paralelo = paralelo.strip()
        self.semestre = semestre.strip()
        self.periodo = peridodo.strip()
        
#horario
class Horario:
    def __init__(self, perido: str, horas_inicio: int, hora_fin: int):
        if horas_inicio < 7:
            raise ValueError("las clases no pueden ser tan trempranas")
        if hora_fin > 19:
            raise ValueError("las clases no pueden ser tan tarde")
        if hora_fin <= horas_inicio:
            raise ValueError("la hora de fin debe ser mayor que la de inicio")
        self.periodo = perido.strip()
        self.hora_inicio = horas_inicio
        self.hora_fin = hora_fin

    def duracion(self):
        return self.hora_fin - self.hora_inicio

    def se_cruza_con(self, otro):
        return (self.periodo == otro.periodo
                and self.hora_inicio < otro.hora_fin
                and otro.hora_inicio < self.hora_fin)


#inyeccion de dependencias
class Notificador(ABC):
    @abstractmethod
    def enviar(self, destinatario: str, mensaje: str):
        pass

class NotificadorConsola(Notificador):
    def enviar(self, destinatario, mensaje):
        print(f"[correo a {destinatario}] {mensaje}")

#asignacion: une docente, materia, curso, horario y espacio
class Asignacion:
    def __init__(self, docente: Docente, materia: Materia, curso: Curso,
                 horario: Horario, espacio: EspacioEstudio):
        if not isinstance(docente, Docente):
            raise ValueError("debe asignar un docente")
        if not espacio.admite(materia):
            raise ValueError("el espacio no es adecuado para la materia")
        self.docente = docente
        self.materia = materia
        self.curso = curso
        self.horario = horario
        self.espacio = espacio

#servicio: el notificador se INYECTA por el constructor
class ServicioAsignaciones:
    def __init__(self, notificador: Notificador):
        self.__notificador = notificador
        self.asignaciones = []

    def asignar(self, docente, materia, curso, horario, espacio):
        nueva = Asignacion(docente, materia, curso, horario, espacio)
        for a in self.asignaciones:
            if a.horario.se_cruza_con(horario) and (a.espacio is espacio or a.docente is docente):
                raise ValueError("cruce de horario con otra asignacion")
        self.asignaciones.append(nueva)
        self.__notificador.enviar(
            docente.correo,
            f"Se le asigno {materia.nombre} en {espacio.descripcion()}")
        return nueva
