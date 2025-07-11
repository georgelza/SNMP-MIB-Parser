#######################################################################################################################
#
#
#  	Project     	: 	SNMP MIB Parser
#
#   File            :   db.py
#
#   Description     :   Database engines currently supported: (Redis, PostgreSQL or MySql)
#
#	By              :   George Leonard ( georgelza@gmail.com )
#
#   Created     	:   05 Jul 2025
#
#
########################################################################################################################
__author__      = "George Leonard"
__email__       = "georgelza@gmail.com"
__version__     = "0.0.1"
__copyright__   = "Copyright 2025, George Leonard"


import json
import psycopg2
import mysql.connector
import redis
#import logger

class DatabaseManager:
    """
    Manages database connections and data insertion for various database types.
    """
    def __init__(self, db_type, host, port, user=None, password=None, dbname=None, schema=None, tbl_name="snmp_oid_metadata", key_prefix="oid:", logger_instance=None):
        
        self.db_type    = db_type.lower()
        self.host       = host
        self.port       = port
        self.user       = user
        self.password   = password
        self.dbname     = dbname
        self.schema     = schema        # Schema for PostgreSQL/MySQL or Redis=0
        self.tbl_name   = tbl_name      # Table name for SQL databases
        self.key_prefix = key_prefix    # For Redis
        self.connection = None
        self.cursor     = None          # For SQL databases
        self.logger     = logger_instance if logger_instance else logger.getLogger(__name__)

    # end def

    def connect(self):
        """Establishes a connection to the specified database."""
        try:
            if self.db_type == 'postgresql':
                if not psycopg2:
                    raise ImportError("psycopg2 is not installed. Cannot connect to PostgreSQL.")

                # end if
                self.connection = psycopg2.connect(
                    host    = self.host,
                    port    = self.port,
                    user    = self.user,
                    password= self.password,
                    dbname  = self.dbname
                )
                
                self.connection.autocommit  = True # Auto-commit changes
                self.cursor                 = self.connection.cursor()

                self.logger.info(f"Connected to PostgreSQL database: {self.dbname} on {self.host}:{self.port}")

                if self.schema:
                    self.cursor.execute(f"SET search_path TO {self.schema}, public;")
                    self.logger.info(f"PostgreSQL search_path set to: {self.schema}, public")

                # end if
            elif self.db_type == 'mysql':
                if not mysql:
                    raise ImportError("mysql-connector-python is not installed. Cannot connect to MySQL.")

                # end if
                
                self.connection = mysql.connector.connect(
                    host        = self.host,
                    port        = self.port,
                    user        = self.user,
                    password    = self.password,
                    database    = self.dbname
                )

                self.cursor = self.connection.cursor()
                self.logger.info(f"Connected to MySQL database: {self.dbname} on {self.host}:{self.port}")

            elif self.db_type == 'redis':
                if not redis:
                    raise ImportError("redis is not installed. Cannot connect to Redis.")

                #end if
                
                self.connection = redis.Redis(
                    host     = self.host,
                    port     = self.port,
                    db       = self.dbname,     # In Redis, 'database' is an integer index
                    password = self.password
                )

                self.connection.ping()          # Test connection
                self.logger.info(f"Connected to Redis database: {self.dbname} on {self.host}:{self.port}")

            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")

            #end if
        except Exception as e:
            self.logger.error(f"Error connecting to {self.db_type} database: {e}")
            self.connection = None
            self.cursor     = None
            raise
        
        #end try
    # end def


    def insert_oid_metadata(self, oid_data_list):
        """
        Inserts a list of OID metadata dictionaries into the connected database.
        Uses UPSERT logic for SQL databases.
        """
        if not self.connection:
            self.logger.error("No active database connection. Please connect first.")
            return

        # end if
        
        if self.db_type == 'postgresql':
            
            table_full_name = f"{self.schema}.{self.tbl_name}" if self.schema else self.tbl_name
            sql = f"""
                INSERT INTO {table_full_name} (oid_string, object_name, info, data_type, oid_type, mib_module)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (oid_string) DO UPDATE SET
                     object_name        = EXCLUDED.object_name
                    ,info               = EXCLUDED.info
                    ,data_type          = EXCLUDED.data_type
                    ,oid_type           = EXCLUDED.oid_type
                    ,mib_module         = EXCLUDED.mib_module;
            """
            
            try:
                for oid in oid_data_list:
                    self.cursor.execute(sql, (
                        oid['oid_string'],
                        oid['object_name'],
                        oid['info'],
                        oid['data_type'],
                        oid['oid_type'],
                        oid['mib_module']
                    ))
                
                # end for
                self.logger.info(f"Successfully inserted/updated {len(oid_data_list)} OIDs into PostgreSQL table '{table_full_name}'.")

            except Exception as e:
                self.logger.error(f"Error inserting into PostgreSQL table '{table_full_name}': {e}")

            # end try
        elif self.db_type == 'mysql':
            # For MySQL, schema is part of the database connection, not table name directly in query
            sql = f"""
                INSERT INTO {self.tbl_name} (oid_string, object_name, info, data_type, oid_type, mib_module)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    object_name     = VALUES(object_name),
                    info            = VALUES(info),
                    data_type       = VALUES(data_type),
                    oid_type        = VALUES(oid_type),
                    mib_module      = VALUES(mib_module);
            """
            try:
                for oid in oid_data_list:
                    self.cursor.execute(sql, (
                         oid['oid_string']
                        ,oid['object_name']
                        ,oid['info']
                        ,oid['data_type']
                        ,oid['oid_type']
                        ,oid['mib_module']
                    ))

                # end for
                self.connection.commit()
                self.logger.info(f"Successfully inserted/updated {len(oid_data_list)} OIDs into MySQL table '{self.tbl_name}'.")

            except Exception as e:
                self.logger.error(f"Error inserting into MySQL table '{self.tbl_name}': {e}")
                self.connection.rollback()

            # enf try
        elif self.db_type == 'redis':
            try:
                pipe = self.connection.pipeline()
                for oid in oid_data_list:
                    redis_key = f"{self.key_prefix}{oid['oid_string']}"
                    pipe.set(redis_key, json.dumps(oid))

                # end for
                pipe.execute()
                self.logger.info(f"Successfully inserted/updated {len(oid_data_list)} OIDs into Redis (keys prefixed with '{self.key_prefix}').")

            except Exception as e:
                self.logger.error(f"Error inserting into Redis: {e}")
            
            # end try
        else:
            self.logger.warning(f"Insertion not supported for database type: {self.db_type}")

        # end if
    # end insert_oid_metadata


    def close(self):
        """Closes the database connection."""
        if self.connection:
            if self.db_type in ['postgresql', 'mysql'] and self.cursor:
                self.cursor.close()

            # end if
            self.connection.close()
            self.logger.info(f"Closed {self.db_type} database connection.")

        else:
            self.logger.info("No active connection to close.")
            
        # end if
    # end def close
# end class DatabaseManager

