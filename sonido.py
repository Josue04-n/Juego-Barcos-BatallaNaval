import pygame
class Sonido:
    def __init__(self, ruta_musica_fondo = "audio/Musica_Fondo.mp3",
                 ruta_dispraro="audio/explosion.mp3",
                 ruta_cofre="audio/gold_coins.mp3",
                 ruta_barco="audio/barco_hundido.wav",
                 ruta_disparo_fallido = "audio/disparo_fallido.wav"
                 ):
        pygame.mixer.init()
        
        self.musica_fondo= ruta_musica_fondo
        self.sonido_disparo = None
        self.sonido_cofre = None
        self.sonido_barco = None
        self.sonido_disparo_fallido = None
        
        
        #musica fondo
        try: 
            pygame.mixer.music.load(self.musica_fondo)
        except pygame.error as e:
            print("Error al cargar la musica: {e}")
        #efectos de sonido
        
        try:
            self.sonido_disparo = pygame.mixer.Sound(ruta_dispraro)
        except pygame.error as e:
            print(f"Error al cargar sonido de disparo: {e}")
        
        try: 
            self.sonido_cofre = pygame.mixer.Sound(ruta_cofre)
        except pygame.error as e:
            print(f"Error al cargar sonido del cofre: {e}")
        
        try: 
            self.sonido_barco = pygame.mixer.Sound(ruta_barco)
        except pygame.error as e:
            print(f"Error al cargar sonido del barco: {e}")
        
        try: 
            self.sonido_disparo_fallido = pygame.mixer.Sound(ruta_disparo_fallido)
        except pygame.error as e:
            print(f"Error al cargar sonido del barco: {e}")
            
            
            
    def reproducir_musica_fondo(self, loops=-1):
        try:
            pygame.mixer.music.play(loops)
        except pygame.error as e:
            print(f"Error al reproducir la musica de fondo: {e}")
    
    def parar_musica_fondo(self):
        pygame.mixer.music.stop()
    
    def reproducir_disparo(self):
        if self.sonido_disparo:
            self.sonido_disparo.play()
            
    def reproducir_cofre(self):
        if self.sonido_cofre:
            self.sonido_cofre.play()

    def reproducir_barco(self):
        if self.sonido_barco:
            self.sonido_barco.play()
    
    def reproducir_disparo_fallido(self):
        if self.sonido_disparo_fallido:
            self.sonido_disparo_fallido.play()
    
        