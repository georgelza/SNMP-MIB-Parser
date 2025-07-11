#  MIB Loader

The below is a program to load MIB information into a simple table structure to enable the user to join the MIB detail with the values extracted via the SNMP Source connector from the SNMP Agents.

As can be seen, it's a Python program based on [pysnmp](https://github.com/pysnmp/pysnmp) python module.


## Prepare Python environment

1. python3 -m venv ./venv

2. source venv/bin/activate

3. pip install --upgrade pip    

4. pip install -r requirements

5. run one of the run*.sh scripts of choice, see mib_parser.py header for example, execute via run_*.sh


```note
oid:             1.3.6.1.4.1.12345.1.1.1
object_name:     myObjectName
info:            This is the description of the object
type:            Integer32
oid_type:        scalar
module:          MY-MIB
```



### References

- [SNMP Protocol](https://en.wikipedia.org/wiki/Simple_Network_Management_Protocol)

- [Structure of Management Information (SMI) Numbers (MIB Module Registrations)](https://www.iana.org/assignments/smi-numbers/smi-numbers.xhtml)

- [Getting Started with SNMP](https://www.easysnmp.com/tutorial/getting-snmp-data/)

- [SNMP by Techtarget](https://www.techtarget.com/searchnetworking/definition/SNMP)

- [Good resource to download missing/dependency MIB files](https://mibbrowser.online/mibdb_search.php)

- [Lisa's Home Page: SNMP Simulator](https://www.rushworth.us/lisa/?p=11032)
 
- [Public SNMP Agent Simulator](http://snmplabs.com/snmpsim/public-snmp-agent-simulator.html)

- [Pysnmp](https://github.com/pysnmp)  & [PySNMP v7](https://docs.lextudio.com/snmp/) & [LexStudio GIT Repo](https://github.com/lextudio/mibs.pysnmp.com)

  - The above (`PySNMP v7`) includes some good history w.r.t SNMP.


### By:

George

[georgelza@gmail.com](georgelza@gmail.com)

[George on Linkedin](https://www.linkedin.com/in/george-leonard-945b502/)

[George on Medium](https://medium.com/@georgelza)
