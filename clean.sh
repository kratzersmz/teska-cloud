#!/bin/bash
docker-compose down  --remove-orphans
docker volume rm teska-cloud_vhost.d
docker volume rm teska-cloud_html
docker volume rm teska-cloud_db
docker volume rm teska-cloud_nextcloud
rm *.tar
rm *.env
rm *.json
rm .env
