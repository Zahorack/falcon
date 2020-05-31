#!/bin/bash

sleep 2
while true; do

  SERVICE="python3.7"
  if pgrep -x "$SERVICE" >/dev/null
  then
      echo ""
  else
      echo "$SERVICE stopped"
      sudo /usr/bin/python3.7 /home/pi/Projects/falcon/app.py
  fi
  sleep 1

  done
