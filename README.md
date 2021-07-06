# IN DEVELOPING, NOT READY YET

# Info
Goal of this project is to have an hybrid installer for paedml-linux/paedml-windows, serving a nextcloud installation best practice the docker way  
This project is currently in developing. 

# Instructions paedml-windows
## Prepare your Octogate:
1. Add a DMZ Interface:  
Netzwerk -> IP-Adressen -> Neuer Eintrag:   
Name: DMZ  
IP-Adresse: 192.168.201.1  
Interface: DMZ  
Subnetz: 24

2. Add Portfreischaltungen (all devices in DMZ can access internet on all ports):  
Position: next iterate  
Beschreibung: dmz_internet  
Port: leave empty  
Protokoll: ALL  
Int IN: DMZ  
Quelle: 0.0.0.0  
In OUT: EXT  
Ziel: 0.0.0.0  
Action: ACCEPT



# Instructions paedml-linux
