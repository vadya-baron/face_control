#!/bin/bash
apt-get install -y cron
cp -R ./backup-cron /etc/cron.d/backup-cron
chmod 0644 /etc/cron.d/backup-cron
crontab /etc/cron.d/backup-cron
touch /var/log/cron.log
cron -f