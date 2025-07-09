#!/usr/bin/bash

PYTHON_VERSION=3.10.18
PWD=/home/marketface
HOME=/home/marketface
LANG=C.UTF-8
TERM=xterm
DISPLAY=:0
SHLVL=1
PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
_=/usr/bin/env

cd /home/marketface

# log env to know display and other envs are set up ok
/usr/bin/env 2>&1 | tee -a /home/marketface/marketface.log

# run script with flock to create a lock file and run once at the time
flock -n /var/lock/marketface.lock -c "/usr/local/bin/python /home/marketface/marketface" 2>&1 | tee -a /home/marketface/marketface.log
