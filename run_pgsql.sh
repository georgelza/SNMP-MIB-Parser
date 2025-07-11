
python3 mib_parser.py \
    --mib-file mibslocal/TRUENAS-MIB.mib \
    --mib-dirs mibstd/ \
    --db-type postgresql \
    --db-host localhost \
    --db-port 5433 \
    --db-user dbadmin \
    --db-password dbpassword \
    --db-name snmp \
    --db-schema public \
    --tbl-name snmp_oid_metadata

