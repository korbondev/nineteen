import os
from pathlib import Path
import ujson as json # pip install ujson
import pandas as pd # pip install pandas
import bittensor as bt # pip install bittensor
import dotenv # pip install python-dotenv
from substrateinterface import Keypair # pip install substrate-interface
import subprocess

# Make sure to install fiber!
# pip install git+https://github.com/korbondev/fiber.git --upgrade

NODE_CONFIG_PREFIX = os.environ.get("NODE_CONFIG_PREFIX")
REPO_DIRECTORY = os.environ.get("REPO_DIRECTORY")



def get_hotkey_file_path(wallet_name: str, hotkey_name: str) -> Path:
    file_path = Path.home() / ".bittensor" / "wallets" / wallet_name / "hotkeys" / hotkey_name
    return file_path


def load_hotkey_keypair(wallet_name: str, hotkey_name: str) -> Keypair:
    file_path = get_hotkey_file_path(wallet_name, hotkey_name)
    try:
        with open(file_path, "r") as file:
            keypair_data = json.load(file)
        keypair = Keypair.create_from_seed(keypair_data["secretSeed"])
        return keypair
    except Exception as e:
        raise ValueError(f"Failed to load keypair: {str(e)}")


def fetch_metagraph(subtensor_address, netuid):
    # Initialize subtensor connection
    try:
        print(f"Fetching metagraph for netuid {netuid} from subtensor network: {subtensor_address}")
        subtensor = bt.subtensor(network=f"ws://{subtensor_address}")
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



parsed_metagraph = None # Initialize the parsed_metagraph
for filename in os.listdir(REPO_DIRECTORY):
    if filename.startswith(f".{NODE_CONFIG_PREFIX}") and filename.endswith(".env"):

        print(f"Processing config file: {filename}")
        # load the config variables from the env 
        dotenv.load_dotenv(f"{filename}")
        # load the bittensor hotkey from the HOTKEY_NAME=coldkey-01-hotkey-01 and WALLET_NAME=coldkey-01
        keypair = load_hotkey_keypair(wallet_name=os.getenv("WALLET_NAME"), hotkey_name=os.getenv("HOTKEY_NAME"))
        hotkey = keypair.ss58_address        
        print(f"Loaded hotkey: {hotkey}")
        
        
        # get the row from the parsed_metagraph dataframe that matches the hotkey
        if not parsed_metagraph:
            parsed_metagraph = fetch_metagraph(os.getenv('SUBTENSOR_ADDRESS'), os.getenv('NETUID'))
        hotkey_row = parsed_metagraph.loc[parsed_metagraph['HOTKEY'] == hotkey]
        print(hotkey_row)     
        
        # get the AXON_IP value from the hotkey_row
        axon_ip_port = hotkey_row['AXON_IP'].values[0]
        
           
                
        # Ensure the hotkey_row is not empty
        if axon_ip_port:
            # Compare the AXON_IP value from the row with the external IP:PORT
            if axon_ip_port != f"{os.getenv('NODE_EXTERNAL_IP')}:{os.getenv('NODE_EXTERNAL_PORT')}":
                print(f"Hotkey: {hotkey} updating metagraph from {axon_ip_port} to {os.getenv('NODE_EXTERNAL_IP')}:{os.getenv('NODE_EXTERNAL_PORT')}")
                quit()
                # Construct the command
                fiber_post_ip_path = os.path.join(REPO_DIRECTORY, '.venv', 'bin', 'fiber-post-ip')

                command = [
                    fiber_post_ip_path,
                    '--netuid', os.getenv('NETUID'),
                    '--subtensor.network', os.getenv('SUBTENSOR_NETWORK'),
                    '--subtensor.chain_endpoint', os.getenv('SUBTENSOR_ADDRESS'),
                    '--external_port', os.getenv('NODE_EXTERNAL_PORT'),
                    '--wallet.name', os.getenv('WALLET_NAME'),
                    '--wallet.hotkey', os.getenv('HOTKEY_NAME'),
                    '--external_ip', os.getenv('NODE_EXTERNAL_IP')
                ]

                # Run the command
                try:
                    print(f"Running command: {' '.join(command)}")
                    result = subprocess.run(command, cwd=REPO_DIRECTORY, capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"Successfully updated IP and port on chain for {hotkey}")
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
