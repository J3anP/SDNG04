import yaml
import requests
import random
import string

from debugpy.adapter.servers import connections
from prettytable import PrettyTable


# -------------------------------------------------
#                   CONEXIONES:
# -------------------------------------------------

controller_ip = '192.168.201.200'

# Estructura nombre del flow:
# Normales:
# "handler-number" o "handler-arp-number"
# Reverse:
# "handler-reverse-number" o "handler-arp-reverse-number"

def get_attachement_points(dato,flag):
    if flag:
        url = f'http://{controller_ip}:8080/wm/device/?mac={dato}'
    else:
        url = f'http://{controller_ip}:8080/wm/device/?ipv4={dato}'
    print(dato)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if not data:
            print('No existe un host con la MAC ingresada!')
            return '',0,''
        else:
            data = data[0]
            switch_DPID,port,mac = data['attachmentPoint'][0]['switchDPID'],data['attachmentPoint'][0]['port'],data['mac'][0]
            return switch_DPID,port,mac
    else:
        print(f'Ocurrió un error con el request!')
        return '',0,''

def get_route(src_dpid,src_port,dst_dpid,dst_port):
    url = f'http://{controller_ip}:8080/wm/topology/route/{src_dpid}/{src_port}/{dst_dpid}/{dst_port}/json'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if not data:
            print('No existe una ruta entre estos dos puntos de conexión!')
            return []
        else:
            lista_ruta = []
            for switch in data:
                switch_DPID, port = switch['switch'], switch['port']['portNumber']
                lista_ruta.append([switch_DPID, port])
            return lista_ruta
    else:
        print(f'Ocurrió un error con el request!')
        return []

def crear_conexion(src_dpid, src_port, dst_dpid, dst_port, ip_usuario, ip_recurso, mac_usuario, mac_recurso, port_recurso, handlername):

    ruta = get_route(src_dpid, src_port, dst_dpid, dst_port)
    if not ruta:
        print("No se pudo encontrar una ruta entre los puntos.")
        return

    # Handler
    handler = handlername
    connections = {}
    connections[handler] = []
    connections[handler + "-ARP"] = []

    j = 1

    # Flujos normales
    for i in range(0, len(ruta) - 1, 2):
        switch_dpid = ruta[i][0]
        in_port = ruta[i][1]
        out_port = ruta[i + 1][1]

        # Usuario a Servidor:
        flow = crear_flow(
            switch_dpid=switch_dpid,
            in_port=in_port,
            out_port=out_port,
            ip_src=ip_usuario,
            mac_src=mac_usuario,
            ip_dst=ip_recurso,
            mac_dst=mac_recurso,
            protocol="TCP",
            port_dst=port_recurso,
            handler=handler,
            flow_number=j
        )
        connections[handler].append(flow)

        flow_arp = crear_arp_flow(
            switch_dpid=switch_dpid,
            in_port=in_port,
            out_port=out_port,
            handler=handler,
            tipo="",
            flow_number=j)

        connections[handler+"-ARP"].append(flow_arp)

        # Servidor a usuario:
        flow_reverse = crear_flow_inverso(
            switch_dpid=switch_dpid,
            in_port=out_port,
            out_port=in_port,
            ip_dst=ip_usuario,
            mac_dst=mac_usuario,
            ip_src=ip_recurso,
            mac_src=mac_recurso,
            protocol="TCP",
            port_src=port_recurso,
            handler=handler,
            flow_number=j
        )
        connections[handler].append(flow_reverse)

        flow_arp_reverse = crear_arp_flow(
            switch_dpid=switch_dpid,
            in_port=out_port,
            out_port=in_port,
            handler=handler,
            tipo="reverse-",
            flow_number=j)

        connections[handler + "-ARP"].append(flow_arp_reverse)
        j += 1


    print(f"Conexión creada con handler: {handler}")

    if len(ruta)==1:
        return len(ruta)
    else:
        return len(ruta)/2


def crear_flow(switch_dpid, in_port, out_port, ip_src, mac_src, ip_dst, mac_dst, protocol, port_dst, handler, flow_number):
    flow_name = f"{handler}-{flow_number}"
    flow = {
        "switch": switch_dpid,
        "name": flow_name,
        "priority": "3",
        "eth_type": "0x0800",
        "ipv4_src": ip_src,
        "eth_src": mac_src,
        "ipv4_dst": ip_dst,
        "eth_dst": mac_dst,
        "ip_proto": 6 if protocol == "TCP" else 17,
        "tp_dst": port_dst,
        "in_port": in_port,
        "active": "true",
        "cookie": "0",
        "actions": f"output={out_port}"
    }
    enviar_flow_al_controller(flow)
    print(flow)
    return flow

def crear_flow_inverso(switch_dpid, in_port, out_port, mac_dst, ip_dst, mac_src, ip_src, protocol, port_src, handler, flow_number):
    flow_name = f"{handler}-reverse-{flow_number}"
    flow = {
        "switch": switch_dpid,
        "name": flow_name,
        "priority": "3",
        "eth_type": "0x0800",
        "ipv4_dst": ip_dst,
        "eth_dst": mac_dst,
        "ipv4_src": ip_src,
        "eth_src": mac_src,
        "ip_proto": 6 if protocol == "TCP" else 17,
        "tp_src": port_src,
        "in_port": in_port,
        "active": "true",
        "cookie": "0",
        "actions": f"output={out_port}"
    }
    enviar_flow_al_controller(flow)
    print(flow)
    return flow


def crear_arp_flow(switch_dpid, in_port, out_port, handler, flow_number,tipo):
    flow_name = f"{handler}-arp-{tipo}{flow_number}"
    flow = {
        "switch": switch_dpid,
        "name": flow_name,
        "priority": "3",
        "eth_type": "0x0806",
        "in_port": in_port,
        "active": "true",
        "cookie": "0",
        "actions": f"output={out_port}"
    }
    enviar_flow_al_controller(flow)
    print(flow)
    return flow

def enviar_flow_al_controller(flow):
    url = f"http://{controller_ip}:8080/wm/staticflowpusher/json"
    response = requests.post(url, json=flow)
    if response.status_code == 200:
        response
        print(f"Flow {flow['name']} enviado correctamente al controlador.")
    else:
        print(f"Error al enviar el flow {flow['name']} al controlador.")
        print(response.content)


# Estructura nombre del flow:
# Normales:
# "handler-number" o "handler-arp-number"
# Reverse:
# "handler-reverse-number" o "handler-arp-reverse-number"

def eliminar_conexion(handler,numrules):

    for i in range(1, numrules + 1):
        normal = f"{handler}-{i}"
        normal_arp = f"{handler}-arp-{i}"
        reverse = f"{handler}-reverse-{i}"
        reverse_arp = f"{handler}-arp-reverse-{i}"
        eliminar_flow(normal)
        eliminar_flow(normal_arp)
        eliminar_flow(reverse)
        eliminar_flow(reverse_arp)
    print(f"Conexión con handler {handler} eliminada.")


def eliminar_flow(flowname):
    url = f"http://{controller_ip}:8080/wm/staticflowpusher/json"
    response = requests.delete(url, json={"name": flowname})
    if response.status_code == 200:
        print(f"Flow {flowname} eliminado correctamente del controlador.")
    else:
        print(f"Error al eliminar el flow {flowname} del controlador.")