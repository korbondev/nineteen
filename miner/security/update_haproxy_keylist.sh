#!/bin/bash

# Check if jq is installed, and install it if not
if ! command -v jq &> /dev/null; then
    echo "jq not found, installing..."
    apt-get update && apt-get install -y jq
fi

# Input JSON file containing nodes
NODES_FILE="nodes.json"
# Output file for the hotkeys
HOTKEYS_FILE="/etc/haproxy/sn19_hotkeys.txt"

# Find the first environment file that starts with .coldkey-
ENV_FILE=$(ls .coldkey-* 2>/dev/null | head -n 1)

# Source the environment file to get the MIN_STAKE_THRESHOLD
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
else
    echo "No environment file found that starts with .coldkey-"
    exit 1
fi

# Extract hotkeys with stake greater than the threshold
temp_file=$(mktemp)
cat "$NODES_FILE" | jq -r --argjson threshold "$MIN_STAKE_THRESHOLD" 'to_entries[] | select(.value.stake > $threshold) | .value.hotkey' > "$temp_file"

# Check if there are any hotkeys and update the output file if there are
if [ -s "$temp_file" ]; then
    mv "$temp_file" "$HOTKEYS_FILE"
    echo "Hotkeys with stake > $MIN_STAKE_THRESHOLD have been written to $HOTKEYS_FILE"
else
    echo "No hotkeys with stake > $MIN_STAKE_THRESHOLD found."
    rm "$temp_file"
fi


# HAProxy configuration
# (in haproxy frontend)

# # Define an ACL to match the "validator-hotkey" header against a list of allowed keys
# acl is_pub_key_request path_beg /public-encryption-key
# acl allowed_hotkey hdr_sub(validator-hotkey) -f /etc/haproxy/sn19_hotkeys.txt

# # Deny the request with a 403 status if the "validator-hotkey" is not in the allowed list
# http-request deny if !is_pub_key_request !allowed_hotkey