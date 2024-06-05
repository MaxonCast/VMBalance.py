from getpass import getpass
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim


# hostname = getpass(prompt="Hostname : ")
# username = getpass(prompt="Username : ")
# password = getpass(prompt="Password : ")


# Connection au VCenter
def authVSphere():
    content = "vide"
    service_instance = SmartConnect(host=getpass(prompt="Hostname : "), user=getpass(prompt="Username : "),
                                    pwd=getpass(prompt="Password : "))
    if not service_instance:
        raise Exception("Failed to connect to vCenter Server")

    try:
        content = service_instance.RetrieveContent()
    except Exception as e:
        print("Error: {}".format(str(e)))
    finally:
        # Disconnect from the vCenter server
        Disconnect(service_instance)
    return content


content = authVSphere()
print("------ RESULTS ------")
print(content)
