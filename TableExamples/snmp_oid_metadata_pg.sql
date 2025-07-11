-- NOTE: see master README.md with regard to the mib_parser utility
CREATE TABLE hive.snmp.snmp_oid_metadata_pg (
     oid_string         VARCHAR(255) PRIMARY KEY NOT ENFORCED  -- The numerical OID (e.g., ".1.3.6.1.2.1.1.1.0")
    ,object_name        VARCHAR(255)                           -- The human-readable name (e.g., "sysDescr")
    ,data_type          VARCHAR(50)                            -- The data type (e.g., "DisplayString", "Integer32")
    ,info               VARCHAR(2000)                          -- The textual description from the MIB
    ,oid_type           VARCHAR(255)                           -- "scalar", "table", "notification", etc.
    ,mib_module         VARCHAR(50)                            -- Source file / Module Name
) WITH (
    'connector'             = 'jdbc',
    'url'                   = 'jdbc:postgresql://postgresql:5432/snmp', -- Key Change: 'jdbc:postgresql' and default port 5432
    'table-name'            = 'public.snmp_oid_metadata',               -- Key Change: Often includes schema, e.g., 'public.your_table'
    'username'              = 'public',
    'password'              = 'abfr24',
    'lookup.cache.max-rows' = '1000',                                   -- Cache OID metadata
    'lookup.cache.ttl'      = '24h'                                     -- OID metadata changes rarely, so a long TTL is fine
);