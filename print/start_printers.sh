#!/bin/bash
# (Re)start all printers, cancel existing jobs
lpstat -p | awk '{ print $2 }' | xargs cupsenable -c
