import os
from pathlib import Path
import ujson as json # pip install ujson
import pandas as pd # pip install pandas
import bittensor as bt # pip install bittensor
from substrateinterface import Keypair # pip install substrate-interface
import subprocess
from dotenv import load_dotenv, dotenv_values

# Make sure to install fiber!
# pip install git+https://github.com/korbondev/fiber.git --upgrade

load_dotenv()
NODE_CONFIG_PREFIX = os.environ.get("NODE_CONFIG_PREFIX")
REPO_DIRECTORY = os.environ.get("REPO_DIRECTORY")



def get_hotkey_file_path(wallet_name: str, hotkey_name: str) -> Path:
    file_path = Path.home() / ".bittensor" / "wallets" / wallet_name / "hotkeys" / hotkey_name
    return file_path


def load_hotkey_keypair(wallet_name, hotkey_name):
    file_path = get_hotkey_file_path(wallet_name, hotkey_name)
    try:
        with open(file_path, "r") as file:
            keypair_data = json.load(file)
        return Keypair.create_from_seed(keypair_data["secretSeed"])
    except Exception as e:
        raise ValueError(f"Failed to load keypair: {str(e)}") from e


def fetch_metagraph(subtensor_address, netuid):
    # Initialize subtensor connection
    try:
        print(f"Fetching metagraph for netuid {netuid} from subtensor network: {subtensor_address}")
        subtensor = bt.subtensor(network=f"{subtensor_address}")
    except Exception as e:
        print(f"Error connecting to subtensor network: {e}")


    netuid_int = int(netuid)
    try:
        metagraph = subtensor.metagraph(netuid=netuid_int)
    except Exception as e:
        print(f"Error fetching metagraph for netuid {netuid}: {e}")


    # Extract the first AxonInfo IP:PORT from each entry
    axon_ip_ports = []
    for axon_info in metagraph.axons:
        axon_ip, axon_port = None, None
        if hasattr(axon_info, 'ip') and hasattr(axon_info, 'port'):
            axon_ip = axon_info.ip
            axon_port = axon_info.port
        axon_ip_ports.append(f"{axon_ip}:{axon_port}")

    # Create the DataFrame with extracted Axon IP:PORT
    data = {
        'SUBNET': netuid_int,
        'UID': metagraph.uids,
        'STAKE()': metagraph.stake,
        'RANK': metagraph.ranks,
        'TRUST': metagraph.trust,
        'CONSENSUS': metagraph.consensus,
        'INCENTIVE': metagraph.incentive,
        'DIVIDENDS': metagraph.dividends,
        'EMISSION(ρ)': metagraph.emission,
        'VTRUST': metagraph.validator_trust,
        'VAL': metagraph.validator_permit,
        'UPDATED': metagraph.last_update,
        'ACTIVE': metagraph.active,
        'AXON_IP': axon_ip_ports,
        'HOTKEY': metagraph.hotkeys,
        'COLDKEY': metagraph.coldkeys
    }

    parsed_metagraph = pd.DataFrame(data)
    print(parsed_metagraph)

    return parsed_metagraph


count_hotkeys = 0
count_registered = 0
count_updated = 0
parsed_metagraph = None # Initialize the parsed_metagraph
for filename in os.listdir(REPO_DIRECTORY):
    if filename.startswith(f".{NODE_CONFIG_PREFIX}") and filename.endswith(".env"):

        print(f"Processing config file: {filename}")
        # load the config variables from the env 
        
        node_env_path = os.path.join(REPO_DIRECTORY, filename)
        env_vars = dotenv_values(node_env_path)
        HOTKEY_NAME = env_vars.get('HOTKEY_NAME')
        WALLET_NAME = env_vars.get('WALLET_NAME')
        SUBTENSOR_NETWORK = env_vars.get('SUBTENSOR_NETWORK')
        SUBTENSOR_ADDRESS = env_vars.get('SUBTENSOR_ADDRESS')
        IS_VALIDATOR = env_vars.get('IS_VALIDATOR')
        NODE_PORT = env_vars.get('NODE_PORT')
        NODE_EXTERNAL_PORT = env_vars.get('NODE_EXTERNAL_PORT')
        NODE_EXTERNAL_IP = env_vars.get('NODE_EXTERNAL_IP')
        NETUID = env_vars.get('NETUID')    
        
        
        # load the bittensor hotkey from the HOTKEY_NAME=coldkey-01-hotkey-01 and WALLET_NAME=coldkey-01
        keypair = load_hotkey_keypair(wallet_name=WALLET_NAME, hotkey_name=HOTKEY_NAME)
        hotkey = keypair.ss58_address
        print(f"Loaded hotkey: {hotkey}")
        count_hotkeys += 1


        # get the row from the parsed_metagraph dataframe that matches the hotkey
        if parsed_metagraph is None:
            parsed_metagraph = fetch_metagraph(SUBTENSOR_ADDRESS, NETUID)
        hotkey_row = parsed_metagraph.loc[parsed_metagraph['HOTKEY'] == hotkey]
        print(hotkey_row) 
        
        # if the dataframe is empty then make a note about the hotkey being deregistered and continue
        if hotkey_row.empty:
            print(f"Hotkey: {hotkey} is deregistered")
            continue
        count_registered += 1

        if axon_ip_port := hotkey_row['AXON_IP'].values[0]:
            # Compare the AXON_IP value from the row with the external IP:PORT
            if axon_ip_port != f"{NODE_EXTERNAL_IP}:{NODE_EXTERNAL_PORT}":
                print(f"Hotkey: {hotkey} updating metagraph from {axon_ip_port} to {NODE_EXTERNAL_IP}:{NODE_EXTERNAL_PORT}")
                #quit()
                # Construct the command
                fiber_post_ip_path = os.path.join(REPO_DIRECTORY, '.venv', 'bin', 'fiber-post-ip')

                command = [
                    fiber_post_ip_path,
                    '--netuid', NETUID,
                    '--subtensor.network', SUBTENSOR_NETWORK,
                    '--subtensor.chain_endpoint', SUBTENSOR_ADDRESS,
                    '--external_port', NODE_EXTERNAL_PORT,
                    '--wallet.name', WALLET_NAME,
                    '--wallet.hotkey', HOTKEY_NAME,
                    '--external_ip', NODE_EXTERNAL_IP
                ]

                # Run the command
                try:
                    print(f"Running command: {' '.join(command)}")
                    result = subprocess.run(command, cwd=REPO_DIRECTORY, capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"Successfully updated IP and port on chain for {hotkey}")
                        count_updated += 1
                    else:
                        print(f"Error updating IP and port on chain for {hotkey}")
                        print(f"Stdout: {result.stdout}")
                        print(f"Stderr: {result.stderr}")
                except Exception as e:
                    print(f"Exception occurred while updating IP and port on chain for {hotkey}: {e}")
            else:
                print(f"Hotkey: {hotkey} metagraph {axon_ip_port} matches!")
        else:
            print(f"No matching row found for hotkey: {hotkey}")
        # if NODE_EXTERNAL_IP or NODE_EXTERNAL_PORT does not match 


# Print the summary
print(f"Total hotkeys: {count_hotkeys}")
print(f"Total registered hotkeys: {count_registered}")
print(f"Total updated hotkeys: {count_updated}")
