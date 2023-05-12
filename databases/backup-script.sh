#!/bin/bash

mkdir -p /data/docker/databases/base_bacup/`date +%F`;

docker-compose -f /data/docker/docker-compose.yml exec -T face_control_mysql mysqldump --no-tablespaces -uroot -p face_control | gzip > /data/docker/databases/base_bacup/`date +%F`/face_control_`date +%H-%M`.sql.gz
echo "face_control Backup "`date +%F_%H-%M`;


/usr/bin/find /data/docker/databases/base_bacup/. -depth -maxdepth 1 -mindepth 1 -xdev -type d -mtime +15  -exec /bin/rm -rf '{}' \;
