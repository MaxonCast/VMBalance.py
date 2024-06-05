from getpass import getpass
from pyVim.connect import SmartConnect  # , Disconnect
from pyVmomi import vim


# hostname = getpass(prompt="Hostname : ")
# username = getpass(prompt="Username : ")
# password = getpass(prompt="Password : ")


# Connecting to VCenter
def authVSphere():
    result = "vide"
    service_instance = SmartConnect(host=getpass(prompt="Hostname : "), user=getpass(prompt="Username : "),
                                    pwd=getpass(prompt="Password : "))
    if not service_instance:
        raise Exception("Failed to connect to vCenter Server")

    try:
        result = service_instance.RetrieveContent()
    except Exception as e:
        print("Error: {}".format(str(e)))
    return result


content = authVSphere()
print("------ RESULTS ------")
print(content)


# Getting VM list
def getVM(vcenter):
    container = vcenter.rootFolder
    view_type = [vim.VirtualMachine]
    recursive = True
    container_view = vcenter.viewManager.CreateContainerView(container, view_type, recursive)
    children = container_view.view
    return children


VM_List = getVM(content)
print("------ VM LIST ------")
for VM in VM_List:
    print(VM, vim.VirtualMachine.summary.guestFullName)

# Disconnect(service_instance)
