#!/usr/bin/env python3
# mostly copied and pasted from sources on the internet.....
# kratzer@lmz-bw.de

import sys
import socket
from contextlib import closing
import subprocess
from subprocess import PIPE
from configparser import SafeConfigParser
import os
import ldap
import docker
import tarfile
import secrets
import time
import json
import yaml
import shutil

# consts
masters = dict(windows="dc01.musterschule.schule.paedml", linux="server.paedml-linux.lokal")
mastersIP = dict(windows="10.1.1.1", linux="10.1.0.1")
dataServers = dict(windows="sp01.musterschule.schule.paedml", linux="server.paedml-linux.lokal")
dataServersIP = dict(windows="10.1.1.2")
ncConfigs = dict(windows="config-win.json.tmpl", linux="config-linux.json.tmpl")
ncConfigShareTeacher = dict(windows="teacher-shares-win.json.tmpl", linux="teacher-shares-linux.json.tmpl")
ncConfigSharePupil = dict(windows="pupil-shares-win.json.tmpl", linux="pupil-shares-linux.json.tmpl")
LdapPorts = dict(windows=636, linux=7636)
smbPort = 445
RUNNING = 'running'
ncContainerName = 'teska-cloud_app_1'
client = docker.from_env()
currentDir, currentFile = os.path.split(os.path.abspath(__file__))

## loop over parameters
#parser = SafeConfigParser()
#parser.add_argument("-fu", "--fixupdate", dest="fixupdate", default="true")
#parser.add_argument("-u", "--update", dest="update", default="true")

# do parser argument stuff
#if fixupdate:
  

# write hosts file
def add_hosts_file(ip,hostname):
    if ip in open('/etc/hosts', 'r').read():
        print("Hosts already modified")
    else:
        with open("/etc/hosts", "a") as myfile:
            myfile.write("{0} {1}\n".format(ip,hostname))
            myfile.close()


# Clean Dir (remove *.tar)
def clean_dir():
    files = os.listdir(currentDir)
    for file in files:
      if file.endswith(".tar"):
        os.remove(os.path.join(currentDir,file))


# run docker-compose with filename (disabled usage of filename in code)
def run_docker_compose(filename):
    command_name = ["docker-compose", "up", "-d", "--build"]
    popen = subprocess.check_call(command_name, stdout=sys.stdout,stderr=subprocess.STDOUT)


# bringing docker-compose down with filename (disabled usage of filename in code)
def down_docker_compose(filename):
    command_name = ["docker-compose", "down"]
    popen = subprocess.Popen(command_name, stdin=PIPE,stdout=PIPE, stderr=PIPE)
    return popen
 
   
# Copy files to Container
#https://stackoverflow.com/questions/46390309/how-to-copy-a-file-from-host-to-container-using-docker-py-docker-sdk
def container_copy_file(src,dst):
    name, dst = dst.split(':')
    container = client.containers.get(name)
    os.chdir(os.path.dirname(src))
    srcname = os.path.basename(src)
    tar = tarfile.open(src + '.tar', mode='w')
    try:
        tar.add(srcname)
    finally:
        tar.close()

    data = open(src + '.tar', 'rb').read()
    container.put_archive(os.path.dirname(dst), data) 


# Check if container is running
def container_is_running(container_name):
    container = DOCKER_CLIENT.containers.get(container_name)
    container_state = container.attrs['State']
    container_is_running = container_state['Status'] == RUNNING
    return container_is_running


# check container state
def container_status(container_name):
    container = DOCKER_CLIENT.containers.get(container_name)
    container_state = container.attrs['State']
    return container_state


# set initial setup stuff
def nextcloud_initial_setup(password):
    command_name = ["docker", "exec", "{0}".format(ncContainerName), "su", "www-data", "-s", "/bin/sh", "-c",
                    'php occ user:add --display-name="nc-admin" --group="admin" --password-from-env nc-admin']
    my_env = os.environ.copy()
    my_env["OC_PASS"] = password
    popen = subprocess.Popen(command_name, stdout=sys.stdout, stderr=subprocess.STDOUT, env=my_env)
    return popen


