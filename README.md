#  MIB File Parser / OID Data extractor -> DB loader.

The below is a utility load MIB based information into a simple table structure to enable the user to join the MIB detail with the values extracted via the SNMP Source connector from the SNMP Agents.


This project/utility is part of a larger set of projects/blogs, see:

- [A Proposal to uitlize Modern Realtime Datastreaming Technologies to Manage Data centre's resources](https://github.com/georgelza/DataPipeline-SNMP_Flink_Fluss)
  
- [Apache Flink SNMP Source Connector](https://github.com/georgelza/SNMP-Flink-Source-connector.git) and


When querying SNMP agents (using one of the below commands) what is returned is a set raw SNMP data. To decode/understand the data it is commonly joined with a MIB files, normally supplied by the vendor of the device.


### SNMPGET Example

- snmpget -v1 -c password 172.16.10.2 sysDescr.0

- snmpget -c passsword 172.16.10.24 HOST-RESOURCES-MIB::hrSystemUptime.0

`HOST-RESOURCES-MIB::hrSystemUptime.0 = Timeticks: (41519049) 4 days, 19:19:50.49`


- snmpget -v1 -c passsword 172.16.10.24 sysDescr.0

`SNMPv2-MIB::sysDescr.0 = STRING: TrueNAS-25.04.1. Hardware: x86_64 Intel(R) Core(TM) i5-7400 CPU @ 3.00GHz. Software: Linux 6.12.15-production+truenas (revision #1 SMP PREEMPT_DYNAMIC Mon May 26 13:44:31 UTC 2025)`


### SNMPWALK Example

- snmpwalk -v1 -c passsword <Agent IP> 1.3.6.1.2.1


This utility will read the mib file and extract the oid value and it's associated detail into a data packet as per below, which can then be inserted into a database, these records can then be joined with the above returned data for deeper insight/understanding of the snmpget or snmpwalk data returned. Take Note: normally one mib file will reference/import additional dependency mib files. When you execute the program and the compile fails it will reference the missing MIB files. See the MIBBrowser link in the reference to source dependency mib files.


Single oid and associated data extracted from MIB file

```note
oid:             1.3.6.1.4.1.12345.1.1.1
object_name:     myObjectName
info:            This is the description of the object
type:            Integer32
oid_type:        scalar
module:          MY-MIB
```

As can be seen, it's a Python program based primarily on [pysnmp](https://github.com/pysnmp/pysnmp) python module.

The module itself internally uses/references common industry standard compiled MIB's. These are packaged as python files... They can be located in the `pysnmp-mibs` folder, and ye I hard coded this location into the program.


## Prepare Python environment

1. python3 -m venv ./venv

2. source venv/bin/activate

3. pip install --upgrade pip    

4. pip install -r requirements

5. Please Pre create the target table in your desired database. see: `TableExamples` directory for relevant PostgreSQL and Mysql scripts.
 
6. You can now run one of the run*.sh scripts of choice, see `mib_parser.py` header for more detail about the various input arguments.



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
