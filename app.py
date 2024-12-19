import pyrad.packet
from flask import Flask, render_template, request
from pyrad.client import Client
from pyrad.dictionary import Dictionary
from pyrad.packet import AccessRequest, Packet

app = Flask(__name__)

# Configuración del cliente RADIUS
RADIUS_SERVER = "127.0.0.1"
RADIUS_PORT = 1812
SECRET = b"testing123"
DICT_PATH = "/etc/freeradius/3.0/dictionaryAuxiliar"

client = Client(server=RADIUS_SERVER, secret=SECRET, dict=Dictionary(DICT_PATH))
client.AuthPort = RADIUS_PORT


def authenticate_user(username, password):
    req = client.CreateAuthPacket(code=pyrad.packet.AccessRequest)
    req["User-Name"] = username
    req["User-Password"] = password

    reply = client.SendPacket(req)

    if reply.code == pyrad.packet.AccessAccept:
        return True
    else:
        return False


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


if __name__ == "__main__":
    app.run(host="192.168.201.200", port=30000, debug=True)

