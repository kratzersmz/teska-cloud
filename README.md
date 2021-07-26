# IN DEVELOPING, NOT READY YET

# Info
Goal of this project is to have an hybrid installer for paedml-linux/paedml-windows, serving a nextcloud installation best practice the docker way  
This project is currently in developing. You'll find the prequisites for ubuntu server in the prerequisitsfile

# Instructions paedml-windows
## Add an A Record on your Domain to Octo/Sophos IP(in this case octo is 37.22.22.111)
e.g. cloud.friedrich-realschule.de	IN	A	37.22.22.111	3600s	(01:00:00)

## Prepare your Octogate:
1. Add a DMZ Interface:  
![DMZ](howto/fw_dmz.png?raw=true "DMZ Interface")

2. Add Portfreischaltungen:  
![DMZ](howto/fw_portfreischaltungen.png?raw=true "DMZ Portfreischaltungen")

3. Add Portweiterleitungen(SSH NOT NEEDED!):  
![DMZ](howto/fw_portweiterleitungen.jpg?raw=true "DMZ Portweiterleitungen")

## Prepare your Ldapbind user
Add an new ldapbinduser for nextcloud under _ServiceAccounts

## Add a new forward Lookup Zone in your DNS Server:
e.g. cloud.hans-schule.de and Point the A record directly to 192.168.201.7

if using collabora, point e.g. office.hans-schule.de directly with a A record to 192.168.201.7

# Instructions paedml-linux
