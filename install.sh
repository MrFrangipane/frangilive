#!/bin/bash

# OVERWITCH

sudo apt install automake libtool libusb-1.0-0-dev libjack-jackd2-dev libsamplerate0-dev libsndfile1-dev autopoint gettext libsystemd-dev libjson-glib-dev python3-virtualenv jackd

cd ~

git clone https://github.com/dagargo/overwitch.git
cd overwitch
git checkout 2.1

autoreconf --install
CLI_ONLY=yes ./configure
make
sudo make install
sudo ldconfig

cd udev
sudo make install

cd ../systemd
sudo make install

cd ..

systemctl start overwitch --user
systemctl --user enable overwitch.service

# PYTHON

cd ~
python -m venv frangilive
source frangilive/bin/activate

pip install -r requirements.txt

python test.py