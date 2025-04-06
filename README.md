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

- select data source prometheus
  
  connections -> data sources -> add (select Prometheus)
  
  connectionURL -> http://prometheus-py:9090
  
  button -> save and test 

- import reforger-dashboard.json to grafana

  dashboard -> new -> import
  
  provide the file or copy/paste the json content
  
- import node-exporter dashboard
  dashboard -> new -> import
  
  use ID -> insert 1860 -> select data source

use default dashboard from grafana.com (https://grafana.com/grafana/dashboards/1860-node-exporter-full/)

ex: 

import with ID (ID -> 1860)

