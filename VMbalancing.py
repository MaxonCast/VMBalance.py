import datetime
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
def get_props(content, container_view):
    # List of properties
    vm_properties = ["name"]
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
def get_perf(content, obj_list):
    counter_info = counter_filter(content)
    data = []
    print("Calculating...")
    for obj in obj_list:
        counter_ids = []
        for m in content.perfManager.QueryAvailablePerfMetric(entity=obj):
            if m.counterId in list(counter_info.values()):
                counter_ids.append(m.counterId)
        metric_ids = [vim.PerformanceManager.MetricId(counterId=counter, instance="*") for counter in counter_ids]
        start_time = datetime.datetime.now() - datetime.timedelta(hours=1)
        end_time = datetime.datetime.now()
        spec = vim.PerformanceManager.QuerySpec(maxSample=1000, entity=obj, metricId=metric_ids, startTime=start_time,
                                                endTime=end_time)
        result_stats = content.perfManager.QueryStats(querySpec=[spec])
        output = ""
        vm_data = [obj.summary.config.name]
        value_data = []
        for _ in result_stats:
            output += "name:        " + obj.summary.config.name + "\n"
            for val in result_stats[0].value:
                value_data.append(val.value[0])
                counterinfo_k_to_v = list(counter_info.keys())[list(counter_info.values()).index(val.id.counterId)]
                output += "%s: %s\n" % (counterinfo_k_to_v, str(val.value[0]))
            vm_data.append(value_data)
        data.append(vm_data)
        # print(output, "\nVM", len(data), "saved !\n------------\n")
    print("Done !\n   ", len(data), "VM saved\n")
    return data


# Counter filter
def counter_filter(content):
    counter_info = {}
    for counter in content.perfManager.perfCounter:
        if (counter.groupInfo.key == "cpu" or counter.groupInfo.key == "mem") and counter.rollupType == "average":
            if counter.nameInfo.key == "consumed" or counter.nameInfo.key == "usagemhz":
                full_name = counter.groupInfo.key + "." + counter.nameInfo.key + "." + counter.rollupType
                counter_info[full_name] = counter.key
    return counter_info


# Sorting the VM List by CPU usage (highest to lowest)
def sort_by_cpu(data):
    for temp1 in range(len(data)-1):
        for temp2 in range(temp1+1, len(data)):
            if len(data[temp1]) > 1 and len(data[temp2]) > 1:
                if data[temp1][1][0] > data[temp2][1][0]:
                    temp = data[temp1]
                    data[temp1] = data[temp2]
                    data[temp2] = temp
    new_data = []
    for i in data:
        new_data = [i] + new_data
    return new_data


# Sorting the VM List by Memory consumed (highest to lowest)
def sort_by_mem(data):
    for temp1 in range(len(data)-1):
        for temp2 in range(temp1+1, len(data)):
            if len(data[temp1]) > 1 and len(data[temp2]) > 1:
                if data[temp1][1][1] > data[temp2][1][1]:
                    temp = data[temp1]
                    data[temp1] = data[temp2]
                    data[temp2] = temp
    new_data = []
    for i in data:
        new_data = [i] + new_data
    return new_data


# Filter powered OFF VMs
def vm_power_filter(vm_list):
    new_list = []
    for vm in vm_list:
        if vm.summary.runtime.powerState == "poweredOn":
            new_list.append(vm)
    return new_list