# configure ldap stuff
def nextcloud_configure_ldap(username, password, email):
    command_name = ["docker", "exec", ncContainerName, "su", "www-data", "-s", "/bin/sh", "-c",
                    "php occ maintenance:install --admin-user {0} --admin-pass {1} --admin-email {2}".format(username,
                                                                                                             password,
                                                                                                             email)]
    popen = subprocess.Popen(command_name, stdout=sys.stdout, stderr=subprocess.STDOUT)


# basic command for general nextcloud setting configs via occ
def nextcloud_configure_general(occommand):
    command_name = ["docker", "exec", "{0}".format(ncContainerName), "su", "www-data", "-s", "/bin/sh", "-c",
                    "php occ {0}".format(occommand)]

    print("docker exec {0} su www-data -s /bin/sh -c php occ {1}".format(ncContainerName,occommand))
    popen = subprocess.Popen(command_name, stdout=sys.stdout, stderr=subprocess.STDOUT)
    return popen


# pinging function
def ping(hostname, waittime=1000):
    assert isinstance(hostname, str), \
        "IP/hostname must be provided as a string."
    if os.system("ping -c 1 -W " + str(waittime) + " " +
                 hostname + " > /dev/null 2>&1") == 0:
        hostup = True
    else:
        hostup = False
    return hostup


# check open ports
def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(2)
        if sock.connect_ex((host, port)) == 0:
            return True
        else:
            return False


# get all xx=xx from ENV Files
def getprops(filename):
    with open(filename, "r") as file:
        props = dict(
            line.strip().split('=', 1) for line in file if not line.startswith("#") and not len(line.strip()) == 0)
        file.close()
        return props


# write full dict back to ENV Files
def writeprop(filename, props):
    f = open(filename, "w")
    for key, value in props.items():
        f.write('{0}={1}\n'.format(key, value))
    f.close()


# get yml dict (docker-compose.yml)
def getyml(filename):
    try:
        with open(filename) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        f.close()
        return data
    except:
        print("File {0} not found or file isnt a yaml file".format(filename))


# write yml dict back to file
def writeyml(filename, props):
    try:
        with open(filename, 'w') as f:
            data = yaml.dump(props, f)
        f.close()
        return data
    except:
        print("File {0} not found or file isnt a yaml file".format(filename))


# get json config file to dict
def nextcloud_get_config(filename):
    try:
        with open(filename, "r") as json_file:
            data = json.load(json_file)
            json_file.close()
            return data
    except:
        print("File not {0} found or file isnt a json file....".format(filename))


# write json to filename
def nextcloud_write_config(data,filename):
    try:
       with open(filename,"w") as json_file:
         json.dump(data, json_file)
         json_file.close()
    except:
      print("File {0} error writing .....".format(filename))


