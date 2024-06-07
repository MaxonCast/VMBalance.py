from getpass import getpass
from pyVim.connect import SmartConnect  # , Disconnect
from pyVmomi import vim, vmodl


# Connecting to VCenter
def authVSphere():
    content = "nothing"
    # Trying to connect to VCenter
    service_instance = SmartConnect(host=getpass(prompt="Hostname : "), user=getpass(prompt="Username : "),
                                    pwd=getpass(prompt="Password : "))
    # Connection verification
    if not service_instance:
        raise Exception("Failed to connect to vCenter Server")
    # Trying to get VCenter content
    try:
        content = service_instance.RetrieveContent()
    except Exception as e:
        print("Error: {}".format(str(e)))
    # Returning VCenter content or "nothing" if there is an error
    return content


# Getting VM list
def getVM(content):
    container = content.rootFolder
    obj_type = [vim.VirtualMachine]
    container_view = content.viewManager.CreateContainerView(container, obj_type, recursive=True)
    return container_view


# Getting properties
def getProps(content, container_view):
    # List of properties
    vm_properties = ["name", "config.uuid"]
    # Collector setup
#    collector = content.propertyCollector
    # obj_spec setup
    obj_spec = vmodl.query.PropertyCollector.ObjectSpec()
    obj_spec.obj = container_view
    obj_spec.skip = True
    # traversal_spec setup
    traversal_spec = vmodl.query.PropertyCollector.TraversalSpec()
    traversal_spec.name = 'traverseEntities'
    traversal_spec.path = 'view'
    traversal_spec.skip = False
    traversal_spec.type = container_view.__class__
    # obj_spec Set
    obj_spec.selectSet = [traversal_spec]
    # property_spec setup
    property_spec = vmodl.query.PropertyCollector.PropertySpec()
    property_spec.type = vim.VirtualMachine
    property_spec.pathSet = vm_properties
    # filter_spec setup
    filter_spec = vmodl.query.PropertyCollector.FilterSpec()
    filter_spec.objectSet = [obj_spec]
    filter_spec.propSet = [property_spec]
    # props & data setup
    props = content.propertyCollector.RetrieveContents([filter_spec])
    data = []
    #
    for obj in props:
        properties = {}
        for prop in obj.propSet:
            properties[prop.name] = prop.val
        properties['obj'] = obj.obj
        data.append(properties)
    return data


# Getting performances
def get_perf(content, vm_list):
    counter_info = counter_filter(content)
    for vm in vm_list:
        counter_ids = []
        for m in content.perfManager.QueryAvailablePerfMetric(entity=vm):
            if m.counterId in list(counter_info.values()):
                counter_ids.append(m.counterId)
        metric_ids = [vim.PerformanceManager.MetricId(
            counterId=counter, instance="*") for counter in counter_ids]
        spec = vim.PerformanceManager.QuerySpec(maxSample=1, entity=vm, metricId=metric_ids)
        result_stats = content.perfManager.QueryStats(querySpec=[spec])
        output = ""
        for _ in result_stats:
            output += "name:        " + vm.summary.config.name + "\n"
            for val in result_stats[0].value:
                counterinfo_k_to_v = list(counter_info.keys())[list(counter_info.values()).index(val.id.counterId)]
                if val.id.instance == '':
                    output += "%s: %s\n" % (
                        counterinfo_k_to_v, str(val.value[0]))
                else:
                    output += "%s (%s): %s\n" % (
                        counterinfo_k_to_v, val.id.instance, str(val.value[0]))
        print(output)
        print("------------\n")


# Counter filter
def counter_filter(content):
    counter_info = {}
    for counter in content.perfManager.perfCounter:
        if (counter.groupInfo.key == "cpu" or counter.groupInfo.key == "mem") and counter.rollupType == "average":
            if counter.nameInfo.key == "usage" or counter.nameInfo.key == "usagemhz" or counter.nameInfo.key == "ready":
                full_name = counter.groupInfo.key + "." + counter.nameInfo.key + "." + counter.rollupType
                counter_info[full_name] = counter.key
    return counter_info


# Authentication to VSphere
vcenter = authVSphere()
print("\n")

# Getting list of all VMs
VM_view = getVM(vcenter)
VM_List = VM_view.view

# Getting properties of all VMs
prop_test = getProps(vcenter, VM_view)

# Printing the perf of all VMs
print("------ RESULTS ------\n")
get_perf(vcenter, VM_List)


# Disconnect(service_instance)
