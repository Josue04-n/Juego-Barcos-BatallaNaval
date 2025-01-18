import sys
import json
import tkinter as tk
import pygame
from PIL import Image, ImageTk
from tkinter import messagebox
from db.base_datos import BaseDatos
from tablero import Tablero
from barco import Barco
from jugador import Jugador
from sonido import Sonido
from p2p_network import PeerConnection
from datetime import datetime
import sqlite3




class PantallaInicio:
    def __init__(self, root, iniciar_juego_callback):
        self.db = BaseDatos()
        self.root = root
        self.root.title("Pantalla de Inicio")
        self.root.geometry("1000x700")
        self.root.resizable(False, False)
        self.iniciar_juego_callback = iniciar_juego_callback
        self.sonido = Sonido()
        self.sonido.reproducir_musica_fondo()

        # Fondo principal con la imagen del barco
        try:
            self.fondo_barco = ImageTk.PhotoImage(
                Image.open("images/pantalla_inicio/background.jpg").resize((1000, 700))
            )
        except Exception as e:
            print(f"Error al cargar la imagen del barco: {e}")
            self.fondo_barco = None

        if self.fondo_barco:
            fondo_label = tk.Label(self.root, image=self.fondo_barco)
            fondo_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Cofre encima del barco
        try:
            self.cofre_img = ImageTk.PhotoImage(
                Image.open("images/pantalla_inicio/overlap.jpg").resize((300, 200))
            )
        except Exception as e:
            print(f"Error al cargar la imagen del cofre: {e}")
            self.cofre_img = None

        if self.cofre_img:
            cofre_label = tk.Label(self.root, image=self.cofre_img, bg="black")
            cofre_label.place(relx=0.5, rely=0.6, anchor="center")

        # Título
        titulo_label = tk.Label(
            self.root,
            text="¡Bienvenido al Tesoro de los Mares!",
            font=("Georgia", 24, "bold"),
            bg="black",
            fg="gold"
        )
        titulo_label.place(relx=0.5, rely=0.15, anchor="center")

        # Entrada para el nombre
        self.entrada_nombre = tk.Entry(self.root, font=("Georgia", 16), justify="center")
        self.entrada_nombre.place(relx=0.5, rely=0.65, anchor="center", width=200)

        # Botón para confirmar el nombre
        boton_empezar = tk.Button(
            self.root,
            text="¡Comenzar!",
            font=("Chiller", 20, "bold"),
            bg="#FFD700",
            fg="black",
            command=self.guardar_nombre_y_iniciar
        )
        boton_empezar.place(relx=0.5, rely=0.75, anchor="center")

    def guardar_nombre_y_iniciar(self):
        nombre = self.entrada_nombre.get().strip()
        if nombre:
            self.root.destroy()  # Cerrar la ventana de inicio
            self.iniciar_juego_callback(self.db, nombre)
        else:
            tk.messagebox.showwarning("Nombre vacío", "Por favor, introduce tu nombre antes de continuar.")


