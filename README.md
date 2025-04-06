# Installation


- Clone Repo

´´´bash
https://github.com/morok101st/ArmaReforgerStats.git
´´´

- change directory

´´´bash
cd ArmaReforgerStats
´´´

- Build metrics image

´´´bash
docker compose build
´´´

- Start stack and check logs

´´´bash
docker compose up -d && docker compose logs -f
´´´

- Open browser to url

http://<ServerIP>:3000

default username and password for grafana (change it)

