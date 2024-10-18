# update_haproxy_keylist.sh usage:

### Set in cron

run miner once, then restart once
make sure the nodes.json is in the repo dir from the miner

Run once:

```bash
/root/nineteen/miner/security/update_haproxy_keylist.sh
```

Schedule in cron:

```bash
crontab -e
# add to bottom

# Keep the haproxy keylist up to date
*/15 * * * * /root/nineteen/miner/security/update_haproxy_keylist.sh
```

# cloudflare_spectrum_update.py usage:

### Example .env for cloudflare_spectrum_update.py

```
CLOUDFLARE_API_KEY=
CLOUDFLARE_BEARER_TOKEN=
CLOUDFLARE_EMAIL=email@domain.com
CLOUDFLARE_ZONE_ID=
CLOUDFLARE_DNS_NAME_PREFIX=btt-sn19-
CLOUDFLARE_PORT_INCREMENT_AMT=1
PREFIX_ONLY_ON_DNS=btt-sn19-
REPO_DIRECTORY=/root/nineteen
UPDATE_NODE_PORT_IN_NODE_FILE=true
```

### Initial Config for miner using cloudflare_spectrum_update.py

```bash
sudo apt install -y python3.11 python3.11-venv
cd ~/nineteen/miner/security
deactivate;
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 cloudflare_spectrum_update.py zero lb.ip.ad.dy
```

### Increment IP using cloudflare_spectrum_update.py

```bash
sudo apt install -y python3.11 python3.11-venv
cd ~/nineteen/miner/security
deactivate;
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 cloudflare_spectrum_update.py increment lb.ip.ad.dy
```
