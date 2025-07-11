
python3 mib_parser.py \
    --mib-file mibslocal/TRUENAS-MIB.mib \
    --mib-dirs mibstd/ \
    --db-type mysql \
    --db-host localhost \
    --db-port 3306 \
    --db-user dbadmin \
    --db-password dbpassword \
    --db-name snmp \
    --db-schema snmp \
    --tbl-name snmp_oid_metadata

