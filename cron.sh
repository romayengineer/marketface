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

/usr/bin/env |& tee -a /home/marketface/marketface.log

/usr/local/bin/python /home/marketface/marketface |& tee -a /home/marketface/marketface.log
