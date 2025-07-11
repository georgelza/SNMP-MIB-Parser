



-- create snmp_oid_metadata table
CREATE TABLE IF NOT EXISTS public.snmp_oid_metadata (
     oid_string         VARCHAR(255) PRIMARY KEY               -- The numerical OID (e.g., ".1.3.6.1.2.1.1.1.0")
    ,object_name        VARCHAR(255)                           -- The human-readable name (e.g., "sysDescr")
    ,data_type          VARCHAR(50)                            -- The data type (e.g., "DisplayString", "Integer32")
    ,info               VARCHAR(2000)                          -- The textual description from the MIB
    ,oid_type           VARCHAR(255)                           -- "scalar", "table", "notification", etc.
    ,mib_module         VARCHAR(50)                            -- Source file / Module Name
);


-- Example Records
-- INSERT statement for public.snmp_oid_metadata
INSERT INTO public.snmp_oid_metadata (
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

INSERT INTO public.snmp_oid_metadata (
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


-- INSERT statement for public.snmp_device_info
-- This table stores information about network devices.
INSERT INTO public.snmp_device_info (
     device_id
    ,ip_address
    ,hostname
    ,device_location
    ,device_type
    ,vendor
    ,model
    ,firmware_version
    ,last_updated_ts
) VALUES (
     '172.16.10.2:161'                                  -- device_id: Unique identifier for the device
    ,'72.16.10.2'                                       -- ip_address: IP address
    ,'UnifiProMax-24PoE'                                -- hostname: Hostname
    ,'BN:11/FN:01/DCRN:Study/RN:01/RCKN:01/UN:10'       -- device_location: Physical location
    ,'Switch'                                           -- device_type: Type of device
    ,'Unifi'                                            -- vendor: Device vendor
    ,'Pro-Max24PoE'                                     -- model: Device model
    ,'IOS XE 17.6.1a'                                   -- firmware_version: Firmware/OS version
    ,CURRENT_TIMESTAMP                                  -- last_updated_ts: Current timestamp with milliseconds
);

INSERT INTO public.snmp_device_info (
     device_id
    ,ip_address
    ,hostname
    ,device_location
    ,device_type
    ,vendor
    ,model
    ,firmware_version
    ,last_updated_ts
) VALUES (
     '172.16.10.3:161'                            
    ,'72.16.10.3'                               
    ,'UnifiAggregation'                           
    ,'BN:11/FN:01/DCRN:Study/RN:01/RCKN:01/UN:05'  
    ,'Switch'                                   
    ,'Unifi'                                
    ,'Aggregation'                             
    ,'IOS XE 17.6.1a'                             
    ,CURRENT_TIMESTAMP                            
);