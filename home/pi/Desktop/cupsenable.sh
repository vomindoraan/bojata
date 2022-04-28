#!/bin/bash
lpstat -p | awk '{print $2}' | xargs cupsenable -c
