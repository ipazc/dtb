#!/bin/bash
####
# INSTALL SCRIPT FOR DTB
# AUTHOR: Ivan de Paz Centeno

if [[ "$USER" != "root" ]]
then
    echo "Error: root is required to install this tool."
    exit -1
fi

if [[ "$1" == "--remove" ]]
then
    rm -r /usr/local/dtb
    rm /usr/bin/dtb
    echo "[OK] Removed successfully."
    exit 0
fi

mkdir -p /usr/local/dtb/
cp -r * /usr/local/dtb/
ln -s /usr/local/dtb/dtb.py /usr/bin/dtb
chmod +x /usr/local/dtb/dtb.py
chmod +x /usr/bin/dtb

echo "Done."

