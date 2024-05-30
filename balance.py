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
def authVcenter():
	response = requests.post('https://{}/rest/com/vmware/cis/session'.format(hostname), verify=False, auth=(username,password))
	sessionID = False
	if response.ok:
		sessionID = response.json()['value']
		print("------",sessionID,"------")
	else:
		print("Erreur POST")
	return sessionID

# GET VM
# curl -X GET 'https://vcsa7.hsc.loc/api/vcenter/vm' -H 'vmware-api-session-id: <ID>'
def getAllVM(token):
	VM = False
	headers = {
		'vmware-api-session-id': token,
	}
	response = requests.get('https://{}/api//vcenter/vm'.format(hostname), verify=False, headers=headers)
	if response.ok:
		VM = response.json()
		print("------ JSON VMs ------")
		print(VM)
	else:
		print("Erreur GET")

token = authVcenter()
print("------")
print(token)
print("------")
getAllVM(token)
