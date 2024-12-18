from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Ruta para la pagina de login
@app.route('/')
def index():
    return render_template('login.html')  # Pagina de prueba de login

# Ruta para manejar autenticacion (simulada)
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    # Logica de autenticación simulada
    if username == "admin" and password == "password":  # Prueba local
        return jsonify({"message": "Login exitoso"})
    else:
        return jsonify({"message": "Credenciales incorrectas"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=30000)
