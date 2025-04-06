# Installation


- Clone Repo

```bash
git clone https://github.com/morok101st/ArmaReforgerStats.git
```

- change directory

```bash
cd ArmaReforgerStats
```

- Build metrics image

```bash
docker compose build
```

- Start stack and check logs

```bash
docker compose up -d && docker compose logs -f
```

- Open browser for grafana url

http://ServerIP:3000

default username and password for grafana (change it)

- import reforger-dashboard.json in grafana

- import node-exporter dashboard

use default dashboard from grafana.com (https://grafana.com/grafana/dashboards/1860-node-exporter-full/)
ex: 
import with ID (ID -> 1860)
select prometheus as source

