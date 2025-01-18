import tkinter as tk
from p2p_network import PeerConnection
import json

class BatallaNavalP2PApp:
    def __init__(self, root, local_ip, remote_ip):
        self.root = root
        self.root.title("Batalla Naval P2P")
        
        self.port = 5000
        
        self.peer = PeerConnection(
            local_ip=local_ip,
            local_port=self.port,
            remote_ip=remote_ip,
            remote_port=self.port,
            on_data_received_callback=self.on_data_received
        )
        
        self.peer.start()
        
        self.text_area = tk.Text(self.root, width=50, height=10)
        self.text_area.pack()
        
        self.entry = tk.Entry(self.root)
        self.entry.pack()
        
        self.send_button = tk.Button(self.root, text="Enviar", command=self.send_message)
        self.send_button.pack()
        
        self.close_button = tk.Button(self.root, text="Salir", command=self.cerrar)
        self.close_button.pack()
    
    def send_message(self):
       msg = self.entry.get()
       if msg:
          evento = {
              "tipo": "CHAT",
              "texto": msg
          }
          json_msg = json.dumps(evento)
        
          self.text_area.insert(tk.END, f"Tú: {msg}\n")
        
          self.peer.send_message(json_msg)
          self.entry.delete(0, tk.END)
    
    def on_data_received(self, data):
        evento = json.loads(data)
        if evento["tipo"] == "DISPARAR":
            x = evento["x"]
            y = evento["y"]
        elif evento["tipo"] == "COLOCAR_BARCO":
         ...

    
    def cerrar(self):
        """Salir de la app P2P."""
        self.peer.stop()  # Cerrar sockets
        self.root.destroy()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Uso: python main.py <mi_ip> <ip_peer>")
        print("Ejemplo: python main.py 192.168.1.10 192.168.1.11")
        sys.exit(1)
    
    local_ip = sys.argv[1]
    remote_ip = sys.argv[2]
    
    root = tk.Tk()
    app = BatallaNavalP2PApp(root, local_ip, remote_ip)
    root.mainloop()