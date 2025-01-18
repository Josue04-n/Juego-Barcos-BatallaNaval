# tablero.py
import random


class Tablero:
    def __init__(self):
        self.matriz = [["" for _ in range(10)] for _ in range(10)]  # Tablero vacío
        self.coferes = []  # Lista de cofres
        self.barcos = []  # Lista de barcos colocados
        self.disparos_realizados = {}  # Registro de disparos realizados

    def es_posicion_valida_para_colocar(self, barco, x, y):
        """Verifica si la posición es válida para colocar el barco."""
        if barco.orientacion == "horizontal":
            if y + barco.tamano > 10:  # Sale del tablero
                return False
            # Verifica si hay espacio libre
            for i in range(barco.tamano):
                if self.matriz[x][y + i] != "":
                    return False
        elif barco.orientacion == "vertical":
            if x + barco.tamano > 10:  # Sale del tablero
                return False
            # Verifica si hay espacio libre
            for i in range(barco.tamano):
                if self.matriz[x + i][y] != "":
                    return False
        return True

    def colocar_barco(self, barco, x, y):
        """Coloca un barco en el tablero."""
        barco.posicion = []  # Asegurarse de vaciar las posiciones anteriores
        if barco.orientacion == "horizontal":
            for i in range(barco.tamano):
                self.matriz[x][y + i] = "B"
                barco.posicion.append((x, y + i))
        elif barco.orientacion == "vertical":
            for i in range(barco.tamano):
                self.matriz[x + i][y] = "B"
                barco.posicion.append((x + i, y))

        self.barcos.append(barco)  # Añadir el barco al registro

    def colocar_cofres(self):
        """Coloca tres cofres aleatorios en el tablero."""
        cofres_colocados = 0
        while cofres_colocados < 3:
            x = random.randint(0, 9)
            y = random.randint(0, 9)
            if self.matriz[x][y] == "":  # Asegurarse que la casilla esté vacía
                self.matriz[x][y] = "C"
                self.coferes.append((x, y))
                cofres_colocados += 1

    def disparar(self, x, y):
        """Realiza un disparo y devuelve el resultado."""
        if self.disparos_realizados.get((x, y)) is not None:
            return "ya_disparo"  # Ya se disparó aquí

        if self.matriz[x][y] == "B":
            self.disparos_realizados[(x, y)] = "B"
            # Verificar si el barco está hundido
            for barco in self.barcos:
                if (x, y) in barco.posicion:
                    if barco.verificar_estado(self.disparos_realizados):
                        barco.hundir()
            return "B"  # Barco
        elif self.matriz[x][y] == "C":
            self.disparos_realizados[(x, y)] = "C"
            return "C"  # Cofre
        else:
            self.disparos_realizados[(x, y)] = "agua"
            return "agua"  # Agua

    def todos_barcos_hundidos(self):
        """Verifica si todos los barcos han sido hundidos."""
        return all(barco.hundido for barco in self.barcos)