# set root pw
def setpassword(username: str, password: str):
    p = subprocess.Popen(["/usr/sbin/chpasswd"], universal_newlines=True, shell=False, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate(username + ":" + password + "\n")
    assert p.wait() == 0
    if stdout or stderr:
        raise Exception("Error encountered changing the password!")


# default input value
def default_input(message, defaultval):
    if defaultval:
        return input("%s [%s]:" % (message, defaultval)) or defaultval
    else:
        return input("%s " % message)


# checking ldap user/pw
def ldap_initialize(remote, port, user, password, use_ssl=False, timeout=None):
    prefix = 'ldap'
    if use_ssl is True:
        prefix = 'ldaps'
        # ask ldap to ignore certificate errors
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

    if timeout:
        ldap.set_option(ldap.OPT_NETWORK_TIMEOUT, timeout)

    ldap.set_option(ldap.OPT_REFERRALS, ldap.OPT_OFF)
    server = prefix + '://' + remote + ':' + '%s' % port
    try:
      conn = ldap.initialize(server)
      conn.simple_bind_s(user, password)
    except:
      return False
    return True



# some standard colors
# todo fix colors
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


"""
# check parser stuff
if fixupdate:
    print("Deaktiviere das Erlauben zum Ändern des eigenen Profiles.....", end="")
    nextcloud_configure_general('db:add-missing-indices')
    time.sleep(2)
    nextcloud_configure_general('db:add-missing-columns')
    time.sleep(2)
    nextcloud_configure_general('db:add-missing-primary-keys')
    print("erledigt!")
    time.sleep(5)
    sys.exit(0)
"""

# print teska info
try:
  sourceFile = open('teska.ascii', 'r')
  asciiArt = sourceFile.read()
  print(asciiArt)
  sourceFile.close()
except:
  print("Cant open {0}".format(sourceFile))


# Check if root/docker access
try:
    DOCKER_CLIENT = docker.DockerClient(base_url='unix://var/run/docker.sock')
except:
    print("Aktueller user ist nicht root bzw. kein Zugang zur docker Instanz. Breche Installationsript nun ab!")
    sys.exit(4)


# General Info
print("Bitte notiere Dir das NEUE root Passwort")
print(
    "Die Urls für Nextcloud/collabora müssen vorher beim Domainhoster eingetragen werden")
print(
    "Bevor hier weiter gemacht wird, vergewissere Dich, dass die Firewall wie lt. Anleitung konfiguriert ist.")
input("Drücke Enter um fortzufahren...")

# bring down running docker-compose instance
print("Beende etwaig laufende docker-compose Instanzen von Nextcloud....")
down_docker_compose('docker-compose.yml')

# add hosts data to hosts file
print("Füge Hosts zu /etc/hosts hinzu")
add_hosts_file(mastersIP["windows"], masters["windows"])
add_hosts_file(dataServersIP["windows"], dataServers["windows"])
add_hosts_file(mastersIP["linux"], masters["linux"])


# clean dir
clean_dir()


# check if paedml linux or paedml windows
print("Checking if paedml-linux or paedml-windows")
if ping(masters['linux']):
    PaedML = "linux"
    print("Eine PaedML Linux gefunden!")
elif ping(masters['windows']):
    if ping(dataServers['windows']):
        PaedML = "windows"
        print("Eine PaedML Windows gefunden!")
else:
    while True:
        PaedML = input("Kann die paedML Version nicht selbst bestimmen. Bitte gib selbst an ob windows oder linux(windows/linux): ")
        if PaedML.lower() in ['windows', 'win', 'w']:
            PaedML = "windows"
        elif PaedML.lower() in ['linux', 'li', 'l']:
            PaedML = "linux"
        else:
            print("Bitte gib windows oder linux ein!")


"""
# Begin testing Basics work
print(f"{bcolors.BOLD}Teste ob dc01 erreichbar via ping....")
if ping():
    print(f"{bcolors.OKGREEN}dc01 ist erreichbar")
else:
    print(
        "dc01 ist nicht erreichbar. Bitte prüfe Firewall Regeln/Verbindungen/DNS. Breche Installationscript nun ab!")
    sys.exit(5)

print(f"{bcolors.BOLD}Teste ob sp01 erreichbar via ping....")
if ping(sp01):
    print(f"{bcolors.OKGREEN}sp01 ist erreichbar")
else:
    print(
        "sp01 ist nicht erreichbar. Bitte prüfe Firewall Regeln/Verbindungen/DNS. Breche Installationscript nun ab!")
    sys.exit(6)
"""

print("Teste grundsätzlich ob der SMB Port 445/tcp von " + dataServers[PaedML] + " erreichbar.......")
if check_socket(dataServers[PaedML], smbPort):
    print("SMB Port 445/tcp " + dataServers[PaedML] +" erreichbar.")
else:
    print("SMB Port 445/tcp " + dataServers[PaedML] +" nicht erreichbar. Bitte prüfe Firewall Regeln/Verbindungen/DNS. Breche Installationsscript nun ab!")
    sys.exit(7)

print("Teste grundsätzlich ob der ldap Port " +  str(LdapPorts[PaedML]) +"/tcp auf " + masters[PaedML] + " erreichbar.......")
if check_socket(masters[PaedML], LdapPorts[PaedML]):
    print("Ldap Port "+ str(LdapPorts[PaedML]) + "/tcp von " + masters[PaedML] +" erreichbar.")
else:
    print("Ldap Port "+ str(LdapPorts[PaedML]) +"/tcp von "+ masters[PaedML] +" nicht erreichbar. Bitte prüfe Firewall Regeln/Verbindungen/DNS. Breche Installationsscript nun ab!")
    sys.exit(8)

"""
while True:
    HostRootPw = input("Wie soll das neue root Passwort für diese virtuelle Maschine laufen(min 6 Zeichen)?: ")
    if (len(HostRootPw) >= 6):
        setpassword('root',HostRootPw)
        break
    else:
        print("Das Passwort ist keine 6 Zeichen lang!")
"""

# School Type for setting shares correcly
while True:
    SchoolTypeShort = input("Wie ist das Schulartkürzel der paedML Installation(Gross/Klein beachten..)?: ")
    if (len(SchoolTypeShort) <= 0):
        print("Zu kurzer Wert, bitte nochmal")
    else:
        break


# Nextcloud nc-admin Password
while True:
    CloudPassword = input("Wie soll das Passwort für den nc-admin sein(Weboberflächenadmin, min 8 Zeichen)?: ")
    if len(CloudPassword) > 8:
        break
    else:
        print("Das Passwort ist keine 8 Zeichen lang! Nochmal!")


# Nextcloud ldap user
while True:
    LdapUser = input("Username vom ldap bind user, welcher zuvor eingerichtet wurde?: ")
    if len(LdapUser) <= 0:
        print("Keinen User eingegeben, bitte nochmal!!")
    else:
        break


# Nextcloud ldap pw
while True:
    LdapPassword = input("Zugehöriges Password von {0}?: ".format(LdapUser))
    if len(LdapPassword) <= 0:
        print("Leeres Password, bitte nochmal!!")
    else:
        break


# Cloud Url Stuff
if os.path.isfile("hosts.env"):
  HostProps = getprops("hosts.env")
else:
  HostProps = getprops("hosts.env.tmpl")
while True:
        CloudUrl = default_input("Wie ist die öffentliche domain/subdomain deiner nextcloud instanz(ohne https://)",
                                 HostProps["VIRTUAL_HOST"])
        if len(CloudUrl) < 3:
            print("Ungültige Eingabe(zu wenig Zeichen)!")
        if not '.' in CloudUrl:
            print("Ungültige Eingabe(für eine richtige domain fehlt ein . in der domain!")
        else:
            CloudEmail = 'admin@' + CloudUrl
            HostProps["LETSENCRYPT_EMAIL"] = CloudEmail
            HostProps["LETSENCRYPT_HOST"] = CloudUrl
            HostProps["VIRTUAL_HOST"] = CloudUrl
            break

print("Personalisiere hosts.env...")
try:
    writeprop('hosts.env', HostProps)
except:
    print("Konnte hosts.env nicht schreiben....")



# Collabora Url Stuff
if os.path.isfile("collabora.env"):
  CollaboraProps = getprops("collabora.env")
else:
  CollaboraProps = getprops("collabora.env.tmpl")
while True:
        CollaboraEnable = default_input("Soll eine Collabora Instanz eingerichtet werden? (J/n)", "J")
        if CollaboraEnable.lower() in ['j', 'ja', 'y', 'yes']:
          CollaboraEnable = True
          CollaboraUrl = default_input("Wie ist die öffentliche domain/subdomain deiner collabora instanz(ohne https://)",
                                 CollaboraProps["VIRTUAL_HOST"])
          if len(CollaboraUrl) < 1:
              print("Ungültige Eingabe(zu wenig Zeichen)!")
          elif not '.' in CollaboraUrl:
              print("Ungültige Eingabe(für eine richtige domain fehlt ein . in der domain!")
          elif HostProps["VIRTUAL_HOST"].lower() == CollaboraUrl.lower():
              print("Collabora Domain kann nicht die gleiche wie die Nextcloud Domain sein!")
          else:
              CollaboraEmail = 'admin@' + CollaboraUrl
              CollaboraProps["LETSENCRYPT_EMAIL"] = CollaboraEmail
              CollaboraProps["LETSENCRYPT_HOST"] = CollaboraUrl
              CollaboraProps["VIRTUAL_HOST"] = CollaboraUrl
              CollaboraProps["domain"] = CloudUrl
              CollaboraProps["password"] = secrets.token_urlsafe(14)
              if os.path.isfile('docker-compose.override.yml.tmpl'):
                try:
                  shutil.copy2('docker-compose.override.yml.tmpl', 'docker-compose.override.yml')
                  print("erledigt!")
                except:
                  print('Kann docker-compose.override.yml.tmpl nicht nach docker-compose.override.yml kopieren')
              break
        else:
          print("Überspringe collabora Einrichtung, kann später noch händisch nachgeholt werden....!")
          if os.path.isfile('docker-compose.override.yml'):
              try:
                  os.rename('docker-compose.override.yml', 'docker-compose.override.yml.tmp2')
                  print("erledigt!")
              except:
                  print('Kann docker-compose.override.yml.tmp nicht nach docker-compose.override.yml2 umbennen')
          break


if CollaboraEnable:
    print("Personalisiere collabora.env...",end="")
    try:
        writeprop('collabora.env', CollaboraProps)
        print("erledigt!")
    except:
        print("Konnte collabora.env nicht schreiben....")

""" Currently not needed to edit yml files
    print("Personalisiere collabora docker-compose override und aktiviere.....", end="")
    try:
        os.rename('docker-compose.override.yml_tmp', 'docker-compose.override.yml')
        print("erledigt!")
    except:
        print('Kann docker-compose.override.yml_tmp nicht nach docker-compose.override.yml umbennen')

    yml = getyml('docker-compose.yml')
    yml['services']['collab'][]
"""

print("Personalisiere generell .env...")
GeneralProps = getprops(".env.tmpl")
GeneralProps["NEXTDOMAIN"] = CloudUrl
if CollaboraEnable:
    GeneralProps["OFFICEDOMAIN"] = CollaboraUrl
else:
    GeneralProps["OFFICEDOMAIN"] = "non.tes-ka.de"
try:
    writeprop(".env", GeneralProps)
except:
    print("Konnte .env nicht schreiben....")

# DB ENVs
if os.path.isfile("db.env"):
  DbProps = getprops("db.env")
else:
  DbProps = getprops("db.env.tmpl")
# todo: logge altes PW in log datei....
if len(DbProps["MYSQL_ROOT_PASSWORD"]) < 8:
    print("Scheint so, also ob die Länge des DB root PWs kleiner 8 wäre, erstelle ein nun ein neues random pw...")
    DbProps["MYSQL_ROOT_PASSWORD"] = secrets.token_urlsafe(12)
if len(DbProps["MYSQL_PASSWORD"]) < 8:
    print("Scheint so, als ob die Länge des db PWs kleiner 8 wäre, erstelle ein neues random pw!")
    DbProps["MYSQL_PASSWORD"] = secrets.token_urlsafe(12)
try:
    writeprop("db.env", DbProps)
except:
    print("Konnte db.env nicht schreiben....")


# start docker-compose and check if container is online
print("Downloade/Starte Docker Container(nextcloud, fpm, redis, letsencrypt, mariadb,...). Dies kann je nach Verbindung einige Minuten dauern. Bitte den Prozess nicht abbrechen.....")
run_docker_compose('docker-compose.yml')
while True:
    time.sleep(5)
    try:
        container_is_running(ncContainerName)
        print('....erledigt!')
        break
    except:
        print('.', end='')


# change admin password nextcloud
print("Richte Nextcloud nc-admin user mit Passwort ein....", end='')
try:
  #todo health check of all containers, workaround waiting 15 secs....
  print('Warte 15 secs bis alle Container gestartet sind...')
  time.sleep(15)
  nextcloud_configure_general('maintenance:install --database=mysql --database-host=db --database-name=nextcloud --database-user=nextcloud --database-pass={0} --admin-user "nc-admin" --admin-pass "{1}"'.format(DbProps["MYSQL_PASSWORD"],CloudPassword))
  print('Warte bis Nextcloud Grundinstallation komplett.....20 secs')
  time.sleep(20)
  nextcloud_configure_general('user:disable admin')
  print('erledigt!')
except:
    print('error!')
time.sleep(5)


# add to trusted domains
print("Add Domain to trusted Domains of nextcloud....", end='')
try:
  nextcloud_configure_general('config:system:set trusted_domains 1 --value={0}'.format(CloudUrl))
  print('erledigt!')
except:
    print('error!')
time.sleep(5)


# add ldap setup to nextcloud
print("PreCheck von Ldap Username/PW direkt am Server....", end='')
if ldap_initialize(masters[PaedML], LdapPorts[PaedML], LdapUser, LdapPassword, use_ssl=False, timeout=4000):
    print("Kombination aus Username/Passwort für Ldapserver scheint zu funktionieren")
else:
    print("Kombination aus User/Passwort für Ldapserver scheint falsch zu sein, mache trotzdem weiter...Du kannst es später in den der Nextcloud Weboberfläche ändern...!")


# Ldap Plugin enable
print("aktiviere user_ldap plugin......", end="")
nextcloud_configure_general("app:enable user_ldap")
print("erledigt!")
time.sleep(5)



# Files external enable
print("aktiviere files_external plugin.....", end="")
nextcloud_configure_general("app:enable files_external")
print("erledigt!")
time.sleep(5)



print("erstelle leere ldap config s01.....", end="")
nextcloud_configure_general("ldap:create-empty-config")
print("erledigt!")
time.sleep(5)



# Starting setup Ldap
print("Beginne mit Nextcloud Ldap Setup(User einrichten, Queries schreiben)....", end="")
if PaedML == 'windows':
  ncConfig = nextcloud_get_config(ncConfigs['windows'])
  ncConfig['apps']['user_ldap']['s01ldap_dn'] = "CN={0},OU=_ServiceAccounts,DC=musterschule,DC=schule,DC=paedml".format(LdapUser)
  ncConfig['apps']['user_ldap']['s01ldap_userfilter_groups'] = "G_Lehrer_{0}\nG_Schueler_{0}".format(SchoolTypeShort)
  #ncConfig['apps']['user_ldap']['s01ldap_agent_password'] = "{0}".format(LdapPassword)
  nextcloud_write_config(ncConfig, "{0}/{1}".format(currentDir,os.path.splitext(os.path.basename(ncConfigs['windows']))[0]))
  container_copy_file("{0}/{1}".format(currentDir,os.path.splitext(os.path.basename(ncConfigs['windows']))[0]),"{0}:/tmp/{1}".format(ncContainerName,os.path.splitext(os.path.basename(ncConfigs['windows']))[0]))
  nextcloud_configure_general("config:import /tmp/{0}".format(os.path.splitext(os.path.basename(ncConfigs['windows']))[0]))
  # workaround for getting imports ready sleep 5 secs
  time.sleep(5)
  nextcloud_configure_general("ldap:set-config s01 ldapAgentPassword {0}".format(LdapPassword))
#if PaedML == 'linux':
  # not finished yet
  #ncConfig = nextcloud_get_config(ncConfigs['linux'])
  #ncConfig['apps']['user_ldap']['s01ldap_dn'] = "CN={0},OU=_ServiceAccounts,DC=musterschule,DC=schule,DC=paedml".format(LdapUser)
  #ncConfig['apps']['user_ldap']['s01ldap_agent_password'] = "{0}".format(LdapPassword)
  #nextcloud_write_config(ncConfig, "{0}/{1}".format(currentDir,ncConfigs['windows']))
  #container_copy_file("{0}/{1}".format(currentDir,ncConfigs['windows']),ncContainerName + "{0}:/tmp/".format(ncConfigs['windows']))
  #nextcloud_configure_general("config:import /tmp/{0}".format(ncConfigs['windows']))
print("erledigt!")
time.sleep(5)


# Teacher Shares
print("Beginne mit dem einrichten der Lehrer Shares.....", end="")
# indexed file 0 - 2
teacherShares = nextcloud_get_config(ncConfigShareTeacher[PaedML])
if PaedML == 'windows':
  teacherShares[1]['configuration']['root'] = '/Tausch/{0}'.format(SchoolTypeShort)
  teacherShares[2]['configuration']['root'] = '/Benutzer/Schueler/{0}'.format(SchoolTypeShort)
  nextcloud_write_config(teacherShares, "{0}/{1}".format(currentDir,os.path.splitext(os.path.basename(ncConfigShareTeacher['windows']))[0]))
  container_copy_file("{0}/{1}".format(currentDir,os.path.splitext(os.path.basename(ncConfigShareTeacher['windows']))[0]),"{0}:/tmp/{1}".format(ncContainerName,os.path.splitext(os.path.basename(ncConfigs['windows']))[0]))
  nextcloud_configure_general("files_external:import /tmp/{0}".format(os.path.splitext(ncConfigShareTeacher['windows'])[0]))
#if PaedML == 'linux':
  # not finished yet
  #teacherShares[1]['configuration']['root'] = '\/Tausch\/{0}'.format(SchoolTypeShort)
  #teacherShares[2]['configuration']['root'] = 'Benutzer\/Schueler\/{0}'.format(SchoolTypeShort)
  #nextcloud_configure_general("files_external:import < {0}".format(teacherShares))
print("erledigt!")
time.sleep(5)


# Pupil Shares
print("Beginne mit dem einrichten der Schüler Shares.....", end="")
pupilShares = nextcloud_get_config(ncConfigSharePupil[PaedML])
if PaedML == "windows":
  pupilShares[1]['configuration']['root'] = '/Tausch/{0}/Klassen'.format(SchoolTypeShort)
  nextcloud_write_config(pupilShares, "{0}/{1}".format(currentDir,os.path.splitext(os.path.basename(ncConfigSharePupil['windows']))[0]))
  container_copy_file("{0}/{1}".format(currentDir,os.path.splitext(os.path.basename(ncConfigSharePupil['windows']))[0]),"{0}:/tmp/{1}".format(ncContainerName,os.path.splitext(os.path.basename(ncConfigs['windows']))[0]))                                                    
  nextcloud_configure_general("files_external:import /tmp/{0}".format(os.path.splitext(ncConfigSharePupil['windows'])[0]))
#todo paedml Linux
print("erledigt!")
time.sleep(5)


# Enable Client
print("Aktiviere Nextcloud Client Option...", end="")
nextcloud_configure_general('config:system:set overwriteprotocol --value="https"')
print("erledigt!")
time.sleep(5)


# Deny share for pupils
print("Setze Schüler dürfen keine Dateien teilen....", end="")
nextcloud_configure_general('config:app:set core shareapi_exclude_groups --value yes')
nextcloud_configure_general('config:app:set core shareapi_exclude_groups_list --value G_Schueler')
print("erledigt!")
time.sleep(5)


# Deactivate autocompletition for users
print("Deaktiviere Autocompletition für Users....", end="")
nextcloud_configure_general('config:app:set core shareapi_allow_share_dialog_user_enumeration --value no')
print("erledigt!")
time.sleep(5)


# disable public uploads
print("Deaktiviere öffentliches Hochladen.....", end="")
nextcloud_configure_general('config:app:set core shareapi_allow_public_upload --value no')
print("erledigt!")
time.sleep(5)


# Set Region to DE
print("Setze Phone Region auf DE.....", end="")
nextcloud_configure_general('config:system:set default_phone_region --value=DE')
print("erledigt!")
time.sleep(5)


# Set Webupdater Disable
print("Setze Webupdater auf Disable.....", end="")
nextcloud_configure_general('config:system:set upgrade.disable-web --value=true')
print("erledigt!")
time.sleep(5)


# Set Default Login app (files), not dashboard
print("Setze Default App auf Files.....", end="")
nextcloud_configure_general('config:system:set defaultapp --value=files')
print("erledigt!")
time.sleep(5)


# Disable knowlegde base
print("Deaktiviere Knowlegdebase.....", end="")
nextcloud_configure_general('config:system:set knowlegdebaseenabled --value=false')
print("erledigt!")
time.sleep(5)


# Install collabora plugin if needed
if CollaboraEnable:
    print("Aktiviere Richdocuments Plugin(Collabora).....", end="")
    nextcloud_configure_general('app:install richdocuments')
    print("erledigt!")
    time.sleep(10)
    print("Personalisiere Collabora Plugin.....", end="")
    nextcloud_configure_general('config:app:set richdocuments wopi_url --value=https:\/\/{0}'.format(CollaboraUrl))
    print("erledigt!")
    time.sleep(5)
    #nextcloud_configure_general('config:richdocuments:activate-config')
    #time.sleep(3)

# Disable profile modification for user-name
print("Deaktiviere das Erlauben zum Ändern des eigenen Profiles.....", end="")
nextcloud_configure_general('config:system:set allow_user_to_change_display_name --value=false')
print("erledigt!")
time.sleep(5)

# Disable special apps
print("Deaktiviere folgende apps: weather, announces, firstrun, federation, survey.....", end="")
nextcloud_configure_general('app:disable weather_status updatenotification firstrunwizard federation nextcloud_announcements survey_client')
print("erledigt!")
time.sleep(5)

## todo
# Limit special Apps to special groups

print("Setup ist durchgelaufen, bitte auf folgende Seite prüfen: https://{0}".format(HostProps['VIRTUAL_HOST']))
print("-------------")


#nextcloud_configure_ldap(l)
