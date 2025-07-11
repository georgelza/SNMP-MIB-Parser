
python3 mib_parser.py \
    --mib-file mibslocal/TRUENAS-MIB.mib \
    --mib-dirs mibstd/ \
    --db-type redis \
    --db-host localhost \
    --db-port 6379 \
    --db-name 0 \
    --redis-key-prefix oid
