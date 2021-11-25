# Alpha Code
## ToDo
* Adding support for onlyoffice
* Adding configparameters for Update fixing
* Adding deny access for Klassenarbeits-User
* Adding loop over Schooltype to support multiple mandants
* More Docu
* Adding paedML Linux Support
* Adding LinuxMusterNet Support


# Info
Goal of this project is to have an hybrid installer for paedml-linux/paedml-windows, serving a nextcloud installation best practice the docker way  
This project is currently in developing. You'll find the prequisites for ubuntu server in the prerequisitsfile. Uses https://github.com/nextcloud/docker as best practice source.

Benefits:
- lets encrypt
- collabora installation
- best practice docker-compose way
- all automated in an interactive python script

# Instructions paedml-windows
## Add an A Record on your public Domain
In this example Octo/Sophos public IP is 37.22.22.111
e.g. cloud.hans-schule.de	IN	A	37.22.22.111	3600s	(01:00:00)

if you want to use collabora, please setup another domain e.g. office.hans-schule.de and point to same IP
Pls wait until the domain records where spread to all Nameservers(mostly 24h)


## Prepare your Octogate:
1. Add a Dummy switch without uplink and bind an portgroup to it (ESXi)
![DMZ](howto/fw_esxi_switch_portgruppe.jpg?raw=true "DMZ Interface")

2. Edit Octo Settings and Add this portgroup to second network Adapter (ESXi)
![DMZ](howto/fw_zuweisung.jpg?raw=true "DMZ Interface")

3. Add a DMZ Interface:
In ESXi add second network interface to a portgroup hanging on an vswitch without uplink
![DMZ](howto/fw_dmz.jpg?raw=true "DMZ Interface")

4. Add Portfreischaltungen:  
![DMZ](howto/fw_portfreischaltungen.png?raw=true "DMZ Portfreischaltungen")

5. Add Portweiterleitungen(SSH NOT NEEDED!):  
![DMZ](howto/fw_portweiterleitungen.jpg?raw=true "DMZ Portweiterleitungen")

## Prepare your dockerhost(nextcloud):
IP: 192.168.201.7

Subnet: 255.255.255.0

Gateway: 192.168.201.1

DNS: 8.8.8.8

## Prepare your Ldapbind user
Add an new ldapbinduser for nextcloud under _ServiceAccounts

## Add a new forward Lookup Zone in your DNS Server:
e.g. cloud.hans-schule.de and Point the A record directly to 192.168.201.7

if using collabora, point e.g. office.hans-schule.de directly with a A record to 192.168.201.7

## HowTo run
use an linux distri you want. this stuff was build on ubuntu-server, but any other distro with docker+docker-compose + a few python moduls should do. 

Install prerequisits metioned in the prerequists file in this repo

Install docker: https://docs.docker.com/engine/install/

Install docker-compose: https://docs.docker.com/compose/install/

git clone https://github.com/kratzersmz/teska-cloud.git

cd teska-cloud

start install script with:
python3 setup.py

## HowTo run of teska-esxi-vm
* navigate to /home/docker/teska-cloud
* bash initial-setup.sh


# Instructions paedml-linux
