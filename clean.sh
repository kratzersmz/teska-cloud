#!/bin/bash
docker-compose down  --remove-orphans
docker volume rm teska-nextcloud_vhost.d
docker volume rm teska-nextcloud_html
docker volume rm teska-nextcloud_db
docker volume rm teska-nextcloud_nextcloud
rm *.tar
rm *.env
