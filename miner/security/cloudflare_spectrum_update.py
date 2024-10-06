
import requests
import ujson as json
import datetime
import os

# check for cli argument for whether to increment or decrement the port
import sys
if len(sys.argv) > 1:
    if sys.argv[1] == "increment":
        print("Incrementing port number")
        PORT_ADJUSTMENT_FACTOR = 1
    elif sys.argv[1] == "decrement":
        print("Decrementing port number")
        PORT_ADJUSTMENT_FACTOR = -1
    else:
        print("Invalid argument. Please use 'increment' or 'decrement'.")
        quit()
else:
    print("No argument provided. Please use 'increment' or 'decrement'.")
    quit()


# Locd credentials from .env file
# sudo pip install python-dotenv
from dotenv import load_dotenv
load_dotenv()
CLOUDFLARE_API_KEY = os.environ.get("CLOUDFLARE_API_KEY")
CLOUDFLARE_BEARER_TOKEN = os.environ.get("CLOUDFLARE_BEARER_TOKEN")
CLOUDFLARE_EMAIL = os.environ.get("CLOUDFLARE_EMAIL")
CLOUDFLARE_ZONE_ID = os.environ.get("CLOUDFLARE_ZONE_ID")
CLOUDFLARE_DNS_NAME_PREFIX = os.environ.get("CLOUDFLARE_DNS_NAME_PREFIX")
CLOUDFLARE_PORT_INCREMENT_AMT = os.environ.get("CLOUDFLARE_PORT_INCREMENT_AMT")


# Cloudflare API endpoint
API_ENDPOINT = f"https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ZONE_ID}/spectrum/apps"

# Headers for the request
HEADERS = {
    "Content-Type": "application/json",
    "X-Auth-Email": f"{CLOUDFLARE_EMAIL}",
    "X-Auth-Key": f"{CLOUDFLARE_API_KEY}",
}


import os
from cloudflare import Cloudflare
import datetime
import json

def save_to_json_file(data, filename):
    try:
        with open(filename, "w") as json_file:
            json.dump(data, json_file, indent=4)
            print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Failed to save data to {filename}: {e}")

def update_spectrum_instance(instance_id, update):
    try:
        update_endpoint = f"{API_ENDPOINT}/{instance_id}"
        response = requests.put(update_endpoint, headers=HEADERS, json=update)
        response.raise_for_status()
        response = response.json()
        print(f"Successfully updated instance {instance_id}! Success: {response['success']}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while updating instance {instance_id}: {e}")
        return False
        
        
def main():
    # Initialize Cloudflare client
    client = Cloudflare(
        api_email=os.environ.get("CLOUDFLARE_EMAIL"),
        api_key=os.environ.get("CLOUDFLARE_API_KEY"),
    )
    
    # Fetch spectrum instances
    try:
        spectrum_data = client.spectrum.apps.list(zone=os.environ.get("CLOUDFLARE_ZONE_ID"))
    except Exception as e:
        print(f"An error occurred while fetching spectrum instances: {e}")
        return
    #print(spectrum_data)
    #quit()
    
    if spectrum_data:
        # Extract relevant details (e.g., instances and port settings)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        before_filename = f"cfs_ports_before_{timestamp}.json"
        after_filename = f"cfs_ports_after_{timestamp}.json"
        
        spectrum_instances_before = []
        spectrum_instances_after = []
        for app in spectrum_data:
            instance = {
                "id": app.get("id"),
                "dns": app.get("dns"),
                "dns_name": app.get("dns").get("name", ""),
                "ip_firewall": app.get("ip_firewall"),
                "origin_direct": app.get("origin_direct"),
                "protocol": app.get("protocol"),
                "proxy_protocol": app.get("proxy_protocol"),
                "tls": app.get("tls"),
                "traffic_type": app.get("traffic_type"),
                "edge_ips": app.get("edge_ips"),
                "argo_smart_routing": app.get("argo_smart_routing"),
                "created_on": app.get("created_on"),
                "modified_on": app.get("modified_on")
            }
            
            # Check the dns name for the start of the domain
            if instance["dns_name"].startswith(CLOUDFLARE_DNS_NAME_PREFIX):
                
                before_instance = instance.copy()
                
                # If the protocol isn't a range, add 10 to the port and update the instance to contain a range of ports
                if "-" not in instance["protocol"]:
                    print(f"API instance found: {instance['dns_name']}")
                    
                    print(instance)
                    protocol, _, port = instance["protocol"].partition("/")
                    port = int(port)
                    updated_protocol = f"{protocol}/{(port + (int(CLOUDFLARE_PORT_INCREMENT_AMT) * int(PORT_ADJUSTMENT_FACTOR)))}"
                    instance["protocol"] = updated_protocol
                    print(f"Updated protocol: {instance['protocol']}")
                    
                    # Update the instance on Cloudflare with curl
                    update = {
                        "dns": instance["dns"],
                        "ip_firewall": instance["ip_firewall"],
                        "origin_direct": instance["origin_direct"],# ex. "origin_direct":["tcp://1.2.3.4:1101"]
                        "protocol": instance["protocol"],
                        "proxy_protocol": instance["proxy_protocol"],
                        "tls": instance["tls"],
                        "traffic_type": instance["traffic_type"],
                        "edge_ips": instance["edge_ips"],
                        "argo_smart_routing": instance["argo_smart_routing"]
                    }
                    #print(update)
                    if update_spectrum_instance(instance["id"], update):
                        spectrum_instances_before.append(before_instance)
                        spectrum_instances_after.append(instance)
            
        
        if len(spectrum_instances_after) > 0:
            print(f"Updated {len(spectrum_instances_after)} instances.")
            
            # Save the original data to a JSON file
            save_to_json_file(spectrum_instances_before, before_filename)
            
            # Save the updated details to a JSON file
            save_to_json_file(spectrum_instances_after, after_filename)
    else:
        print("Failed to fetch spectrum instances or no data returned.")

if __name__ == "__main__":
    main()