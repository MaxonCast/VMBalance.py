from getpass import getpass

import requests

hostname = input("hostname : ")
username = input("username : ")
password = getpass(prompt="password : ")

print("------------")

# GET THE TOKEN
# curl -k -X POST https://vcenter/rest/com/vmware/cis/session -u username:password
def authVsphere():
	response = requests.post('https://{}/api/session'.format(hostname), verify=False, auth=(username,password))
	sessionID = False
	if response.ok:
		sessionID = response.json()
		print("------ GOT SessionID ------")
	else:
		print("Erreur POST")
	return sessionID

# GET VM
# curl -X GET 'https://vcenter/api/vcenter/vm' -H 'vmware-api-session-id: <ID>'
def getAllVM(token):
	VM = False
	headers = {
		'vmware-api-session-id': token,
	}
	response = requests.get('https://{}/api/vcenter/vm'.format(hostname), verify=False, headers=headers)
	if response.ok:
		VM = response.json()
		print("------ JSON VMs ------")
		print(VM)
	else:
		print("Erreur GET VM")
#	return VM

# GET HOSTS
# curl -X GET 'https://vcenter/api/vcenter/vm' -H 'vmware-api-session-id: <ID>'
def getAllHosts(token):
	host = False
	headers = {
		'vmware-api-session-id': token,
	}
	response = requests.get('https://{}/api/vcenter/host'.format(hostname), verify=False, headers=headers)
	if response.ok:
		host = response.json()
		print("------ JSON HOSTS ------")
		print(host)
	else:
		print("Erreur GET Hosts")
#	return host

token = authVsphere()
print("------")
getAllVM(token)
print("------")
getAllHosts(token)
print("------")

# TEST
print("------ TESTS ------")

def metrics(token):
	headers = {
		'vmware-api-session-id': token,
	}
	response = requests.get('https://{}/api/stats/metrics'.format(hostname), verify=False, headers=headers)
	if response.ok:
		t = response.json()
		print("------ TEST ------")
		print(t)
	else:
		print("Erreur TEST")

metrics(token)
