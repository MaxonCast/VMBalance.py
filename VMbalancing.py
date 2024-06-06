from getpass import getpass
from pyVim.connect import SmartConnect  # , Disconnect
from pyVmomi import vim, vmodl


# hostname = getpass(prompt="Hostname : ")
# username = getpass(prompt="Username : ")
# password = getpass(prompt="Password : ")


# Connecting to VCenter
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
    return content


# Getting VM list
def getVM(content):
    container = content.rootFolder
    obj_type = [vim.VirtualMachine]
    container_view = content.viewManager.CreateContainerView(container, obj_type, recursive=True)
    vm_list = container_view.view
    return vm_list


# Test getting properties
def getProps(content):
    vm_properties = ["name", "config.uuid"]
    collector = content.propertyCollector
    container = content.rootFolder
    container_view = content.viewManager.CreateContainerView(container, [vim.VirtualMachine], recursive=True)
    obj_spec = vmodl.query.PropertyCollector.ObjectSpec()
    obj_spec.obj = container_view
    obj_spec.skip = True
    traversal_spec = vmodl.query.PropertyCollector.TraversalSpec()
    traversal_spec.name = 'traverseEntities'
    traversal_spec.path = 'view'
    traversal_spec.skip = False
    traversal_spec.type = container_view.__class__
    obj_spec.selectSet = [traversal_spec]
    property_spec = vmodl.query.PropertyCollector.PropertySpec()
    property_spec.type = vim.VirtualMachine
    property_spec.pathSet = vm_properties
    filter_spec = vmodl.query.PropertyCollector.FilterSpec()
    filter_spec.objectSet = [obj_spec]
    filter_spec.propSet = [property_spec]
    props = collector.RetrieveContents([filter_spec])
    data = []
    for obj in props:
        properties = {}
        for prop in obj.propSet:
            properties[prop.name] = prop.val
        properties['obj'] = obj.obj
        data.append(properties)
    return data


# Test getting performances
def get_perf(content, vm):
    perf_manager = content.perfManager
    counter_info = {}
    for counter in perf_manager.perfCounter:
        full_name = counter.groupInfo.key + "." + \
                    counter.nameInfo.key + "." + counter.rollupType
        counter_info[full_name] = counter.key
    counter_ids = [m.counterId for m in perf_manager.QueryAvailablePerfMetric(entity=vm)]
    metric_ids = [vim.PerformanceManager.MetricId(
        counterId=counter, instance="*") for counter in counter_ids]
    spec = vim.PerformanceManager.QuerySpec(maxSample=1, entity=vm, metricId=metric_ids)
    result_stats = perf_manager.QueryStats(querySpec=[spec])
    output = ""
    for _ in result_stats:
        output += "name:        " + vm.summary.config.name + "\n"
        for val in result_stats[0].value:
            counterinfo_k_to_v = list(counter_info.keys())[
                list(counter_info.values()).index(val.id.counterId)]

            if val.id.instance == '':
                output += "%s: %s\n" % (
                    counterinfo_k_to_v, str(val.value[0]))
            else:
                output += "%s (%s): %s\n" % (
                    counterinfo_k_to_v, val.id.instance, str(val.value[0]))
        return output


# Authentication to VSphere
vcenter = authVSphere()

# Getting list of all VMs
VM_List = getVM(vcenter)

# Getting properties of all VMs
prop_test = getProps(vcenter)
# Getting performance for 1 VM
perf_test = get_perf(vcenter, VM_List[37])

# Printing the name, props and perf of 1 VM
print("VM : ", VM_List[37])
print(prop_test[37])
print("------ RESULTS ------")
print(perf_test)


# Disconnect(service_instance)
