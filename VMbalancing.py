import datetime
from getpass import getpass
from pyVim.connect import SmartConnect  # , Disconnect
from pyVmomi import vim, vmodl
from pulp import LpMinimize, LpProblem, LpVariable, lpSum, value


# Connecting to VCenter
def authVSphere():
    content = "nothing"
    # Trying to connect to VCenter
    service_instance = SmartConnect(host=input("Hostname : "), user=input("Username : "),
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


# Getting VM list
def get_host(content):
    container = content.rootFolder
    obj_type = [vim.HostSystem]
    container_view = content.viewManager.CreateContainerView(container, obj_type, recursive=True)
    return container_view


# Getting properties
def get_props(content, container_view):
    # List of properties
    host_properties = ["name", "vm"]
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
    property_spec.type = vim.HostSystem
    property_spec.pathSet = host_properties
    # filter_spec setup
    filter_spec = vmodl.query.PropertyCollector.FilterSpec()
    filter_spec.objectSet = [obj_spec]
    filter_spec.propSet = [property_spec]
    # props & data setup
    props = content.propertyCollector.RetrieveContents([filter_spec])
    data = []
    for obj in props:
        properties = {}
        vm_list = []
        for vm in obj.propSet[1].val:
            vm_list.append(vm.config.name)
        if len(vm_list) > 0:
            properties['name'] = obj.obj.name
            properties['vm_list'] = vm_list
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
                counter_info_k_to_v = list(counter_info.keys())[list(counter_info.values()).index(val.id.counterId)]
                output += "%s: %s\n" % (counter_info_k_to_v, str(val.value[0]))
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
    for temp1 in range(len(data) - 1):
        for temp2 in range(temp1 + 1, len(data)):
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
def sort_by_abc(data):
    for temp1 in range(len(data) - 1):
        for temp2 in range(temp1 + 1, len(data)):
            if len(data[temp1]) > 1 and len(data[temp2]) > 1:
                if data[temp1][0].upper() > data[temp2][0].upper():
                    temp = data[temp1]
                    data[temp1] = data[temp2]
                    data[temp2] = temp
    return data


# Filter powered OFF VMs
def vm_power_filter(vm_list):
    new_list = []
    for vm in vm_list:
        if vm.summary.runtime.powerState == "poweredOn":
            new_list.append(vm)
    return new_list


# Calculate differences to print a result
def valid_test(data):
    # CPU test
    cpu_group1 = data["group1_cpu"]
    cpu_group2 = data["group2_cpu"]
    cpu_percent = (cpu_group1 + cpu_group2) / 50
    if -cpu_percent < cpu_group1 - cpu_group2 < cpu_percent:
        cpu = "Good"
    else:
        cpu = "BAD !"
    # MEMORY test
    mem_group1 = data["group1_mem"]
    mem_group2 = data["group2_mem"]
    mem_percent = (mem_group1 + mem_group2) / 20
    if -mem_percent <= mem_group1 - mem_group2 < mem_percent:
        mem = "Good"
    else:
        mem = "BAD !"
    # Printing results
    print("CPU Result :", cpu, "\nMemory Result :", mem)
    if cpu == "BAD !" or mem == "BAD !":
        print("I do not recommend moving VMs now !")


# Testing a VM name that can't be moved ("test = True" if VM is in the good group)
def test_protection(name, list1, list2, host_list):
    test = False
    name = name.upper()
    if name in host_list[0]['vm_list']:
        for vm in list1:
            vm[0] = vm[0].upper()
            if name == vm[0]:
                test = True
    elif name in host_list[1]['vm_list']:
        for vm in list2:
            vm[0] = vm[0].upper()
            if name == vm[0]:
                test = True
    return test


# Print list line by line
def print_list(plist):
    for p in plist:
        print(p)


# ----------------------------


# Pulp function
def pulp_search(vms, cpu, mem):
    vm_number = len(vms)
    # x[i] = 1 if vm goes in A Group and 0 if B Group
    x = LpVariable.dicts('x', range(vm_number), cat='Binary')
    # Max differences
    cpu_diff = LpVariable('cpu_diff', lowBound=0)
    mem_diff = LpVariable('mem_diff', lowBound=0)
    # Model
    model = LpProblem("Balancing_Servers", LpMinimize)
    # Sum of CPU usage and Mem consumed for each group
    # (cpu*100.000 to compensate difference between cpu numbers ~1.000 and mem numbers ~1.000.000)
    cpu_a = 10 ** 5 * lpSum([cpu[i] * x[i] for i in range(vm_number)])
    cpu_b = 10 ** 5 * lpSum([cpu[i] * (1 - x[i]) for i in range(vm_number)])
    mem_a = lpSum([mem[i] * x[i] for i in range(vm_number)])
    mem_b = lpSum([mem[i] * (1 - x[i]) for i in range(vm_number)])
    # Constrain differences
    model += cpu_diff >= cpu_a - cpu_b
    model += cpu_diff >= cpu_b - cpu_a
    model += mem_diff >= mem_a - mem_b
    model += mem_diff >= mem_b - mem_a
    # We try to minimize the differences between groups
    model += cpu_diff + mem_diff
    # Solving
    model.solve()
    print("RESEARCH FINISHED\n")
    group_a = [[vms[i], [cpu[i], mem[i]]] for i in range(vm_number) if value(x[i]) == 1]
    group_b = [[vms[i], [cpu[i], mem[i]]] for i in range(vm_number) if value(x[i]) == 0]
    # Sum of CPU usage and Mem consumed for each group
    cpu_a_value = sum([cpu[i] for i in range(vm_number) if value(x[i]) == 1])
    memoire_a_value = sum([mem[i] for i in range(vm_number) if value(x[i]) == 1])
    cpu_b_value = sum([cpu[i] for i in range(vm_number) if value(x[i]) == 0])
    memoire_b_value = sum([mem[i] for i in range(vm_number) if value(x[i]) == 0])
    result = [group_a, group_b, [cpu_a_value, memoire_a_value], [cpu_b_value, memoire_b_value]]
    return result


# ----------------------------


def main(content):
    # Get Host Properties
    host_props = get_props(content, get_host(content))

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

        # Sorting the VMs and data in lists
        vms1, vms2 = [], []
        cpu1, cpu2 = [], []
        mem1, mem2 = [], []
        for index in range(len(vm_list_cpu)):
            if index < len(vm_list_cpu)/2:
                vms1.append(vm_list_cpu[index][0])
                cpu1.append(vm_list_cpu[index][1][0])
                mem1.append(vm_list_cpu[index][1][1])
            else:
                vms2.append(vm_list_cpu[index][0])
                cpu2.append(vm_list_cpu[index][1][0])
                mem2.append(vm_list_cpu[index][1][1])
        group1 = [vms1, cpu1, mem1]
        group2 = [vms2, cpu2, mem2]

        # Researching best groups using Pulp
        print("\n------ RESEARCH PULP 1 ------\n")
        pulp1 = pulp_search(group1[0], group1[1], group1[2])
        print("\n------ RESEARCH PULP 2 ------\n")
        pulp2 = pulp_search(group2[0], group2[1], group2[2])
        # Organizing results
        pulp_groups = [pulp1[0], pulp1[1], pulp2[0], pulp2[1]]
        pulp_cpu = [pulp1[2][0], pulp1[3][0], pulp2[2][0], pulp2[3][0]]
        pulp_mem = [pulp1[2][1], pulp1[3][1], pulp2[2][1], pulp2[3][1]]
        # Calculating and sorting good lists using pulp
        print("\n------ RESEARCH PULP FINAL ------\n")
        final_pulp = pulp_search(pulp_groups, pulp_cpu, pulp_mem)
        temp1 = final_pulp[0][0][0] + final_pulp[0][1][0]
        temp2 = final_pulp[1][0][0] + final_pulp[1][1][0]

        vm_exclude = input("Which VM do you want to protect from moving ? "
                           "(only one VM can be chosen, press ENTER to skip) : ")

        # Way to protect 1 VM from being moved
        if vm_exclude != "" and vm_exclude != " " and not test_protection(vm_exclude, temp1, temp2, host_props):
            # VM groups
            temp = final_pulp[0]
            final_pulp[0] = final_pulp[1]
            final_pulp[1] = temp
            # Totals
            temp = final_pulp[2]
            final_pulp[2] = final_pulp[3]
            final_pulp[3] = temp

        # Grouping final results together
        final1 = sort_by_abc(final_pulp[0][0][0] + final_pulp[0][1][0])
        final2 = sort_by_abc(final_pulp[1][0][0] + final_pulp[1][1][0])
        cpu_sum1 = final_pulp[2][0]
        cpu_sum2 = final_pulp[3][0]
        mem_sum1 = final_pulp[2][1]
        mem_sum2 = final_pulp[3][1]
        cpu_mem = {"group1_cpu": cpu_sum1, "group1_mem": mem_sum1, "group2_cpu": cpu_sum2, "group2_mem": mem_sum2}

        # Printing results
        print("\n------ FINAL RESULTS ------\n")
        print("\n------", host_props[0]['name'], "------")
        print_list(final1)
        print("\n------", host_props[1]['name'], "------")
        print_list(final2)
        print("\nData Summary :")
        print("CPU Usage / Memory Consumed for", host_props[0]['name'], ":", cpu_sum1 / 1000, "GHz /",
              mem_sum1 / 1000000, "Go")
        print("CPU Usage / Memory Consumed for", host_props[1]['name'], ":", cpu_sum2 / 1000, "GHz /",
              mem_sum2 / 1000000, "Go")

        # Verification and Validation
        valid_test(cpu_mem)

        # Printing easy to read instructions
        print("\n------ WHO'S MOVING ? ------\n")
        print("------", host_props[0]['name'], "--->", host_props[1]['name'], "------\n")
        for vm1 in final2:
            for vm2 in host_props[0]['vm_list']:
                if vm1[0] == vm2:
                    print(vm2)
        print("\n------", host_props[1]['name'], "--->", host_props[0]['name'], "------\n")
        for vm1 in final1:
            for vm2 in host_props[1]['vm_list']:
                if vm1[0] == vm2:
                    print(vm2)

    else:
        print("Not enough data to create 2 groups.")


# Authentication to VSphere
vcenter = authVSphere()
print("\n")

# Main Program
main(vcenter)

print("\nEnd")

# Disconnect(service_instance)
