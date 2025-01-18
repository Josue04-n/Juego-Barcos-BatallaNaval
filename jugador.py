class Jugador:
    def __init__(self, nombre):
        self.nombre = nombre
        self.puntuacion = 0
        self.disparos_realizados= 0

    def registrar_disparo(self):
        """Incrementa el contador de disparos."""
        self.disparos_realizados += 1

    def incrementar_puntuacion(self, puntos):
        """Incrementa la puntuación del jugador."""
        self.puntuacion += puntos
