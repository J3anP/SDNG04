import pyrad.packet
from datetime import datetime, timedelta
import jwt
import mysql.connector
from datetime import datetime
import pytz
import requests
import random
import string
from flask import session, url_for
import json
import files.flowUtils as fu
import hashlib
from flask import Flask, jsonify,render_template, request, redirect
from pyrad.client import Client
from pyrad.dictionary import Dictionary
from pyrad.packet import AccessRequest, Packet

# ----------------------------
# -- Configuración de Flask --
# ----------------------------

app = Flask(__name__)
app.secret_key = "grupo4"

# -------------------------------
# -- Configuración de MySQL BD --
# -------------------------------

db_config = {
    "host": "192.168.201.200",
    "user": "gabriel",
    "password": "gabriel",
    "database": "mydb"
}

# --------------------------------------
# -- Configuración del cliente RADIUS --
# --------------------------------------

RADIUS_SERVER = "127.0.0.1"
RADIUS_PORT = 1812
SECRET = b"testing123"
DICT_PATH = "/etc/freeradius/3.0/dictionaryAuxiliar"

client = Client(server=RADIUS_SERVER, secret=SECRET, dict=Dictionary(DICT_PATH))
client.AuthPort = RADIUS_PORT

# ------------
# -- Clases --
# ------------

# Usuario:
class Usuario:
    def __init__(self, username, session, time_stamp, rol, rolname, names, lastnames, code):
        self.username = username
        self.session = session
        self.time_stamp = time_stamp
        self.rol = rol
        self.rolname = rolname
        self.names = names
        self.lastnames = lastnames
        self.code = code

    @classmethod
    def from_db(cls, username, db_connection,aux):
        if(aux):
            query = """
                        SELECT u.username, u.session, u.time_stamp, u.rol, r.rolname, u.names, u.lastnames, u.code
                        FROM user u
                        JOIN role r ON u.rol = r.idrole
                        WHERE u.username = %s
                    """
        else:
            query = """
                        SELECT u.username, u.session, u.time_stamp, u.rol, r.rolname, u.names, u.lastnames, u.code
                        FROM user u
                        JOIN role r ON u.rol = r.idrole
                        WHERE u.ip = %s
                    """

        cursor = db_connection.cursor(dictionary=True)
        cursor.execute(query, (username,))
        user_data = cursor.fetchone()
        if user_data:
            return cls(**user_data)
        return None

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, user_dict):
        return cls(**user_dict)

    def __str__(self):
        return f"{self.names} {self.lastnames} ({self.rolname})"


# --------------------------
# -- Funciones necesarias --
# --------------------------

# Radius:
def authenticate_user(username, password):
    req = client.CreateAuthPacket(code=pyrad.packet.AccessRequest)
    req["User-Name"] = username

    # Comprobación de si la contraseña está cifrada en MD5
    if not is_md5(password):
        password = text_to_md5(password)

    req["User-Password"] = password
    reply = client.SendPacket(req)
    if reply.code == pyrad.packet.AccessAccept:
        return True
    else:
        return False


# MySQL:
def get_user_from_db(username, db_config,aux):
    try:
        db_connection = mysql.connector.connect(**db_config)
        usuario = Usuario.from_db(username, db_connection,aux)
        db_connection.close()
        return usuario
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None

def update_user(username, nuevos_valores):
    conexion = None
    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor()

        set_clause = ", ".join([f"{campo} = %s" for campo in nuevos_valores.keys()])
        valores = list(nuevos_valores.values()) + [username]
        consulta = f"UPDATE user SET {set_clause} WHERE username = %s"

        cursor.execute(consulta, valores)
        conexion.commit()

        return cursor.rowcount > 0

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False
    finally:
        if conexion and conexion.is_connected():
            cursor.close()
            conexion.close()



