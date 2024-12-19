import requests

floodlight_ip = "10.20.12.65"
base_url = f"http://{floodlight_ip}:8080/wm/staticflowpusher"

def get_all_flows():
    try:
        response = requests.get(f"{base_url}/list/all/json")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch flows. Status code: {response.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Floodlight: {e}")
        return {}

def delete_flow(flow_name):
    try:
        data = {"name": flow_name}
        response = requests.delete(f"{base_url}/json", json=data)
        if response.status_code == 200:
            print(f"Successfully deleted flow: {flow_name}")
        else:
            print(f"Failed to delete flow: {flow_name}. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error deleting flow {flow_name}: {e}")

def delete_all_flows():
    all_flows = get_all_flows()

    for switch, flow_list in all_flows.items():
        for flow_entry in flow_list:
            for flow_name in flow_entry.keys():
                delete_flow(flow_name)

if __name__ == "__main__":
    delete_all_flows()
