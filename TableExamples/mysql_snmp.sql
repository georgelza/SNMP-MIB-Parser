
CREATE DATABASE IF NOT EXISTS snmp;
use snmp;

-- create snmp_oid_metadata table
CREATE TABLE IF NOT EXISTS snmp.snmp_oid_metadata (
     oid_string         VARCHAR(255) PRIMARY KEY               -- The numerical OID (e.g., ".1.3.6.1.2.1.1.1.0")
    ,object_name        VARCHAR(255)                           -- The human-readable name (e.g., "sysDescr")
    ,data_type          VARCHAR(50)                            -- The data type (e.g., "DisplayString", "Integer32")
    ,info               VARCHAR(2000)                          -- The textual description from the MIB
    ,oid_type           VARCHAR(255)                           -- "scalar", "table", "notification", etc.
    ,mib_module         VARCHAR(50)                            -- Source file / Module Name
);


-- Example Records
-- INSERT statement for snmp.snmp_oid_metadata
INSERT INTO snmp.snmp_oid_metadata (
     oid_string
    ,object_name
    ,info
    ,data_type
    ,oid_type
    ,mib_module
) VALUES (
     '.1.3.6.1.2.1.1.1.0'                              
    ,'sysDescr'                                       
    ,'A textual description of the entity. This value should include the full name and version identification of the system''s hardware type, software operating-system, and networking software.' -- oid_description: Description from MIB
    ,'DisplayString'                                
    ,'scalar'                                           
    ,'TRUENAS-MIB'                                          
);

INSERT INTO snmp.snmp_oid_metadata (
     oid_string
    ,object_name
    ,info
    ,data_type
    ,oid_type
    ,mib_module
) VALUES (
     '.1.3.6.1.2.1.2.2.1.10'                            -- ifInOctets (example for a table column)
    ,'ifInOctets'                     
    ,'The total number of octets received on the interface, including framing characters.' 
    ,'Counter32'                     
    ,'table'                       
    ,'TRUENAS-MIB'                                          
);