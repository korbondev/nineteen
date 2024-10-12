import os
import argparse
current_pid = os.getpid()
import requests
import subprocess

import datetime
import time
subprocess.run(["python3", "-m", "pip", "install", "pytz"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
import pytz
subprocess.run(["python3", "-m", "pip", "install", "tzlocal"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
from tzlocal import get_localzone

import re
import sys

# for discord bot
subprocess.run(["python3", "-m", "pip", "install", "python-dotenv"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
from dotenv import load_dotenv
import socket
import hashlib
import ujson as json


# Constants
WEIGHTS_ENDPOINT_URL = os.getenv('WEIGHTS_ENDPOINT_URL')# "https://taovision.ai/v1/weights"
CACHE_FILE = os.getenv('CACHE_FILE')# "weights_cache.json"
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
DISCORD_MENTION_CODE = os.getenv('DISCORD_MENTION_CODE') # '<@&1203050411611652156>' # You can get this by putting a \ in front of a mention and sending a message in discord GUI client
UPDATE_INTERVAL = os.getenv('UPDATE_INTERVAL') # 3600  # Time in seconds check for updates (3600 sec = 1 hr)
WATCHDOG_INTERVAL = os.getenv('WATCHDOG_INTERVAL') # 300  # Time in seconds check for updates (3600 sec = 1 hr)
AUTO_UPDATES_ENABLED = os.getenv('AUTO_UPDATES_ENABLED') # true


# Updates
auto_update_enabled = AUTO_UPDATES_ENABLED == 'true'
update_interval = UPDATE_INTERVAL  # Time in seconds check for updates (3600 sec = 1 hr)

# Uptime
watchdog_interval = WATCHDOG_INTERVAL # Time in seconds to check for liveness

# Comms
discord_mention_code = DISCORD_MENTION_CODE 


# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the path to the .env file
env_file = os.path.join(script_dir, '.env')


def initialize_env_file(env_file_path):
    if os.path.exists(env_file_path):
        load_dotenv(env_file_path)
        webhook_url = DISCORD_WEBHOOK_URL
        if webhook_url and webhook_url != 'your_webhook_url_here':
            print(f"Existing webhook URL found in {env_file_path}")
            return

    print("Discord webhook URL is required to run this script.")
    webhook_url = input("Please enter your Discord webhook URL: ").strip()

    while not webhook_url.startswith("https://discord.com/api/webhooks/"):
        print("Invalid webhook URL. It should start with 'https://discord.com/api/webhooks/'")
        webhook_url = input("Please enter a valid Discord webhook URL: ").strip()

    with open(env_file_path, 'w') as f:
        f.write(f'DISCORD_WEBHOOK_URL={webhook_url}\n')
    
    print(f"Webhook URL has been saved to {env_file_path}")


def validate_webhook(webhook_url):
    try:
        response = requests.post(webhook_url, json={"content": "Weights Monitor: Webhook test"})
        if response.status_code == 204:
            print("Webhook test successful!")
            return True
        else:
            print(f"Webhook test failed. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error testing webhook: {str(e)}")
        return False


def report_for_duty(message_topic, message_contents, webhook_url):
    # Message content
    host_name = socket.gethostname() 
    os.chdir(os.path.dirname(__file__))
    commit_before_pull = get_latest_commit_hash()
    
    message = f"# :saluting_face: _reporting for duty!_\n" + \
              f"**Host Name:** {host_name}\n" + \
              f"**Commit Hash:** {commit_before_pull}\n" + \
              f"**{message_topic} Details:**\n\n{message_contents}"

    if len(message) > 2000:
        # Post lengthy message to dpaste and get the link
        dpaste_link = post_to_dpaste(message)
        short_message = f"# :saluting_face: _reporting for duty!_\n" + \
                        f"**Host Name:** {host_name}\n" + \
                        f"**Commit Hash:** {commit_before_pull}\n" + \
                        f"**{message_topic} Details:** [View full report]({dpaste_link})"
        data = {
            "content": short_message,
            "username": host_name
        }
    else:
        data = {
            "content": message,
            "username": host_name
        }

    response = requests.post(webhook_url, json=data)
    if response.status_code == 204:
        print(f"[{datetime.datetime.now()}] Message sent successfully")
    else:
        print(f"[{datetime.datetime.now()}] Failed to send message, status code: {response.status_code}")


def post_to_dpaste(content, lexer='python', expires='2592000', format='url'):

    # dpaste API endpoint
    api_url = 'https://dpaste.org/api/'

    # Data to be sent to dpaste
    data = {
        'content': content,
        'lexer': lexer,
        'expires': expires,
        'format': format,
    }

    # Make the POST request
    response = requests.post(api_url, data=data)

    # Check if the request was successful
    if response.status_code == 200:
        # Return the URL of the snippet
        return response.text.strip()  # Strip to remove any extra whitespace/newline
    else:
        # Return an error message or raise an exception
        return "Failed to create dpaste snippet. Status code: {}".format(response.status_code)


def get_latest_commit_hash():
    """Function to get the latest commit hash."""
    result = subprocess.run(["git", "log", "-1", "--format=%H"], capture_output=True, text=True)
    return result.stdout.strip()


def check_for_updates():
    os.chdir(os.path.dirname(__file__))
    commit_before_pull = get_latest_commit_hash()
    subprocess.run(["git", "pull"], check=True)
    commit_after_pull = get_latest_commit_hash()

    if commit_before_pull != commit_after_pull:
        print("Updates pulled, exiting...")
        exit(0)
    else:
        print("No updates found, continuing...")
        return time.time()


def fetch_weights():
    response = requests.get(WEIGHTS_ENDPOINT_URL)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch weights from {WEIGHTS_ENDPOINT_URL}")


def calculate_hash(data):
    return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {'weights': {}, 'hash': ''}


def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)


def check_weights(webhook_url):
    print(f"[{datetime.datetime.now()}] Starting weights check...")
    cache = load_cache()
    
    current_weights = fetch_weights()
    current_hash = calculate_hash(current_weights)
    
    if current_hash != cache['hash']:
        changes = []
        old_weights = cache['weights']
        
        for key, value in current_weights.items():
            if key not in old_weights or old_weights[key] != value:
                changes.append(f"{key}: {old_weights.get(key, 'N/A')} → {value}")
        
        cache['weights'] = current_weights
        cache['hash'] = current_hash
        save_cache(cache)
        
        message = f"{discord_mention_code} :stethoscope: Weights changes detected:\n\n"
        message += "\n".join(changes)
        report_for_duty("Weights Changes", message, webhook_url)
        print(f"[{datetime.datetime.now()}] Weights changes detected and reported.")
    else:
        print(f"[{datetime.datetime.now()}] No changes detected in weights.")
    
    print(f"[{datetime.datetime.now()}] Weights check completed.")


def main():
    if not os.geteuid() == 0:
        sys.exit("\nOnly root can run this script\n")

    # Load .env file, or initialize it if it doesn't exist
    initialize_env_file(env_file)
    load_dotenv(env_file)
    webhook_url = DISCORD_WEBHOOK_URL

    if not validate_webhook(webhook_url):
        print("Failed to validate the webhook. Please check your URL and try again.")
        exit(1)
        
    # Check Updates
    if auto_update_enabled:
        update_start_time = check_for_updates()

    # Initialize start time
    watchdog_liveness = time.time()
    
    if not webhook_url or webhook_url == 'your_webhook_url_here':
        print("Webhook URL is not set in .env file. Exiting.")
        exit(1)

    # Check in with admins
    initial_message = f"Weights monitor script has started.\n\n"
    initial_weights = fetch_weights()
    initial_message += f"# Initial Weights:\n{json.dumps(initial_weights, indent=4)}"
    report_for_duty("Script Started", initial_message, webhook_url)

    # Commands for system setup commented out for brevity
    while True:
        try:
            # Liveness
            if time.time() - watchdog_liveness >= watchdog_interval:
                # Weights check
                check_weights(webhook_url)
                watchdog_liveness = time.time()

            # Updates
            if auto_update_enabled and time.time() - update_start_time >= update_interval:
                update_start_time = check_for_updates()

            time.sleep(60)
        except Exception as e:
            report_for_duty("Error", f"An error occurred in the weights monitor script: {str(e)}", webhook_url)


if __name__ == "__main__":
    main()