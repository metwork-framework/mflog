#!/bin/bash

find /home/buildcache -type f -atime +30 -exec rm -f {} \; >/dev/null 2>&1
chown -RL metworkpub:metworkpub /home/buildcache
chmod -R 755 /home/buildcache
