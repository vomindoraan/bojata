#!/bin/bash
# Set all printers' error policies to abort-job (instead of the default stop-printer)
lpstat -s | awk -F"device for " '{ print $2 }' | awk -F":" '{ print $1 }' | while read line; do
   if [ -n "$line" ]; then
      echo "Changing error policy to abort-job for $line"
      lpadmin -p "$line" -o printer-error-policy=abort-job
   fi
done
