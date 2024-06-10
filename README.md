Alternative of VMWare DRS

Using pyVmomi to balance VMs between 2 servers in VMWare (CPU and Memory)


------ DESCRIPTION OF CODE ------

Function authVcenter :
  Authentication to VSphere and fetching content
  (return content)

Function getVM :
  Getting all VMs in VSphere using ContainerView
  (returns view)

Function getProps (TODO) :
  Getting properties for all VMs
  (return list of properties)
    -> recycling this function

Function get_perf (TODO) :
  Printing performance (filtered by counter_filter) for all VMs
    -> change it to return final values in a list to be used later

Function counter_filter :
  Filtering CPU usage and Memory usage