import requests
from requests.auth import HTTPBasicAuth
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning

hostname = "ici"
username = "mwa"
password = "no"

VMlist = []

print (username)

def auth_vcenter(user,userpass):
	resp = requests.post('https://{}/api/session',auth=(username, password))
	if resp.ok:
		sessionID = response.json()
		print(sessionID)
	else:
		print("Erreur")
#	if resp.status_code != 200:
#		print('Error {}'.format(resp.status_code))
#		return
#	return resp.json()['value']

auth_vcenter("moi","moi")
