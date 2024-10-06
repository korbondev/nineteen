import requests
import ujson as json
import datetime
import os
import sys
import subprocess
from dotenv import load_dotenv, dotenv_values

# Check for CLI argument for whether to increment or decrement the port
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

# Load credentials from .env file
load_dotenv()
CLOUDFLARE_API_KEY = os.environ.get("CLOUDFLARE_API_KEY")
CLOUDFLARE_BEARER_TOKEN = os.environ.get("CLOUDFLARE_BEARER_TOKEN")
CLOUDFLARE_EMAIL = os.environ.get("CLOUDFLARE_EMAIL")
CLOUDFLARE_ZONE_ID = os.environ.get("CLOUDFLARE_ZONE_ID")
CLOUDFLARE_DNS_NAME_PREFIX = os.environ.get("CLOUDFLARE_DNS_NAME_PREFIX")
CLOUDFLARE_PORT_INCREMENT_AMT = os.environ.get("CLOUDFLARE_PORT_INCREMENT_AMT")
PREFIX_ONLY_ON_DNS = os.environ.get("PREFIX_ONLY_ON_DNS")
REPO_DIRECTORY = os.environ.get("REPO_DIRECTORY")
UPDATE_NODE_PORT_IN_NODE_FILE = os.environ.get("UPDATE_NODE_PORT_IN_NODE_FILE")

# Cloudflare API endpoint
API_ENDPOINT = f"https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ZONE_ID}/spectrum/apps"

# Headers for the request
HEADERS = {
    "Content-Type": "application/json",
    "X-Auth-Email": f"{CLOUDFLARE_EMAIL}",
    "X-Auth-Key": f"{CLOUDFLARE_API_KEY}",
}

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
    # Fetch spectrum instances
    try:
        response = requests.get(API_ENDPOINT, headers=HEADERS)
        response.raise_for_status()
        spectrum_data = response.json().get('result', [])
    except Exception as e:
        print(f"An error occurred while fetching spectrum instances: {e}")
        return

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
                "dns_name": app.get("dns", {}).get("name", ""),
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

                if "-" in instance["protocol"]:
                    print(f"Skipping instance {instance['dns_name']}, ports cannot be a range!")
                    continue
                
                before_instance = instance.copy()

                # If the protocol isn't a range, add to the port and update the instance
                
                print(f"API instance found: {instance['dns_name']}")

                protocol, _, port = instance["protocol"].partition("/")
                port = int(port)
                new_port = port + (int(CLOUDFLARE_PORT_INCREMENT_AMT) * int(PORT_ADJUSTMENT_FACTOR))
                updated_protocol = f"{protocol}/{new_port}"
                instance["protocol"] = updated_protocol
                print(f"Updated protocol: {instance['protocol']}")

                # Update the instance on Cloudflare
                update = {
                    "dns": instance["dns"],
                    "ip_firewall": instance["ip_firewall"],
                    "origin_direct": instance["origin_direct"],
                    "protocol": instance["protocol"],
                    "proxy_protocol": instance["proxy_protocol"],
                    "tls": instance["tls"],
                    "traffic_type": instance["traffic_type"],
                    "edge_ips": instance["edge_ips"],
                    "argo_smart_routing": instance["argo_smart_routing"]
                }

                if update_spectrum_instance(instance["id"], update):
                    spectrum_instances_before.append(before_instance)
                    spectrum_instances_after.append(instance)

                    # Extract the subdomain
                    dns_name = instance["dns_name"]
                    subdomain = dns_name.split('.')[0]

                    # Trim PREFIX_ONLY_ON_DNS from subdomain
                    if subdomain.startswith(PREFIX_ONLY_ON_DNS):
                        DNS_SUBDOMAIN_PREFIX = subdomain[len(PREFIX_ONLY_ON_DNS):]
                    else:
                        DNS_SUBDOMAIN_PREFIX = subdomain

                    # Form the filename
                    filename = f".{DNS_SUBDOMAIN_PREFIX}.env"

                    # Check if the file exists
                    node_env_path = os.path.join(REPO_DIRECTORY, filename)
                    if os.path.exists(node_env_path):
                        # Load the .env file
                        env_vars = dotenv_values(node_env_path)
                        HOTKEY_NAME = env_vars.get('HOTKEY_NAME')
                        WALLET_NAME = env_vars.get('WALLET_NAME')
                        SUBTENSOR_NETWORK = env_vars.get('SUBTENSOR_NETWORK')
                        SUBTENSOR_ADDRESS = env_vars.get('SUBTENSOR_ADDRESS')
                        IS_VALIDATOR = env_vars.get('IS_VALIDATOR')
                        NODE_PORT = env_vars.get('NODE_PORT')
                        NODE_EXTERNAL_IP = env_vars.get('NODE_EXTERNAL_IP')
                        NETUID = env_vars.get('NETUID')

                        # Update NODE_PORT in the env_vars dictionary
                        env_vars['NODE_PORT'] = str(new_port)

                        if UPDATE_NODE_PORT_IN_NODE_FILE == "true":
                            # Write back to the .env file
                            try:
                                with open(node_env_path, 'w') as f:
                                    for key, value in env_vars.items():
                                        f.write(f"{key}={value}\n")
                                print(f"Updated {node_env_path} with new port number {new_port}")
                            except Exception as e:
                                print(f"Failed to update {node_env_path}: {e}")
                                continue

                        # Construct the command
                        fiber_post_ip_path = os.path.join(REPO_DIRECTORY, '.venv', 'bin', 'fiber-post-ip')

                        command = [
                            fiber_post_ip_path,
                            '--netuid', NETUID,
                            '--subtensor.network', SUBTENSOR_NETWORK,
                            '--subtensor.chain_endpoint', SUBTENSOR_ADDRESS,
                            '--external_port', str(new_port),
                            '--wallet.name', WALLET_NAME,
                            '--wallet.hotkey', HOTKEY_NAME,
                            '--external_ip', NODE_EXTERNAL_IP
                        ]

                        # Run the command
                        try:
                            print(f"Running command: {' '.join(command)}")
                            result = subprocess.run(command, cwd=REPO_DIRECTORY, capture_output=True, text=True)
                            if result.returncode == 0:
                                print(f"Successfully updated IP and port on chain for {DNS_SUBDOMAIN_PREFIX}")
                            else:
                                print(f"Error updating IP and port on chain for {DNS_SUBDOMAIN_PREFIX}")
                                print(f"Stdout: {result.stdout}")
                                print(f"Stderr: {result.stderr}")
                        except Exception as e:
                            print(f"Exception occurred while updating IP and port on chain for {DNS_SUBDOMAIN_PREFIX}: {e}")
                    else:
                        print(f"No .env file found for subdomain {DNS_SUBDOMAIN_PREFIX}, expected at {filename}")
                else:
                    print(f"Failed to update instance {instance['id']}")

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