def get_rules_by_role(idrole):

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = """
            SELECT r.idrule, r.name, r.description, r.svr_ip, r.svr_port, r.svr_mac, r.action
            FROM rule r
            JOIN role_has_rule rr ON r.idrule = rr.rule_idrule
            WHERE rr.role_idrole = %s
        """

        cursor.execute(query, (idrole,))
        reglas = cursor.fetchall()

        for regla in reglas:
            print(f"ID: {regla[0]}, Name: {regla[1]}, Description: {regla[2]}, "
                  f"IP: {regla[3]}, Port: {regla[4]}, MAC: {regla[5]}, Action: {regla[6]}")

        return reglas

    except mysql.connector.Error as err:
        print(f"Error al conectarse a la base de datos: {err}")
        return None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_num_rules_by_username(username):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = """
            SELECT u.numrules
            FROM user u
            WHERE u.username = %s
        """

        cursor.execute(query, (username,))
        numrules = cursor.fetchall()
        return numrules[0]
    except mysql.connector.Error as err:
        print(f"Error al conectarse a la base de datos: {err}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/usuarios', methods=['GET'])
def obtener_usuarios():
    try:
        # Conexión a la base de datos
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor(dictionary=True)
        
        # Consulta SQL
        query = "SELECT u.username, u.names, u.lastnames, u.code,u.time_stamp ,r.rolname as rol FROM user join role r on u.rol = r.idrole"
        cursor.execute(query)
        resultados = cursor.fetchall()
        
        return jsonify(resultados)
    except mysql.connector.Error as error:
        return jsonify({"error": str(error)})
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()

# Floodlight:
def create_authorization_flows(usuario):

    # Atributos:
    ip_usuario = get_ip()
    ip_usuario = "10.0.0.1"

    sw_id_usuario,sw_port_usuario,mac_usuario = fu.get_attachement_points(ip_usuario,False)

    # Creación de conexión por rol (probando con un recurso por rol):
    regla_usuario = get_rules_by_role(usuario.rol)[0]

    # Recurso:
    ip_recurso = regla_usuario[3]
    port_recurso = regla_usuario[4]
    sw_id_recurso, sw_port_recurso, mac_recurso = fu.get_attachement_points(ip_recurso, False)

    # Flows:
    numrules = fu.crear_conexion(sw_id_usuario,sw_port_usuario,sw_id_recurso, sw_port_recurso, ip_usuario, mac_usuario, ip_recurso, mac_recurso,port_recurso,usuario.username)

    # Update del usuario:
    update_user(usuario.username, {"ip": ip_usuario, "sw_id": sw_id_usuario, "sw_port": sw_port_usuario, "mac": mac_usuario, "numrules": numrules})

    return regla_usuario

# Session:
def create_session(username):
    update_user(username,{"session": generate_session_id(), "time_stamp": get_date()})

# Otros:
def text_to_md5(texto):
    md5 = hashlib.md5()
    md5.update(texto.encode('utf-8'))
    return md5.hexdigest()

def is_md5(text):
    # Una cadena MD5 tiene 32 caracteres hexadecimales
    return len(text) == 32 and all(c in '0123456789abcdef' for c in text)


def generate_session_id():
    caracteres = string.ascii_uppercase + string.digits
    codigo = ''.join(random.choices(caracteres, k=6))
    return codigo

def get_date():
    zona_horaria = pytz.timezone("America/Lima")  # Perú está en GMT-5
    hora_actual = datetime.now(zona_horaria)
    return hora_actual.strftime("%H:%M:%S del %d-%m-%Y ")

def get_ip():
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.remote_addr
    return ip

def generate_token(usuario):
    payload = {
        'usuario': usuario,
        'exp': datetime.utcnow() + timedelta(minutes=1)
    }
    token = jwt.encode(payload, 'grupo4', algorithm='HS256')
    return token

def decode_token(token):
    try:
        payload = jwt.decode(token, 'grupo4', algorithms=['HS256'])
        return payload['usuario']
    except jwt.ExpiredSignatureError:
        print("error expiredsignatuere")
        return None
    except jwt.InvalidTokenError:
        print("error InvalidTokenError")
        return None

# -----------------------
# -- Configuración WEB --
# -----------------------

# Inicio de sesión:
@app.route("/", methods=["GET", "POST"])
def login():

    ip_usuario = get_ip()
    ip_usuario = "10.0.0.1"

    if "usuario" in session:
        usuario = get_user_from_db(ip_usuario, db_config, False)
        if usuario:
            regla_usuario = get_rules_by_role(usuario.rol)[0]
            token = generate_token(usuario.to_dict())
            return redirect(f"http://{regla_usuario[3]}:{regla_usuario[4]}/?token={token}")
    else:
        usuario = get_user_from_db(ip_usuario, db_config, False)
        if usuario:
            session["usuario"] = usuario.to_dict()
            regla_usuario = get_rules_by_role(usuario.rol)[0]
            token = generate_token(usuario.to_dict())
            return redirect(f"http://{regla_usuario[3]}:{regla_usuario[4]}/?token={token}")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if authenticate_user(username, password):

            # Creación de la sesión
            create_session(username)

            # Obtención del usuario
            usuario = get_user_from_db(username, db_config, True)
            session["usuario"] = usuario.to_dict()

            # Creación de flows de autorización
            regla_usuario = create_authorization_flows(usuario)

            # Redirección
            token = generate_token(usuario.to_dict())
            return redirect(f"http://{regla_usuario[3]}:{regla_usuario[4]}/?token={token}")
        else:
            return "Credenciales inválidas", 401
    return render_template("login.html")

# Cerrar sesión:
@app.route("/logout", methods=["GET"])
def logout():

    username = request.args.get('username')

    if username:
        numrules = get_num_rules_by_username(username)[0]
        if numrules:
            fu.eliminar_conexion(username, numrules)
            update_user(username, {"numrules": None})

    session.clear()
    return redirect(url_for('login'))

# Main:
if __name__ == "__main__":
    app.run(host="192.168.201.200", port=30000, debug=True)

