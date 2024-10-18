#!/usr/bin/expect -f

# Timeout for each command's response
set timeout -1


# Command-line arguments
set start_coldkey_number [lindex $argv 0]
set start_hotkey_number [lindex $argv 1]

set num_hotkeys_per_coldkey [lindex $argv 2]
set num_hotkeys [lindex $argv 3]

set axon_start_port [lindex $argv 4]

set image_port [lindex $argv 5]
set llama_3_1_8b_port [lindex $argv 6]
set llama_3_2_3b_port [lindex $argv 7]
set llama_3_1_70b_port [lindex $argv 8]

set chain_endpoint [lindex $argv 9]


# Initialize coldkey number
set coldkey_number $start_coldkey_number

set original_hotkey_number $start_hotkey_number

# Initialize hotkey increment var
set h 0

# Helper procedure to get the external IP for a given subdomain
proc get_external_ip {subdomain} {
    set result [exec nslookup $subdomain | grep "Address: " | tail -n 1 | awk "{print \$2}"]
    return $result
}

# Loop to configure hotkeys
for {set i 0} {$i < $num_hotkeys} {incr i} {

    spawn python3 core/create_config.py --miner

    # Check if we need to increment coldkey and reset hotkey number
    if {$i > 0 && $i % $num_hotkeys_per_coldkey == 0} {
        incr coldkey_number
        set start_hotkey_number $original_hotkey_number
        set h 0
    }

    set coldkey_suffix [format "%02d" [expr $coldkey_number]]
    set coldkey "coldkey-$coldkey_suffix"

    set hotkey_suffix [format "%02d" [expr $start_hotkey_number + $h]]
    set hotkey "$coldkey-hotkey-$hotkey_suffix"

    set axon_port [expr $axon_start_port + $i]

    # Form the subdomain and get the external IP
    set subdomain "btt-sn19-$hotkey.tududes.com"
    set external_ip [get_external_ip $subdomain]

    puts "Subdomain: $subdomain, External IP: $external_ip"


    # Provide answers for the prompts
    expect "Enter wallet name"
    send -- "$coldkey\r"

    expect "Enter hotkey name"
    send -- "$hotkey\r"

    expect "Enter subtensor network"
    send -- "finney\r"

    expect "Enter subtensor address"
    send -- "$chain_endpoint\r"

    expect "Enter the port to run the miner server on"
    send -- "$axon_port\r"

    # Worker URL configurations
    expect "Enter IMAGE_WORKER_URL:"
    send -- "127.0.0.1:$image_port\r"

    expect "Enter LLAMA_3_1_8B_TEXT_WORKER_URL:"
    send -- "127.0.0.1:$llama_3_1_8b_port\r"

    expect "Enter LLAMA_3_2_3B_TEXT_WORKER_URL:"
    send -- "127.0.0.1:$llama_3_2_3b_port\r"

    expect "Enter LLAMA_3_1_70B_TEXT_WORKER_URL:"
    send -- "127.0.0.1:$llama_3_1_70b_port\r"

    expect "Enter MIN_STAKE_THRESHOLD"
    send -- "1000\r"

    expect "Enter MINER_TYPE"
    send -- "text\r"

    # add something to the end of the file
    sleep 1;
    set env_file ".$hotkey.env"
    exec sh -c "echo 'NODE_EXTERNAL_IP=$external_ip' >> $env_file"
    exec sh -c "echo 'NODE_EXTERNAL_PORT=$axon_port' >> $env_file"

    incr h
}


# sirouk 2024-07-13 - additional miners
set start_coldkey_number 1
set start_hotkey_number 9

set num_hotkeys_per_coldkey 2
set num_hotkeys 12

set axon_start_port [expr $axon_start_port + $i]

set image_port [lindex $argv 5]
set llama_3_1_8b_port [lindex $argv 6]
set llama_3_2_3b_port [lindex $argv 7]
set llama_3_1_70b_port [lindex $argv 8]

set chain_endpoint [lindex $argv 9]


# Initialize coldkey number
set coldkey_number $start_coldkey_number

set original_hotkey_number $start_hotkey_number

# Initialize hotkey increment var
set h 0


# Loop to configure hotkeys
for {set i 0} {$i < $num_hotkeys} {incr i} {

    spawn python3 core/create_config.py --miner

    # Check if we need to increment coldkey and reset hotkey number
    if {$i > 0 && $i % $num_hotkeys_per_coldkey == 0} {
        incr coldkey_number
        set start_hotkey_number $original_hotkey_number
        set h 0
    }

    set coldkey_suffix [format "%02d" [expr $coldkey_number]]
    set coldkey "coldkey-$coldkey_suffix"

    set hotkey_suffix [format "%02d" [expr $start_hotkey_number + $h]]
    set hotkey "$coldkey-hotkey-$hotkey_suffix"

    set axon_port [expr $axon_start_port + $i]

    # Form the subdomain and get the external IP
    set subdomain "btt-sn19-$hotkey.tududes.com"
    set external_ip [get_external_ip $subdomain]

    puts "Subdomain: $subdomain, External IP: $external_ip"


    # Provide answers for the prompts
    expect "Enter wallet name"
    send -- "$coldkey\r"

    expect "Enter hotkey name"
    send -- "$hotkey\r"

    expect "Enter subtensor network"
    send -- "finney\r"

    expect "Enter subtensor address"
    send -- "$chain_endpoint\r"

    expect "Enter the port to run the miner server on"
    send -- "$axon_port\r"

    # Worker URL configurations
    expect "Enter IMAGE_WORKER_URL:"
    send -- "127.0.0.1:$image_port\r"

    expect "Enter LLAMA_3_1_8B_TEXT_WORKER_URL:"
    send -- "127.0.0.1:$llama_3_1_8b_port\r"

    expect "Enter LLAMA_3_2_3B_TEXT_WORKER_URL:"
    send -- "127.0.0.1:$llama_3_2_3b_port\r"

    expect "Enter LLAMA_3_1_70B_TEXT_WORKER_URL:"
    send -- "127.0.0.1:$llama_3_1_70b_port\r"

    expect "Enter MIN_STAKE_THRESHOLD"
    send -- "1000\r"

    expect "Enter MINER_TYPE"
    send -- "text\r"

    # add something to the end of the file
    sleep 1;
    set env_file ".$hotkey.env"
    exec sh -c "echo 'NODE_EXTERNAL_IP=$external_ip' >> $env_file"
    exec sh -c "echo 'NODE_EXTERNAL_PORT=$axon_port' >> $env_file"

    incr h
}


# Wait for the process to finish
expect eof
