#! /bin/sh

if [ -e "/dev/serial0" ]; then
  echo "Found /dev/serial0."
else
  echo "Need to complete UART port setup from https://spellfoundry.com/2016/05/29/configuring-gpio-serial-port-raspbian-jessie-including-pi-3/"
  exit -1
fi

# also need to install git, vim, php

chmod 755 doortestd
sudo cp ./doortestd /etc/init.d/doortestd
sudo update-rc.d doortestd defaults
sudo cp update-amt-rfid /etc/cron.hourly/
echo "Setup complete."
