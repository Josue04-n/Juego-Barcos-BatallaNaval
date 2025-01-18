class Barco:
    def __init__(self, nombre, tamano, orientacion):
        self.nombre = nombre
        self.tamano = tamano
        self.orientacion = orientacion  
        self.colocado = False
        self.posicion = []  
        self.hundido = False  

    def verificar_estado(self, disparos_realizados):
        """Verifica si el barco está completamente hundido."""
        for coord in self.posicion:
            if disparos_realizados.get(coord) != "B":
                return False
        return True

    def hundir(self):
        """Marca el barco como hundido."""
        self.hundido = True
