 --> Alternative of VMWare DRS

Using pyVmomi and Pulp to balance VMs between 2 servers in VMWare (CPU usage and Memory consumed)

! Only work with 2 servers and 2 groups !


------ DESCRIPTION OF CODE ------

First, we connect to the VCenter, loging in with server address, login and password.

Then we use pyVmomi to get hosts information (like VxRail) and virtual machines list.
With the function "vm_power_filter", I remove powered off machines from the list.
(I didn't try disabling this function with this version of the program, you can certainly try, it should work regardless)

The next step is to get VM performances for each VM and sorting them by CPU usage.

---

Note :
Because I'm working with 50 VMs or so, I'm splitting VMs in 2 groups before sorting them. It reduces drastically the time needed to calculate groups.
 - If you're working with fewer VMs, you can try skipping this part (you also need to modify the rest of the code after that)
 - If you're working with more, you may need to make more groups (you also probably need to modify the code after this step)

---

Using Pulp, we sort each group formed in 2 balanced groups.
(If you got fewer VMs you can form the final groups directly, if you got more you may need to sort more than 2 groups at this step)
Once the balanced groups are formed, we are using Pulp again to form groups of the balanced groups (can be done manually).

Finally, we can print the results :
We print the final list for each of the 2 groups and the final performance total. (CPU usage in GHz and Memory consumed in Go)
I also print a Good or Bad summary for CPU usage and Memory consumed differences between the 2 groups.
It will print Good for CPU usage if there is less than 2% of difference, and 5% for Memory consumed.

After that, I print for each server which VMs need to switch side. 
It can be done automatically of course with pyVmomi, but this program isn't doing that. It shouldn't be too hard to had it though. 


------

Final words :

I worked on this for 4 weeks now, during my internship.
It was a good experience for me in terms of programming, but my program isn't perfect at all.

I will probably stop developing it soon, feel free to improve it if needed. 
