from flask import Flask, render_template, request, redirect, url_for
import pyrad.packet
from pyrad.client import Client
from pyrad.dictionary import Dictionary
from pyrad.packet import AccessRequest, AccessAccept, AccessReject
import hashlib

app = Flask(__name__)

# Configuración del cliente para FreeRADIUS
RADIUS_SERVER = "192.168.201.200"  # Dirección IP de tu servidor FreeRADIUS
RADIUS_PORT = 1812  # Puerto por defecto de RADIUS
SECRET = "secret_key"  # Clave secreta compartida
DICT_PATH = "/etc/freeradius/3.0/dictionary"  # Ruta a tu diccionario RADIUS

# Creación de un cliente RADIUS
client = Client(server=RADIUS_SERVER, secret=SECRET, dict=Dictionary(DICT_PATH))
client.AuthPort = RADIUS_PORT


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if authenticate_user(username, password):
            return redirect(url_for("welcome"))
        else:
            return render_template("login.html", error="Invalid username or password")
    return render_template("login.html", error=None)


def authenticate_user(username, password):
    # Crear un nuevo paquete de solicitud de acceso
    req = client.CreatePacket(packet_type=AccessRequest)

    # Añadir los atributos de User-Name y User-Password
    req.AddAttribute(1, username.encode('utf-8'))  # User-Name
    req.AddAttribute(2, password.encode('utf-8'))  # User-Password

    # Enviar el paquete al servidor y esperar la respuesta
    try:
        reply = client.SendPacket(req)
        if reply.code == AccessAccept:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error during authentication: {e}")
        return False


@app.route("/welcome")
def welcome():
    return render_template("welcome.html")


if __name__ == "__main__":
    app.run(host="192.168.201.200", debug=True, port=30000)

