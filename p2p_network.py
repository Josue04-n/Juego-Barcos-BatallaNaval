import socket
import threading
import time

class PeerConnection:
    def __init__(self, local_ip, local_port, remote_ip, remote_port, on_data_received_callback):

        self.local_ip = local_ip
        self.local_port = local_port
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.on_data_received_callback = on_data_received_callback
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.out_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False
        
    def start(self):
        self.running = True
        
        try:
            self.listen_socket.bind((self.local_ip, self.local_port))
            self.listen_socket.listen(1)
            print(f"[{self.local_ip}] Escuchando en puerto {self.local_port}...")
        except Exception as e:
            print(f"Error al hacer bind/listen: {e}")
            self.running = False
            return
        
        accept_thread = threading.Thread(target=self._accept_connection, daemon=True)
        accept_thread.start()
        
        connect_thread = threading.Thread(target=self._connect_to_remote, daemon=True)
        connect_thread.start()
    
    def _accept_connection(self):
        while self.running:
            try:
                client_socket, addr = self.listen_socket.accept()
                print(f"Conexión entrante desde {addr}")
                
                read_thread = threading.Thread(
                    target=self._handle_incoming_data, 
                    args=(client_socket,),
                    daemon=True
                )
                read_thread.start()
                
            except Exception as e:
                print(f"Error en accept_connection: {e}")
                break
    
    def _connect_to_remote(self):
        while self.running:
            try:
                print(f"[{self.local_ip}] Intentando conectar a {self.remote_ip}:{self.remote_port}...")
                self.out_socket.connect((self.remote_ip, self.remote_port))
                print(f"[{self.local_ip}] Conexión establecida con {self.remote_ip}!")
                break
            except socket.error:
                time.sleep(3)
                continue
    
    def _handle_incoming_data(self, sock):
        while self.running:
            try:
                data = sock.recv(1024)
                if not data:
                    break
                self.on_data_received_callback(data.decode('utf-8'))
            except Exception as e:
                print(f"Error al recibir datos: {e}")
                break
    
    def send_message(self, msg):
        try:
            self.out_socket.sendall(msg.encode('utf-8'))
        except Exception as e:
            print(f"Error al enviar mensaje: {e}")
    
    def stop(self):
        self.running = False
        self.listen_socket.close()
        self.out_socket.close()
