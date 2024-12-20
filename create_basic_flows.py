import requests
import json

# Configuración del controlador Floodlight
CONTROLLER_IP = "10.20.12.65"  # Cambiar por la IP del controlador si no es local
CONTROLLER_PORT = 8080       # Puerto por defecto de la REST API del Floodlight

# Configuración de la regla
RULE = {
    "switch": "",
    "name": "flow-basic",
    "priority": "2",
    "ipv4_dst": "10.0.0.0/24",
    "eth_type": "0x0800",
    "active": "true",
    "actions": ""
}

# URL de la REST API para la instalación de flujos
ADD_FLOW_URL = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/staticflowpusher/json"

def get_switches():
    """
    Obtiene la lista de switches conectados al controlador Floodlight.
    """
    url = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/core/controller/switches/json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener la lista de switches: {e}")
        return []

def add_flow_to_switch(switch_id,j):
    """
    Agrega la regla de flujo al switch especificado.
    """
    flow = RULE.copy()
    flow["switch"] = switch_id
    flow["name"] = f"flow-basic-{j}"
    try:
        response = requests.post(ADD_FLOW_URL, data=json.dumps(flow))
        response.raise_for_status()
        print(f"Regla agregada al switch {switch_id}: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error al agregar la regla al switch {switch_id}: {e}")

def main():
    # Obtener todos los switches conectados
    switches = get_switches()
    print(switches)
    if not switches:
        print("No se encontraron switches conectados.")
        return

    # Instalar la regla en cada switch
    j = 1
    for switch in switches:
        switch_id = switch.get("switchDPID")
        if switch_id:
            add_flow_to_switch(switch_id,j)
            j += 1

if __name__ == "__main__":
    main()
