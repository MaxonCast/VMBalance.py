import datetime
from getpass import getpass
from pyVim.connect import SmartConnect  # , Disconnect
from pyVmomi import vim, vmodl
from pulp import LpMinimize, LpProblem, LpVariable, lpSum, value, LpStatus


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
    cpu_percent = (cpu_group1 + cpu_group2) / 20
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


# Print list line by line
def print_list(plist):
    for p in plist:
        print(p)


# ----------------------------


# Forming the lists in order to use pulp
def sorting_pulp_groups(pulp_groups, pulp_data):
    groups = [[], []]
    # Comparing CPU data in the first 2 groups
    if pulp_data["group1"][0] < pulp_data["group2"][0]:
        # Comparing CPU data in the second 2 groups
        if pulp_data["group3"][0] < pulp_data["group4"][0]:
            groups[0] = pulp_groups["group1"] + pulp_groups["group4"]
            groups[1] = pulp_groups["group2"] + pulp_groups["group3"]
        elif pulp_data["group3"][0] > pulp_data["group4"][0]:
            groups[0] = pulp_groups["group1"] + pulp_groups["group3"]
            groups[1] = pulp_groups["group2"] + pulp_groups["group4"]

        # No issue with CPU
        else:
            # Comparing Memory data in the first 2 groups
            if pulp_data["group1"][1] < pulp_data["group2"][1]:
                # Comparing Memory data in the second 2 groups
                if pulp_data["group3"][1] < pulp_data["group4"][1]:
                    groups[0] = pulp_groups["group1"] + pulp_groups["group4"]
                    groups[1] = pulp_groups["group2"] + pulp_groups["group3"]
                else:
                    groups[0] = pulp_groups["group1"] + pulp_groups["group3"]
                    groups[1] = pulp_groups["group2"] + pulp_groups["group4"]

            # Comparing Memory data in the first 2 groups
            elif pulp_data["group1"][1] > pulp_data["group2"][1]:
                # Comparing Memory data in the second 2 groups
                if pulp_data["group3"][1] < pulp_data["group4"][1]:
                    groups[0] = pulp_groups["group1"] + pulp_groups["group3"]
                    groups[1] = pulp_groups["group2"] + pulp_groups["group4"]
                else:
                    groups[0] = pulp_groups["group1"] + pulp_groups["group4"]
                    groups[1] = pulp_groups["group2"] + pulp_groups["group3"]

    # Comparing CPU data in the first 2 groups
    elif pulp_data["group1"][0] > pulp_data["group2"][0]:
        # Comparing CPU data in the second 2 groups
        if pulp_data["group3"][0] < pulp_data["group4"][0]:
            groups[0] = pulp_groups["group1"] + pulp_groups["group3"]
            groups[1] = pulp_groups["group2"] + pulp_groups["group4"]
        elif pulp_data["group3"][0] > pulp_data["group4"][0]:
            groups[0] = pulp_groups["group1"] + pulp_groups["group4"]
            groups[1] = pulp_groups["group2"] + pulp_groups["group3"]

        # No issue with CPU
        else:
            # Comparing Memory data in the first 2 groups
            if pulp_data["group1"][1] < pulp_data["group2"][1]:
                # Comparing Memory data in the second 2 groups
                if pulp_data["group3"][1] < pulp_data["group4"][1]:
                    groups[0] = pulp_groups["group1"] + pulp_groups["group4"]
                    groups[1] = pulp_groups["group2"] + pulp_groups["group3"]
                else:
                    groups[0] = pulp_groups["group1"] + pulp_groups["group3"]
                    groups[1] = pulp_groups["group2"] + pulp_groups["group4"]

            # Comparing Memory data in the first 2 groups
            elif pulp_data["group1"][1] > pulp_data["group2"][1]:
                # Comparing Memory data in the second 2 groups
                if pulp_data["group3"][1] < pulp_data["group4"][1]:
                    groups[0] = pulp_groups["group1"] + pulp_groups["group3"]
                    groups[1] = pulp_groups["group2"] + pulp_groups["group4"]
                else:
                    groups[0] = pulp_groups["group1"] + pulp_groups["group4"]
                    groups[1] = pulp_groups["group2"] + pulp_groups["group3"]

    # No issue with CPU
    else:
        # Comparing Memory data
        if pulp_data["group1"][1] < pulp_data["group2"][1]:
            if pulp_data["group3"][1] < pulp_data["group4"][1]:
                groups[0] = pulp_groups["group1"] + pulp_groups["group4"]
                groups[1] = pulp_groups["group2"] + pulp_groups["group3"]
            else:
                groups[0] = pulp_groups["group1"] + pulp_groups["group3"]
                groups[1] = pulp_groups["group2"] + pulp_groups["group4"]
        elif pulp_data["group1"][1] > pulp_data["group2"][1]:
            if pulp_data["group3"][1] < pulp_data["group4"][1]:
                groups[0] = pulp_groups["group1"] + pulp_groups["group3"]
                groups[1] = pulp_groups["group2"] + pulp_groups["group4"]
            else:
                groups[0] = pulp_groups["group1"] + pulp_groups["group4"]
                groups[1] = pulp_groups["group2"] + pulp_groups["group3"]
    return groups


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
    cpu_a = lpSum([cpu[i] * x[i] for i in range(vm_number)])
    cpu_b = lpSum([cpu[i] * (1 - x[i]) for i in range(vm_number)])
    mem_a = lpSum([mem[i] * x[i] for i in range(vm_number)])
    mem_b = lpSum([mem[i] * (1 - x[i]) for i in range(vm_number)])
    # Constrain differences
    model += cpu_diff >= cpu_a - cpu_b
    model += cpu_diff >= cpu_b - cpu_a
    model += mem_diff >= mem_a - mem_b
    model += mem_diff >= mem_b - mem_a
    # We try to minimize the differences between groups
    # (cpu*100.000 to compensate difference between cpu numbers ~1.000 and mem numbers ~1.000.000)
    model += 10 ** 5 * cpu_diff + mem_diff
    # Solving
    model.solve()
    group_a = [[vms[i], [cpu[i], mem[i]]] for i in range(vm_number) if value(x[i]) == 1]
    group_b = [[vms[i], [cpu[i], mem[i]]] for i in range(vm_number) if value(x[i]) == 0]
    # Sum of CPU usage and Mem consumed for each group
    cpu_a_value = sum([cpu[i] for i in range(vm_number) if value(x[i]) == 1])
    memoire_a_value = sum([mem[i] for i in range(vm_number) if value(x[i]) == 1])
    cpu_b_value = sum([cpu[i] for i in range(vm_number) if value(x[i]) == 0])
    memoire_b_value = sum([mem[i] for i in range(vm_number) if value(x[i]) == 0])
    if LpStatus[model.status] != "Optimal":
        print("Status:", LpStatus[model.status])
    result = [group_a, group_b, [cpu_a_value, memoire_a_value], [cpu_b_value, memoire_b_value]]
    return result


