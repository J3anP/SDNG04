import pyrad.packet
import hashlib
from flask import Flask, render_template, request
from pyrad.client import Client
from pyrad.dictionary import Dictionary
from pyrad.packet import AccessRequest, Packet
app = Flask(__name__)

# --------------------------------------
# -- Configuración del cliente RADIUS --
# --------------------------------------

RADIUS_SERVER = "127.0.0.1"
RADIUS_PORT = 1812
SECRET = b"testing123"
DICT_PATH = "/etc/freeradius/3.0/dictionaryAuxiliar"

client = Client(server=RADIUS_SERVER, secret=SECRET, dict=Dictionary(DICT_PATH))
client.AuthPort = RADIUS_PORT

# --------------------------
# -- Funciones necesarias --
# --------------------------

# Radius:
def authenticate_user(username, password):
    req = client.CreateAuthPacket(code=pyrad.packet.AccessRequest)
    req["User-Name"] = username

    # Comprobación de si la contraseña está cifrada en MD5
    if not is_md5(password):
        password = texto_a_md5(password)

    req["User-Password"] = password
    reply = client.SendPacket(req)
    if reply.code == pyrad.packet.AccessAccept:
        return True
    else:
        return False




# MySQL:



# Otros:
def texto_a_md5(texto):
    md5 = hashlib.md5()
    md5.update(texto.encode('utf-8'))
    return md5.hexdigest()

def is_md5(text):
    # Una cadena MD5 tiene 32 caracteres hexadecimales
    return len(text) == 32 and all(c in '0123456789abcdef' for c in text)

# -----------------------
# -- Configuración WEB --
# -----------------------

# Inicio de sesión:
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if authenticate_user(username, password):
            return "Login exitoso"
        else:
            return "Credenciales inválidas", 401
    return render_template("login.html")

# Redirección a recursos:
if __name__ == "__main__":
    app.run(host="192.168.201.200", port=30000, debug=True)