class BatallaNavalApp:
    def __init__(self, root, db, jugador_nombre, local_ip=None, remote_ip=None):
        self.conn = sqlite3.connect('db/batalla_naval.db')
        self.cursor = self.conn.cursor()
        self.local_ip = local_ip
        self.remote_ip = remote_ip
        
        pygame.mixer.init()
        self.db = db
        self.root = root
        self.jugador_nombre = jugador_nombre
        self.sonido = Sonido()

        # Config ventana
        self.icono = tk.PhotoImage(file="images/favicon/icono.png")
        self.root.iconphoto(False, self.icono)
        self.root.title("Batalla Naval P2P" if local_ip else "Batalla Naval")
        self.root.geometry("1000x700")
        self.root.resizable(False, False)

        # Jugador
        self.jugador = Jugador(jugador_nombre)

        # Cargar imágenes, tablero, etc.
        self.cargar_imagenes()

        self.sonido.reproducir_musica_fondo()

        # Fondo principal
        try:
            self.fondo_principal = ImageTk.PhotoImage(
                Image.open("images/tablero/fondo_principal.webp").resize((1000, 700))
            )
            fondo_label = tk.Label(self.root, image=self.fondo_principal)
            fondo_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"Error al cargar el fondo principal: {e}")
            messagebox.showerror(
                "Error de fondo",
                "No se pudo cargar el fondo principal. Verifica que la imagen existe."
            )

        # Crear Barcos
        self.barcos = [
            Barco("Barco Horizontal Grande", 5, "horizontal"),
            Barco("Barco Vertical Grande", 5, "vertical"),
            Barco("Barco Horizontal Pequeño", 4, "horizontal"),
            Barco("Barco Vertical Pequeño", 4, "vertical"),
        ]
        self.barco_actual = None

        # P2P: si tenemos IPs
        self.peer = None
        if self.local_ip and self.remote_ip:
            self.peer = PeerConnection(
                local_ip=self.local_ip,
                local_port=5000,
                remote_ip=self.remote_ip,
                remote_port=5000,
                on_data_received_callback=self.on_data_received
            )
            self.peer.start()

        # Interfaz
        self.crear_zona_estadisticas()
        self.crear_zona_control()
        self.crear_tablero_colocacion()

 
    def on_data_received(self, raw_data):
        """Callback al recibir datos del peer (JSON)."""
        try:
            data = json.loads(raw_data)
            tipo = data.get("tipo")
        
            if tipo == "VOLVER_A_JUGAR":
                jugador = data.get("jugador", "Desconocido")
                self.mostrar_mensaje_personalizado(
                    "Solicitud de Juego",
                    f"El jugador {jugador} desea volver a jugar."
                )

            if tipo == "DISPARAR":
                x = data["x"]
                y = data["y"]
                self._disparo_remoto(x, y)

            elif tipo == "COLOCAR_BARCO":
                barco_nombre = data["barco_nombre"]
                x = data["x"]
                y = data["y"]
                self._colocar_barco_remoto(barco_nombre, x, y)

            else:
                print("Evento desconocido:", data)
        except json.JSONDecodeError:
            print("Error al decodificar JSON; ", raw_data)
        except Exception as e:
            print(f'Error inesperado', {e})

    def _disparo_remoto(self, x, y):
        """Cuando el otro peer dispara en nuestra matriz."""
        if self.tablero.disparos_realizados.get((x, y)) is not None:
            return
        self.disparar(x, y)

    def _colocar_barco_remoto(self, barco_nombre, x, y):
        """Cuando el otro peer coloca un barco en nuestro tablero."""
        barco = None
        for b in self.barcos:
            if b.nombre == barco_nombre:
                barco = b
                break
        if not barco:
            print(f"No encontré el barco: {barco_nombre}")
            return
        if barco.colocado:
            print(f"El barco {barco.nombre} ya está colocado.")
            return

        if self.tablero.es_posicion_valida_para_colocar(barco, x, y):
            self.tablero.colocar_barco(barco, x, y)
            for (bx, by) in barco.posicion:
                self.canvas_colocacion.create_image(by * 50, bx * 50, image=self.img_barco, anchor="nw")
            barco.colocado = True
            barco.boton.config(state=tk.DISABLED)

    def enviar_disparo(self, x, y):
        """Notifica al peer que disparamos en (x,y)."""
        if self.peer:
            data = {
                "tipo": "DISPARAR",
                "x": x,
                "y": y
            }
            self.peer.send_message(json.dumps(data))

    def enviar_colocacion_barco(self, barco, x, y):
        """Notifica al peer que colocamos un barco."""
        if self.peer:
            data = {
                "tipo": "COLOCAR_BARCO",
                "barco_nombre": barco.nombre,
                "x": x,
                "y": y
            }
            self.peer.send_message(json.dumps(data))

    def stop_peer(self):
        if self.peer:
            self.peer.stop()
    def cargar_imagenes(self):
        try:
            self.img_pergamino = ImageTk.PhotoImage(Image.open("images/tablero/pergamino.png").resize((600, 100)))
            self.img_fallo = ImageTk.PhotoImage(Image.open("images/tablero/disparo_fallido.png").resize((50, 50)))
            self.img_mar = ImageTk.PhotoImage(Image.open("images/tablero/Mar.jpg").resize((50, 50)))
            self.img_cofre = ImageTk.PhotoImage(Image.open("images/tablero/Tesoro.png").resize((50, 50)))
            self.img_fondo_colocacion = ImageTk.PhotoImage(
                Image.open("images/tablero/fondo_pirata.jpg").resize((500, 500))
            )
            self.img_barco = ImageTk.PhotoImage(Image.open("images/tablero/Barco.png").resize((50, 50)))
            self.img_explosion = ImageTk.PhotoImage(
                Image.open("images/tablero/Explosion.webp").resize((50, 50))
            )
        except Exception as e:
            messagebox.showerror("Error de imagen", f"No se pudo cargar una imagen: {e}")
            self.root.quit()
        self.tablero = Tablero()

    def crear_zona_control(self):
        self.zona_control = tk.Frame(self.root, bg="#8B4513")
        self.zona_control.pack(side=tk.LEFT, padx=20, pady=20, fill="y")

        barcos_frame = tk.LabelFrame(
            self.zona_control,
            text="Selecciona un barco:",
            font=("Chiller", 24, "bold"),
            bg="#8B4513",
            fg="gold",
            bd=3,
            relief="groove",
            labelanchor="n"
        )
        barcos_frame.pack(padx=10, pady=10, fill="x")

        botones_frame = tk.Frame(barcos_frame, bg="#8B4513")
        botones_frame.pack(pady=(10, 20))

        for i, barco in enumerate(self.barcos):
            boton = tk.Button(
                botones_frame,
                text=barco.nombre,
                font=("Times New Roman", 12),
                bg="#FFD700",
                fg="black",
                relief="raised",
                bd=2,
                command=lambda b=barco: self.seleccionar_barco(b)
            )
            boton.grid(row=i // 2, column=i % 2, padx=10, pady=10)
            barco.boton = boton

        iniciar_frame = tk.Frame(self.zona_control, bg="#8B4513")
        iniciar_frame.pack(pady=20)

        self.boton_iniciar = tk.Button(
            iniciar_frame,
            text="Iniciar Juego",
            font=("Chiller", 18, "bold"),
            bg="#FFD700",
            fg="black",
            activebackground="#DAA520",
            activeforeground="white",
            bd=4,
            relief="raised",
            command=lambda: self.iniciar_juego(self.jugador_nombre)
        )
        self.boton_iniciar.pack()
        
        self.boton_estadisticas = tk.Button(
            iniciar_frame,
            text="Estadísticas",
            font=("Chiller", 18, "bold"),
            bg="#FFD700",
            fg="black",
            activebackground="#DAA520",
            activeforeground="white",
            bd=4,
            relief="raised",
            command=self.mostrar_estadisticas
        )
        self.boton_estadisticas.pack(pady=10)
        



        # Imagen decorativa (fondo pirata)
        try:
            img_fondo_pirata = ImageTk.PhotoImage(
                Image.open("images/tablero/fondo_pirata.jpg").resize((200, 150))
            )
            fondo_pirata_label = tk.Label(self.zona_control, image=img_fondo_pirata, bg="#8B4513")
            fondo_pirata_label.image = img_fondo_pirata
            fondo_pirata_label.pack(pady=(10, 0))
        except Exception as e:
            print(f"Error al cargar la imagen fondo_pirata: {e}")
            
            

    def mostrar_estadisticas(self):
        resultados = self.obtener_mejores_resultados()
        if resultados:
            mensaje = "\n".join(
                f"{nombre}: {puntuacion} puntos, {disparos_usados} disparos (Eficiencia: {eficiencia:.2f}) - {fecha}"
                for nombre, puntuacion, disparos_usados, fecha, eficiencia in resultados
            )
        else:
            mensaje = "No se encontraron resultados."

        tk.messagebox.showinfo("Estadísticas", mensaje)
    
    def obtener_mejores_resultados(self, limite=3):
        """Obtiene los mejores resultados basados en una métrica de eficiencia."""
        try:
            self.cursor.execute('''
                SELECT nombre, puntuacion, disparos_usados, fecha,
                    CAST(puntuacion AS FLOAT) / disparos_usados AS eficiencia
                FROM jugadores
                ORDER BY eficiencia DESC
                LIMIT ?
            ''', (limite,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al obtener los mejores resultados: {e}")
            return []
        
    def seleccionar_barco(self, barco):
        if barco.colocado:
            messagebox.showwarning("Barco ya colocado", f"El {barco.nombre} ya ha sido colocado.")
            return
        self.barco_actual = barco
        self.mostrar_mensaje_personalizado(
            "Seleccionar Barco",
            f"Selecciona una celda en el tablero para colocar el {barco.nombre}."
        )

    def crear_tablero_colocacion(self):
        """Crea el tablero de colocación."""
        self.tablero_colocacion_frame = tk.Frame(self.root)
        self.tablero_colocacion_frame.pack(side=tk.RIGHT, padx=10, pady=10)

        self.canvas_colocacion = tk.Canvas(self.tablero_colocacion_frame, width=500, height=500)
        self.canvas_colocacion.pack()

        self.canvas_colocacion.create_image(0, 0, image=self.img_fondo_colocacion, anchor="nw", tags="fondo_mar")

        # Crear los barcos en el tablero
        for x in range(10):
            for y in range(10):
                self.canvas_colocacion.create_image(
                    y * 50, x * 50, image=self.img_mar, anchor="nw", tags="mar"
                )
                rect = self.canvas_colocacion.create_rectangle(
                    y * 50, x * 50, y * 50 + 50, x * 50 + 50, outline="", fill="", tags=f"celda_{x}_{y}"
                )
                self.canvas_colocacion.tag_bind(
                    rect, "<Button-1>", lambda event, rx=x, ry=y: self.manejar_colocacion_barco(rx, ry)
                )

        # Ocultar barcos temporalmente
        for barco_tag in self.canvas_colocacion.find_withtag("barco"):
            self.canvas_colocacion.itemconfigure(barco_tag, state="hidden")

        # Enviar el mensaje para ocultar el tablero del jugador
        if self.peer:
            self.peer.send_message(json.dumps({"tipo": "OCULTAR_TABLERO"}))



    def manejar_colocacion_barco(self, x, y):
        if not self.barco_actual:
            self.mostrar_mensaje_personalizado(
                "Seleccionar Barco",
                "Selecciona un barco antes de colocarlo."
            )
            return

        if self.tablero.es_posicion_valida_para_colocar(self.barco_actual, x, y):
            self.tablero.colocar_barco(self.barco_actual, x, y)
            for (bx, by) in self.barco_actual.posicion:
                self.canvas_colocacion.create_image(by * 50, bx * 50, image=self.img_barco, anchor="nw")

            self.barco_actual.colocado = True
            self.barco_actual.boton.config(state=tk.DISABLED)

            # Enviar info al peer
            self.enviar_colocacion_barco(self.barco_actual, x, y)

            self.barco_actual = None
        else:
            self.mostrar_mensaje_personalizado(
                "Colocación inválida",
                "No puedes colocar el barco aquí. Intenta en otra posición."
            )

    def verificar_barcos_colocados(self):
        return all(barco.colocado for barco in self.barcos)

    def crear_tablero_disparos(self):
        self.tablero_disparos_frame = tk.Frame(self.root, bg="#8B4513", relief="groove", bd=5)
        self.tablero_disparos_frame.pack(pady=20)

        titulo_tablero = tk.Label(
            self.tablero_disparos_frame,
            text="Tablero de Disparos",
            font=("Chiller", 24, "bold"),
            bg="#8B4513",
            fg="gold"
        )
        titulo_tablero.pack(pady=10)

        self.canvas_disparos = tk.Canvas(
            self.tablero_disparos_frame,
            width=500,
            height=500,
            bg="#000080",
            bd=0,
            highlightthickness=0
        )
        self.canvas_disparos.pack()
        self.canvas_disparos.bind("<Motion>", self.dibujar_mira)
        self.canvas_disparos.bind("<Button-1>", self.manejar_disparo)

        for x in range(10):
            for y in range(10):
                self.canvas_disparos.create_image(y * 50, x * 50, image=self.img_mar, anchor="nw")
                rect = self.canvas_disparos.create_rectangle(
                    y * 50, x * 50, y * 50 + 50, x * 50 + 50,
                    outline="#FFFFFF", width=1, tags=f"celda_{x}_{y}"
                )

    def disparar(self, x, y):
        resultado = self.tablero.disparar(x, y)

        if resultado == "B":
            self.jugador.incrementar_puntuacion(20)
            explosion_id = self.canvas_disparos.create_image(
                y * 50, x * 50, image=self.img_explosion, anchor="nw"
            )
            self.root.after(1000, lambda: self.revelar_barco(x, y, explosion_id))

        elif resultado == "C":
            self.jugador.incrementar_puntuacion(10)
            explosion_id = self.canvas_disparos.create_image(
                y * 50, x * 50, image=self.img_explosion, anchor="nw"
            )
            self.root.after(1000, lambda: self.revelar_cofre(x, y, explosion_id))

        elif resultado == "agua":
            fallo_id = self.canvas_disparos.create_image(
                y * 50, x * 50, image=self.img_fallo, anchor="nw"
            )
            self.sonido.reproducir_disparo_fallido()

        else:
            self.mostrar_mensaje_personalizado("Ya Disparaste", "Ya has disparado en esta casilla. Intenta en otra.")

        self.jugador.registrar_disparo()
        self.actualizar_estadisticas()

        # Avisar al peer si es un disparo local
        self.enviar_disparo(x, y)

        # Verificar si se hundieron todos los barcos
        if self.tablero.todos_barcos_hundidos():
            self.finalizar_juego()

    def manejar_disparo(self, event):
        self.sonido.reproducir_disparo()
        x = event.y // 50
        y = event.x // 50
        if self.tablero.disparos_realizados.get((x, y)) is not None:
            self.mostrar_mensaje_personalizado("Casilla Ocupada", "Ya has disparado en esta casilla. Intenta en otra.")
            return
        self.disparar(x, y)

    def dibujar_mira(self, event):
        self.canvas_disparos.delete("mira")
        x, y = event.x, event.y
        self.canvas_disparos.create_line(x - 10, y, x + 10, y, fill="red", width=2, tags="mira")
        self.canvas_disparos.create_line(x, y - 10, x, y + 10, fill="red", width=2, tags="mira")
        self.canvas_disparos.create_oval(x - 8, y - 8, x + 8, y + 8, outline="red", width=2, tags="mira")

    def crear_zona_estadisticas(self):
        self.zona_estadisticas = tk.Frame(self.root, bg="#8B4513", height=100, relief="groove", bd=3)
        self.zona_estadisticas.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        pergamino_label = tk.Label(self.zona_estadisticas, image=None, bg="#8B4513")
        pergamino_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.zona_estadisticas.pack_forget()

        # Intentamos poner el pergamino
        try:
            pergamino_img = ImageTk.PhotoImage(
                Image.open("images/tablero/pergamino.png").resize((600, 100))
            )
            pergamino_label.config(image=pergamino_img)
            pergamino_label.image = pergamino_img
        except:
            pass

        titulo_label = tk.Label(
            self.zona_estadisticas,
            text="Estadísticas del Jugador",
            font=("Chiller", 24, "bold"),
            bg="#8B4513",
            fg="gold"
        )
        titulo_label.pack(anchor="center", pady=5)

        stats_frame = tk.Frame(self.zona_estadisticas, bg="#8B4513")
        stats_frame.pack()

        self.etiqueta_nombre = tk.Label(
            stats_frame,
            text=f"Jugador: {self.jugador.nombre}",
            font=("Chiller", 20),
            bg="#8B4513",
            fg="white"
        )
        self.etiqueta_nombre.grid(row=0, column=0, padx=(20, 10))

        self.etiqueta_puntuacion = tk.Label(
            stats_frame,
            text=f"Puntuación: {self.jugador.puntuacion}",
            font=("Chiller", 20),
            bg="#8B4513",
            fg="gold"
        )
        self.etiqueta_puntuacion.grid(row=0, column=1, padx=(20, 10))

        self.etiqueta_disparos = tk.Label(
            stats_frame,
            text=f"Disparos: {self.jugador.disparos_realizados}",
            font=("Chiller", 20),
            bg="#8B4513",
            fg="red"
        )
        self.etiqueta_disparos.grid(row=0, column=2, padx=(20, 10))

    def iniciar_juego(self, nombre_jugador):
        # Verificar si todos los barcos han sido colocados
        if not self.verificar_barcos_colocados():
            self.mostrar_mensaje_personalizado(
                "Barcos pendientes",
                f"Hola {nombre_jugador}, debes colocar todos los barcos en el tablero antes de iniciar el juego."
            )
            return

        soy_host = (self.peer is not None and True)

        if soy_host:
            # Notificar al jugador que debe ocultar el tablero antes de cualquier otra acción
            self.peer.send_message(json.dumps({"tipo": "OCULTAR_TABLERO"}))

        # Proceder con la colocación de cofres
        self.tablero.colocar_cofres()

        if soy_host:
            # Enviar las posiciones de los cofres al jugador después de colocarlos
            lista_cofres = list(self.tablero.coferes)[:3]
            data = {
                "tipo": "COFRES_POSICIONES",
                "cofres": lista_cofres
            }
            self.peer.send_message(json.dumps(data))

        # Ocultar controles de colocación y preparar la interfaz para el juego
        self.zona_control.pack_forget()
        self.tablero_colocacion_frame.pack_forget()
        self.zona_estadisticas.pack()
        self.actualizar_estadisticas()
        self.crear_tablero_disparos()

        # Mostrar mensaje de inicio del juego
        self.mostrar_mensaje_personalizado(
            "¡Juego Iniciado!",
            f"¡{nombre_jugador}, todos los barcos han sido colocados! "
            "Ahora comienza la batalla. Intenta hundir los barcos enemigos y encontrar los cofres."
        )




    def revelar_barco(self, x, y, explosion_id):
        self.canvas_disparos.delete(explosion_id)
        self.canvas_disparos.create_image(y * 50, x * 50, image=self.img_barco, anchor="nw")
        self.sonido.reproducir_barco()

    def revelar_cofre(self, x, y, explosion_id):
        self.canvas_disparos.delete(explosion_id)
        self.canvas_disparos.create_image(y * 50, x * 50, image=self.img_cofre, anchor="nw")
        self.sonido.reproducir_cofre()

    def actualizar_estadisticas(self):
        self.etiqueta_nombre.config(text=f"Jugador: {self.jugador.nombre}")
        self.etiqueta_puntuacion.config(text=f"Puntuación: {self.jugador.puntuacion}")
        self.etiqueta_disparos.config(text=f"Disparos: {self.jugador.disparos_realizados}")

    def mostrar_mensaje_personalizado(self, titulo, mensaje):
        ventana_mensaje = tk.Toplevel(self.root)
        ventana_mensaje.title(titulo)
        ventana_mensaje.geometry("400x200")
        ventana_mensaje.resizable(False, False)

        try:
            icono_mensaje = tk.PhotoImage(file="images/favicon/icono_mensajes.png")
            ventana_mensaje.iconphoto(False, icono_mensaje)
        except:
            pass

        # Fondo pergamino
        try:
            img_fondo = ImageTk.PhotoImage(
                Image.open("images/mensajes/pergamino_mensaje.jpg").resize((400, 200))
            )
        except:
            img_fondo = None

        if img_fondo:
            fondo_label = tk.Label(ventana_mensaje, image=img_fondo)
            fondo_label.place(x=0, y=0, relwidth=1, relheight=1)
            fondo_label.image = img_fondo

        titulo_label = tk.Label(
            ventana_mensaje,
            text=titulo,
            font=("Georgia", 18, "bold"),
            bg="#8B4513",
            fg="gold"
        )
        titulo_label.place(relx=0.5, rely=0.2, anchor="center")

        mensaje_label = tk.Label(
            ventana_mensaje,
            text=mensaje,
            font=("Book Antiqua", 14),
            bg="#8B4513",
            fg="white",
            wraplength=350,
            justify="center"
        )
        mensaje_label.place(relx=0.5, rely=0.5, anchor="center")

        cerrar_boton = tk.Button(
            ventana_mensaje,
            text="Cerrar",
            font=("Georgia", 12, "bold"),
            bg="#FFD700",
            fg="black",
            command=ventana_mensaje.destroy
        )
        cerrar_boton.place(relx=0.5, rely=0.8, anchor="center")

    def finalizar_juego(self):
        puntuacion_final = self.jugador.puntuacion
        try:
            self.db.guardar_resultados(
                self.jugador.nombre,
                puntuacion_final,
                self.jugador.disparos_realizados
            )
        except Exception as e:
            print(f"Error al guardar resultados en la base de datos: {e}")

        self.mostrar_estadisticas_finales()
        self.mostrar_ventana_juego_terminado(puntuacion_final)

    def mostrar_estadisticas_finales(self):
        """Muestra las estadísticas finales con los mejores resultados."""
        ventana_estadisticas = tk.Toplevel(self.root)
        ventana_estadisticas.title("Mejores Estadísticas")
        ventana_estadisticas.geometry("1000x700")
        ventana_estadisticas.resizable(False, False)

        # Fondo
        try:
            img_fondo = ImageTk.PhotoImage(
                Image.open("images/estadisticas/estadisticas_finales.webp").resize((1000, 700))
            )
        except Exception as e:
            print(f"Error al cargar la imagen de fondo: {e}")
            img_fondo = None

        if img_fondo:
            fondo_label = tk.Label(ventana_estadisticas, image=img_fondo)
            fondo_label.place(x=0, y=0, relwidth=1, relheight=1)
            fondo_label.image = img_fondo

        frame_central = tk.Frame(ventana_estadisticas, bg="#8B4513", highlightthickness=0)
        frame_central.place(relx=0.5, rely=0.5, anchor="center", width=800, height=600)

        titulo_label = tk.Label(
            frame_central,
            text="Estadísticas Finales",
            font=("Georgia", 30, "bold"),
            bg=None,
            fg="black"
        )
        titulo_label.pack(pady=20)

        # Obtener datos de la DB
        mejores_resultados = sorted(
            self.db.obtener_mejores_resultados(),
            key=lambda x: (-x[1], x[2])
        )[:3]

        encabezados = ["Posición", "Pirata", "Score", "Disparos", "Insignia"]
        encabezados_frame = tk.Frame(frame_central, bg="#8B4513")
        encabezados_frame.pack(pady=(0, 10))

        for i in range(len(encabezados)):
            encabezados_frame.grid_columnconfigure(i, weight=1, uniform="col")

        for col, encabezado in enumerate(encabezados):
            tk.Label(
                encabezados_frame,
                text=encabezado,
                font=("Georgia", 16, "bold"),
                bg="#8B4513",
                fg="gold",
                anchor="center"
            ).grid(row=0, column=col, padx=20, pady=10, sticky="nsew")

        frases = ["Rey/na Naval", "Capitán/a", "Aventurero/a"]
        premios = [
            "images/insignia/Primer_Lugar.webp",
            "images/insignia/Segundo_Lugar.webp",
            "images/insignia/Tercer_Lugar.webp"
        ]
        premios_imgs = []
        for premio in premios:
            try:
                img = ImageTk.PhotoImage(Image.open(premio).resize((100, 100)))
                premios_imgs.append(img)
            except Exception as e:
                print(f"Error al cargar imagen del premio {premio}: {e}")
                premios_imgs.append(None)

        resultados_frame = tk.Frame(frame_central, bg="#8B4513")
        resultados_frame.pack()

        for i in range(len(encabezados)):
            resultados_frame.grid_columnconfigure(i, weight=1, uniform="col")

        for row, resultado in enumerate(mejores_resultados, start=1):
            tk.Label(
                resultados_frame,
                text=row,
                font=("Georgia", 14),
                bg="#8B4513",
                fg="gold",
                anchor="center"
            ).grid(row=row, column=0, padx=20, pady=10, sticky="nsew")

            for col, valor in enumerate(resultado[:3]):
                tk.Label(
                    resultados_frame,
                    text=valor,
                    font=("Georgia", 14),
                    bg="#8B4513",
                    fg="gold",
                    anchor="center"
                ).grid(row=row, column=col + 1, padx=20, pady=10, sticky="nsew")

            # Insignia + Frase
            if row <= 3 and premios_imgs[row - 1]:
                insignia_frame = tk.Frame(resultados_frame, bg="#8B4513")
                insignia_frame.grid(row=row, column=len(encabezados) - 1,
                                    padx=20, pady=10, sticky="nsew")

                insignia_label = tk.Label(
                    insignia_frame,
                    image=premios_imgs[row - 1],
                    bg="#8B4513",
                    anchor="center"
                )
                insignia_label.pack()

                frase_label = tk.Label(
                    insignia_frame,
                    text=frases[row - 1],
                    font=("Georgia", 12, "italic"),
                    bg="#8B4513",
                    fg="gold",
                    anchor="center"
                )
                frase_label.pack()

        boton_cerrar = tk.Button(
            frame_central,
            text="Cerrar",
            font=("Georgia", 16, "bold"),
            bg="#8B4513",
            fg="gold",
            command=ventana_estadisticas.destroy
        )
        boton_cerrar.pack(pady=30)

        self.root.wait_window(ventana_estadisticas)

    def mostrar_ventana_juego_terminado(self, puntuacion_final):
        """Muestra la ventana de 'Juego Terminado' con opciones."""
        ventana_final = tk.Toplevel(self.root)
        ventana_final.title("Juego Terminado")
        ventana_final.geometry("1000x700")
        ventana_final.resizable(False, False)

        # Fondo temático
        try:
            img_fondo = ImageTk.PhotoImage(
                Image.open("images/finish/background.webp").resize((1000, 700))
            )
        except Exception as e:
            print(f"Error al cargar la imagen de fondo: {e}")
            img_fondo = None

        if img_fondo:
            fondo_label = tk.Label(ventana_final, image=img_fondo)
            fondo_label.place(x=0, y=0, relwidth=1, relheight=1)
            fondo_label.image = img_fondo

        # Título "Misión Cumplida"
        titulo_label = tk.Label(
            ventana_final,
            text="¡Misión Cumplida!",
            font=("Georgia", 20, "bold"),
            bg="#8B4513",
            fg="gold"
        )
        titulo_label.place(relx=0.5, rely=0.2, anchor="center")

        # Mensaje de agradecimiento
        mensaje_label = tk.Label(
            ventana_final,
            text=(
                f"¡Felicidades Pirata {self.jugador.nombre}!\n"
                f"Puntuación Final: {puntuacion_final}\n"
                "¿Qué deseas hacer ahora?"
            ),
            font=("Book Antiqua", 14),
            bg="#8B4513",
            fg="white",
            wraplength=450,
            justify="center"
        )
        mensaje_label.place(relx=0.5, rely=0.3, anchor="center")

        # Imagen decorativa (pirata)
        try:
            img_decoracion = Image.open("images/finish/finalizar_juego.webp").resize((200, 200))
            img_decoracion_tk = ImageTk.PhotoImage(img_decoracion)
        except Exception as e:
            print(f"Error al cargar la imagen decorativa: {e}")
            img_decoracion_tk = None

        if img_decoracion_tk:
            decoracion_label = tk.Label(
                ventana_final,
                image=img_decoracion_tk,
                bg="#8B4513"
            )
            decoracion_label.image = img_decoracion_tk
            decoracion_label.place(relx=0.5, rely=0.55, anchor="center")

        # Botón para volver a jugar
        boton_reiniciar = tk.Button(
            ventana_final,
            text="Volver a Jugar",
            font=("Georgia", 12, "bold"),
            bg="#FFD700",
            fg="black",
            command=lambda: self.reiniciar_juego(ventana_final)
        )
        boton_reiniciar.place(relx=0.4, rely=0.8, anchor="center")

        # Botón para salir
        boton_salir = tk.Button(
            ventana_final,
            text="Salir",
            font=("Georgia", 12, "bold"),
            bg="#FF4500",
            fg="white",
            command=self.root.quit
        )
        boton_salir.place(relx=0.6, rely=0.8, anchor="center")

    def reiniciar_juego(self, ventana):
        ventana.destroy()
        if self.peer:
            self.peer.stop()

        self.root.destroy()
        
        nuevo_root = tk.Tk()
        nuevo_root.geometry("1000x700")
        nuevo_root.resizable(False, False)

        nueva_app = BatallaNavalApp(nuevo_root, self.db, self.jugador_nombre, self.local_ip, self.remote_ip)
        nuevo_root.mainloop()



def iniciar_juego(db, nombre_jugador, local_ip=None, remote_ip=None):
    """Se llama cuando PantallaInicio cierra y pasa el nombre."""
    root = tk.Tk()
    app = BatallaNavalApp(root, db, nombre_jugador, local_ip, remote_ip)
    root.mainloop()


if __name__ == "__main__":
    local_ip = None
    remote_ip = None

    if len(sys.argv) >= 3:
        local_ip = sys.argv[1]
        remote_ip = sys.argv[2]

    root = tk.Tk()
    icono = tk.PhotoImage(file="images/favicon/icono.png")
    root.iconphoto(False, icono)
    root.geometry("1000x600")
    root.resizable(False, False)

    pantalla_inicio = PantallaInicio(
        root,
        lambda db, nombre: iniciar_juego(db, nombre, local_ip, remote_ip)
    )

    root.mainloop()