# ----------------------------


# Getting VM and their performances then distributing them in 2 balanced lists
def main(content):
    # Getting Host
    # Host Properties
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
            if index % 2 == 0:
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
        print("RESEARCH FINISHED\n")
        print("\n------ RESEARCH PULP 2 ------\n")
        pulp2 = pulp_search(group2[0], group2[1], group2[2])
        print("RESEARCH FINISHED\n")
        # Organizing results
        pulp_groups = {"group1": pulp1[0], "group2": pulp1[1], "group3": pulp2[0], "group4": pulp2[1]}
        pulp_data = {"group1": pulp1[2], "group2": pulp1[3], "group3": pulp2[2], "group4": pulp2[3]}

        # Calculating and sorting good lists using pulp
        results = sorting_pulp_groups(pulp_groups, pulp_data)
        final1 = sort_by_abc(results[0])
        final2 = sort_by_abc(results[1])

        # Calculating sum of CPU and Mem for each group
        cpu_sum1 = sum(i[1][0] for i in final1)
        cpu_sum2 = sum(i[1][0] for i in final2)
        mem_sum1 = sum(i[1][1] for i in final1)
        mem_sum2 = sum(i[1][1] for i in final2)
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
        print("------", host_props[1]['name'], "--->", host_props[0]['name'], "------\n")
        for vm1 in final1:
            for vm2 in host_props[1]['vm_list']:
                if vm1[0] == vm2:
                    print(vm2)
        print("\n------", host_props[0]['name'], "--->", host_props[1]['name'], "------\n")
        for vm1 in final1:
            for vm2 in host_props[0]['vm_list']:
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
