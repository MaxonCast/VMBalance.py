import requests
from requests.auth import HTTPBasicAuth
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning

hostname = "https://mwa"
username = "mwa"
password = "mdp"

VMlist = []

print (username,password)

def auth_vcenter(user,userpass):
	resp = requests.post('{}/com/vmware/cis/session'.format(api_url),auth=(username, password),verify=False)
	if resp.status_code != 200:
		print('Error {}'.format(resp.status_code))
		return
	return resp.json()['value']
