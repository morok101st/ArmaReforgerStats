# README


## Clone Repo

```bash
git clone https://github.com/morok101st/ArmaReforgerStats.git
cd ArmaReforgerStats
```

## Build metrics image

```bash
docker compose build
```

## Set LOG path Arma Reforger

- **Adjust the Path in docker-compose.yaml:** Replace `/data/armar_ds/data/logs` with path where your Reforger logs are stored.

- **Server Configuration:** Ensure that in your Arma Reforger server configuration, the `-logStats` option is set to `2000` (t in ms). Reforger generate new log entry for stats every 2 sec.

## Start stack and check logs

```bash
docker compose up -d && docker compose logs -f
```

## Open browser for grafana url

- http://ServerIP:3000
- default username and password for grafana (change it)

### select data source prometheus
  
- connections -> data sources -> add (select Prometheus)
- connectionURL -> http://prometheus-py:9090
- button -> save and test 

### import reforger-dashboard.json to grafana

- dashboard -> new -> import
- provide the file or copy/paste the json content
  
### import node-exporter dashboard

- dashboard -> new -> import
- use ID -> insert 1860 -> select data source

- ex: use default dashboard from grafana.com (https://grafana.com/grafana/dashboards/1860-node-exporter-full/)

## credits

https://github.com/SebastianUnterscheutz/ArmaReforgerMetrics