# Distributing ordered VM (cpu) into 2 Lists (trying to balance the 2)
def distribution_vm_cpu(vm_list, cpu_percent, mem_percent):
    list1, list2 = [], []
    sum1, sum2 = [0, 0], [0, 0]
    for index in range(len(vm_list)):
        vm = vm_list[index]
        # Initiation
        if len(list1) == 0:
            list1.append(vm)
            sum1[0] = vm[1][0]
            sum1[1] = vm[1][1]
        elif ((sum1[0] == sum2[0] or sum1[1]-sum2[1] > mem_percent or sum2[1]-sum1[1] > mem_percent)
              and vm[1][0] < cpu_percent / 10):
            if sum1[1] > sum2[1]:
                list2.append(vm)
                sum2[0] = sum2[0] + vm[1][0]
                sum2[1] = sum2[1] + vm[1][1]
            else:
                list1.append(vm)
                sum1[0] = sum1[0] + vm[1][0]
                sum1[1] = sum1[1] + vm[1][1]
        # Equilibrate CPU
        elif sum1[0] > sum2[0]:
            list2.append(vm)
            sum2[0] = sum2[0] + vm[1][0]
            sum2[1] = sum2[1] + vm[1][1]
        else:
            list1.append(vm)
            sum1[0] = sum1[0] + vm[1][0]
            sum1[1] = sum1[1] + vm[1][1]
    balanced_list = [list1, list2, sum1, sum2]
    return balanced_list


# Distributing ordered VM (cpu) into 2 Lists (trying to balance the 2)
def distribution_vm(vm_list):
    sorted_vm = sorted(vm_list, key=lambda x: (x[1][0], x[1][1]), reverse=True)
    print_list(sorted_vm)
    list1, list2 = [], []
    sum1, sum2 = [0, 0], [0, 0]
    for index in range(len(sorted_vm)):
        vm = sorted_vm[index]
    balanced_list = [list1, list2, sum1, sum2]
    return balanced_list


# Calculate differences to print a result
def valid_test(vm_list, cpu_percent, mem_percent):
    # CPU
    if -cpu_percent < vm_list[2][0]-vm_list[3][0] < cpu_percent:
        print("CPU Result : Good")
    else:
        print("CPU Result : BAD !")
    # MEMORY
    if -mem_percent <= vm_list[2][1]-vm_list[3][1] < mem_percent:
        print("Memory Result : Good")
    else:
        print("Memory Result : BAD !")


# Print list line by line
def print_list(plist):
    for p in plist:
        print(p)


# ----------------------------


# Getting VM and their performances then distributing them in 2 balanced lists
def main_vm(content):

    # Getting list of all VMs
    vm_view = getVM(content)
    vm_list = vm_view.view
    # Filtering the powered ON VMs (deleting powered OFF VMs of list)
    vm_list = vm_power_filter(vm_list)

    # Getting the perf of all VMs
    perf_data = get_perf(content, vm_list)

    if len(perf_data) > 1:

        # Sorting VM by CPU / Mem
        vm_list_cpu = sort_by_cpu(perf_data)

        all_cpu, all_mem = 0, 0
        for vm in vm_list_cpu:
            all_cpu = all_cpu + vm[1][0]
            all_mem = all_mem + vm[1][1]
        cpu_percent = all_cpu / 20
        mem_percent = all_mem / 20

        # Distributing VMs in 2 balanced lists
        vm_lists = distribution_vm_cpu(vm_list_cpu, cpu_percent, mem_percent)
        print("------ DISTRIBUTION BY CPU USAGE ------\n\nList 2 :")
        print_list(vm_lists[0])
        print("\nList 1 :")
        print_list(vm_lists[1])
        print("\nSummary :\nCPU / Memory list 1 :", vm_lists[2][0]/1000, "GHz /", vm_lists[2][1]/1000000, "Go",
              "\nCPU / Memory list 2 :", vm_lists[3][0]/1000, "GHz /", vm_lists[3][1]/1000000, "Go")
        valid_test(vm_lists, cpu_percent, mem_percent)

        # VM Properties
        print("\n------ VM PROPERTIES ------\n")
        vm_props = get_props(vcenter, vm_view)
        # print_list(vm_props)

        # distribution_vm(perf_data)

        return vm_lists

    else:

        print("Not enough data to create 2 groups.")
        return perf_data


# Authentication to VSphere
vcenter = authVSphere()
print("\n")

# VM program
vm_balanced = main_vm(vcenter)


# Disconnect(service_instance)
