import requests
from requests.auth import HTTPBasicAuth
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import getpass

hostname = input("hostname : ")
username = input("username : ")
password = getpass.getpass("password : ")

VMlist = []

# GET THE TOKEN
# curl -k -X POST https://vcsa7.hsc.loc/rest/com/vmware/cis/session -u username:password
def auth_vcenter():
	response = requests.post('https://{}/rest/com/vmware/cis/session'.format(hostname), verify=False, auth=(username,password))
	if response.ok:
		sessionID = response.json()
		print("------",sessionID,"------")
	else:
		print("Erreur")

# GET VM
# curl -X GET 'https://vcsa7.hsc.loc/api/vcenter/vm' -H 'vmware-api-session-id: <ID>'

auth_vcenter()
