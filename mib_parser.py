    #######################################################################################################################
#
#
#  	Project     	: 	SNMP MIB Parser/Database Loader.
#
#   File            :   mib_parser.py
#
#   Description     :   Load extracted oid from MIB files into designated tables that can be
#                   :   exposed into Apache Flink
#
#                   :   Database engines currently supported: (Redis, PostgreSQL or MySql).
#
#	By              :   George Leonard ( georgelza@gmail.com )
#
#   Created     	:   11 Jul 2025
#
#   MySQL           :   python mib_parser.py \
#                           --mib-file mibs/RFC1213-MIB.mib \
#                           --mib-dirs mibstd \
#                           --db-type mysql \
#                           --db-host localhost \
#                           --db-port 3306 \
#                           --db-user dbadmin \
#                           --db-password dbpassword \
#                           --db-name snmp \
#                           --db-schema snmp \
#                           --tbl-name snmp_oid_data
#
#   PostgreSQL      :   python mib_parser.py \
#                           --mib-file mibs/RFC1213-MIB.mib \
#                           --mib-dirs mibstd \
#                           --db-type postgresql \
#                           --db-host localhost \
#                           --db-port 5432 \
#                           --db-user dbadmin \
#                           --db-password dbpassword \
#                           --db-name snmp \
#                           --db-schema public \
#                           --tbl-name snmp_oid_data
#
#   Redis           :   python mib_parser.py \
#                           --mib-file mibs/RFC1213-MIB.mib \
#                           --mib-dirs mibstd \
#                           --db-type redis \
#                           --db-host localhost \
#                           --db-port 6379 \
#                           --db-user dbadmin \
#                           --db-password dbpassword \
#                           --db-name 0 \
#                           --redis-key-prefix oid
#
#   The script now uses argparse to accept command-line arguments for:
#
#           --mib-file:         Path to MIB file.
#           --mib-dirs:         Optional list of directories where dependent MIBs are located.
#           --db-type           (required): postgresql, mysql, or redis.
#           --db-host           (required): Database hostname.
#           --db-port           (required): Database port. [3306, 5432, 6379]
#           --db-user:          Username (for SQL).
#           --db-password:      Password (for all).
#           --db-name:          (required): Database name (for SQL) or DB index (for Redis).
#           --db-schema:        (required): Schema name (for Mysql and PostgreSQL).
#           --tbl-name:         Target table to load data into (for PostgreSQL/MySQL).
#           --redis-key-prefix: Custom key prefix for Redis (defaults to oid:).
#
#
########################################################################################################################
__author__      = "George Leonard"
__email__       = "georgelza@gmail.com"
__version__     = "0.0.1"
__copyright__   = "Copyright 2025, George Leonard"


from utils              import logger 
from datetime           import datetime
from db                 import *

from pysnmp.smi         import builder, view, compiler, error
from pysmi              import debug
from pysmi.reader       import FileReader
from pysmi.searcher     import StubSearcher
from pysmi.writer       import PyFileWriter
from pysmi.parser       import SmiStarParser
from pysmi.codegen      import PySnmpCodeGen
from pysmi.compiler     import MibCompiler

import argparse, os, sys


# Initialize logger instance globally for this script
current_datetime    = datetime.now()
datetime_str        = current_datetime.strftime("%Y%m%d_%H%M%S") # Example format: 20250709_165531

LOG_TAG             = 'mib_parser'
LOG_FILE            = f'{LOG_TAG}_{datetime_str}.log'
CONSOLE_DEBUG_LEVEL = 1, # INFO
FILE_DEBUG_LEVEL    = 0, # DEBUG - changed to 0 for less verbose file logging unless explicitly needed
CONSOLE_LOG_FORMAT  = '%(asctime)s - %(levelname)s - %(processName)s - %(message)s'
FILE_LOG_FORMAT     = '%(asctime)s - %(levelname)s - %(message)s'


def parse_arguments(log):
    
    try:
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(description="Parse SNMP MIB files and insert OID metadata into a database.")

        # Create a mutually exclusive group for mib_file and mib_directory
        mib_input_group = parser.add_mutually_exclusive_group(required=True)
        
        parser.add_argument('--mib-file',                   required=True, help='Path to the MIB file to parse')
        parser.add_argument('--mib-dirs',                   required=True, help='Comma-separated list of MIB directories containing dependencies')
        parser.add_argument("--db-type",                    choices=['postgresql', 'mysql', 'redis'], required=True, help="Type of database to connect to (postgresql, mysql, redis).")
        parser.add_argument("--db-host",                    required=True, help="Database hostname or IP address.")
        parser.add_argument("--db-port",                    type=int, required=True, help="Database port number.")
        parser.add_argument("--db-user",                    help="Database username (for SQL).")
        parser.add_argument("--db-password",                help="Database password (for PostgreSQL/MySQL/Redis).")
        parser.add_argument("--db-name",                    help="Database name (for PostgreSQL/MySQL) or DB index (for Redis).")
        parser.add_argument("--db-schema",                  help="Database schema name (for PostgreSQL and MySQL).")

        mib_input_group.add_argument("--tbl-name",          default="snmp_oid_metadata", help="Table name for SQL databases (PostgreSQL/MySQL). Defaults to 'snmp_oid_metadata'.")
        mib_input_group.add_argument("--redis-key-prefix",  default="oid:", help="Prefix for Redis keys (e.g., 'oid:' for 'oid:1.3.6.1.2.1.1.3.0'). Only for Redis.")

        return parser.parse_args()
    except Exception as err:
        log.error(f"Error on arguments {err}")
        return None
    
#end def


def extract_mib_module_name(mib_file_path, log):
    """Extract the MIB module name from the MIB file."""
    try:
        with open(mib_file_path, 'r') as f:
            content = f.read()
            
        # Look for the module definition line (usually at the beginning)
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('--') and 'DEFINITIONS' in line:
                # Extract module name (everything before 'DEFINITIONS')
                module_name = line.split('DEFINITIONS')[0].strip()
                return module_name
                
        # Fallback: use filename without extension
        return os.path.splitext(os.path.basename(mib_file_path))[0]
        
    except Exception as e:
        log.error(f"Error extracting module name from {mib_file_path}: {e}")
        return os.path.splitext(os.path.basename(mib_file_path))[0]

#end def


def parse_mib_file_for_metadata(mib_file_path, log):
    """Parse the MIB file directly to extract info and types."""
    try:
        with open(mib_file_path, 'r') as f:
            content = f.read()
        
        # Remove comments but keep line structure for better parsing
        lines       = content.split('\n')
        clean_lines = []
        for line in lines:
            # Remove comments but keep the line
            if '--' in line:
                line = line.split('--')[0]
                
            clean_lines.append(line)
        
        content = '\n'.join(clean_lines)
        
        # Dictionary to store metadata
        metadata = {}
        
        # Split into sections - look for OBJECT-TYPE definitions
        import re
        
        # Pattern to match OBJECT-TYPE definitions
        object_pattern = r'(\w+)\s+OBJECT-TYPE\s+(.*?)(?=\n\s*\w+\s+OBJECT-TYPE|\n\s*\w+\s+::=|\Z)'
        
        matches = re.findall(object_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            obj_name = match[0].strip()
            obj_body = match[1].strip()
            
            # Extract DESCRIPTION (now called info)
            info_match  = re.search(r'DESCRIPTION\s*"([^"]*)"', obj_body, re.DOTALL)
            info        = ""
            if info_match:
                info = info_match.group(1).strip()
            
            # Extract SYNTAX type
            type_value      = ""
            syntax_match    = re.search(r'SYNTAX\s+([^\s\n]+)', obj_body, re.IGNORECASE)
            if syntax_match:
                type_value = syntax_match.group(1).strip()
            
            # Store metadata
            metadata[obj_name] = {
                'info': info,
                'type': type_value
            }
        
        log.info(f"Extracted metadata for {len(metadata)} objects from MIB file")
        return metadata
        
    except Exception as e:
        log.error(f"Error parsing MIB file for metadata: {e}")
        return {}

    #end try
#end def


def get_target_mib_oid_prefix(mib_file_path, log):
    """Extract the OID prefix for the target MIB module."""
    try:
        with open(mib_file_path, 'r') as f:
            content = f.read()
        
        # Look for MODULE-IDENTITY and its OID assignment
        lines       = content.split('\n')
        module_name = None
        
        # First find the module name
        for line in lines:
            line = line.strip()
            if line and not line.startswith('--') and 'DEFINITIONS' in line:
                module_name = line.split('DEFINITIONS')[0].strip()
                break
        
        if not module_name:
            return None
        
        # Look for the module identity OID assignment
        # Pattern: moduleName MODULE-IDENTITY ... or moduleName OBJECT IDENTIFIER ::= { ... }
        for i, line in enumerate(lines):
            line = line.strip()
            if (line.startswith(module_name) and 
                ('MODULE-IDENTITY' in line or 'OBJECT IDENTIFIER' in line)):
                
                # Look for the OID assignment in the next few lines
                for j in range(i, min(i + 10, len(lines))):
                    if '::=' in lines[j]:
                        # Extract OID from the assignment
                        oid_part = lines[j].split('::=')[1].strip()
                        if '{' in oid_part and '}' in oid_part:
                            oid_content = oid_part.split('{')[1].split('}')[0].strip()
                            # Parse the OID content (e.g., "enterprises 50536" or "1 3 6 1 4 1 50536")
                            parts = oid_content.split()
                            
                            # Convert symbolic names to numbers if needed
                            if 'enterprises' in parts:
                                idx = parts.index('enterprises')
                                # enterprises = 1.3.6.1.4.1
                                oid_parts = ['1', '3', '6', '1', '4', '1'] + parts[idx+1:]
                                return '.'.join(oid_parts)
                            
                            elif 'internet' in parts:
                                idx = parts.index('internet')
                                # internet = 1.3.6.1
                                oid_parts = ['1', '3', '6', '1'] + parts[idx+1:]
                                return '.'.join(oid_parts)
                            
                            else:
                                # Assume it's already numeric
                                return '.'.join(parts)
                            
                            #end if
                        #end if
                        break
                    #end if
                #end for
            #end if
        #end for
        
        return None
        
    except Exception as e:
        log.error(f"Error extracting OID prefix from {mib_file_path}: {e}")
        return None

    #end try
#end def


def compile_mib_file(mib_file_path, mib_dirs, output_dir=None, log=None):
    """Compile a MIB file to Python using pysmi."""
    try:
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(mib_file_path), 'compiled_mibs')
        
        #end if
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create MIB compiler
        mibCompiler = MibCompiler(
            SmiStarParser(),
            PySnmpCodeGen(),
            PyFileWriter(output_dir)
        )
        
        # Add MIB sources (directories to search for MIB files)
        mib_sources = []
        
        # Add the directory containing the target MIB file
        mib_file_dir = os.path.dirname(os.path.abspath(mib_file_path))
        mib_sources.append(mib_file_dir)
        
        # Add user-specified MIB directories
        for mib_dir in mib_dirs:
            if os.path.exists(mib_dir):
                mib_sources.append(mib_dir)

            #end if
        #end for
        
        # Add MIB sources to compiler (correct API)
        for mib_source in mib_sources:
            mibCompiler.addSources(FileReader(mib_source))
        
        #end for
        
        # Add MIB searchers (for finding dependencies)
        for mib_source in mib_sources:
            mibCompiler.addSearchers(StubSearcher(mib_source))
        
        #end for
        
        # Get MIB module name from file
        mib_module_name = extract_mib_module_name(mib_file_path, log)
        
        log.info(f"Compiling MIB module: {mib_module_name}")
        log.info(f"Output directory:     {output_dir}")
        log.info(f"MIB sources:          {mib_sources}")
        
        # Compile the MIB
        results = mibCompiler.compile(mib_module_name)
        
        log.info(f"Compilation results: {results}")
        
        if mib_module_name in results:
            status = results[mib_module_name]
            if status == 'compiled':
                log.info(f"Successfully compiled MIB: {mib_module_name}")
                return output_dir, mib_module_name
            
            else:
                log.error(f"MIB compilation failed: {status}")
                return None, None
            #end if
        else:
            log.error(f"MIB compilation results did not include {mib_module_name}")
            return None, None
        
        #end if
    except Exception as e:
        log.error(f"Error compiling MIB file: {e}", exc_info=True)
        return None, None

    #end try

def extract_syntax_type(mib_node, object_name, mib_metadata, log):
    """Extract the syntax type from a MIB node with multiple fallback methods."""
    type_value = ""
    
    try:
        # Method 1: Try to get from the syntax object
        if hasattr(mib_node, 'syntax') and mib_node.syntax is not None:
            syntax = mib_node.syntax
            
            # Try getTypeName method first
            if hasattr(syntax, 'getTypeName') and callable(getattr(syntax, 'getTypeName')):
                try:
                    type_value = syntax.getTypeName()
                    if type_value:
                        return str(type_value).strip()

                    #end if
                except:
                    pass

                #end try
            #end if
                        
            # Try namedType attribute
            if hasattr(syntax, 'namedType') and syntax.namedType:
                try:
                    type_value = str(syntax.namedType)
                    if type_value:
                        return type_value.strip()
                    
                    #end if
                except:
                    pass
                
                #end try
            #end if
            
            # Try class name
            if hasattr(syntax, '__class__') and hasattr(syntax.__class__, '__name__'):
                try:
                    type_value = syntax.__class__.__name__
                    if type_value:
                        return type_value.strip()

                    #end if
                except:
                    pass
            
                #end try
            #end if
            
            # Try type name from type object
            if hasattr(syntax, 'type') and hasattr(syntax.type, '__name__'):
                try:
                    type_value = syntax.type.__name__
                    if type_value:
                        return type_value.strip()

                    #end if
                except:
                    pass
                #end try
            #end if
        #end if
        
        # Method 2: Try to get from the node's direct type attributes
        if hasattr(mib_node, 'type') and mib_node.type is not None:
            try:
                if hasattr(mib_node.type, '__name__'):
                    type_value = mib_node.type.__name__
                    if type_value:
                        return type_value.strip()
                    
                    #end if
                else:
                    type_value = str(mib_node.type)
                    if type_value:
                        return type_value.strip()

                    #end if
                #end if
            except:
                pass
        
            #end try
        #end if
        
        # Method 3: Try to get from the node's class name
        if hasattr(mib_node, '__class__') and hasattr(mib_node.__class__, '__name__'):
            try:
                class_name = mib_node.__class__.__name__
                # Convert PySNMP class names to more readable types
                if 'Integer' in class_name:
                    return 'Integer'

                elif 'Counter' in class_name:
                    return 'Counter'

                elif 'Gauge' in class_name:
                    return 'Gauge'

                elif 'TimeTicks' in class_name:
                    return 'TimeTicks'

                elif 'OctetString' in class_name:
                    return 'OctetString'

                elif 'ObjectIdentifier' in class_name:
                    return 'ObjectIdentifier'

                elif 'IpAddress' in class_name:
                    return 'IpAddress'

                elif 'Opaque' in class_name:
                    return 'Opaque'

                elif 'Counter64' in class_name:
                    return 'Counter64'

                else:
                    return class_name

                #end if
            except:
                pass
        
            #end try
        # Method 4: Try to get from parsed MIB metadata
        if object_name in mib_metadata and mib_metadata[object_name]['type']:
            return mib_metadata[object_name]['type']
       
        #end if
         
        # Method 5: Try to extract from string representation
        try:
            node_str = str(mib_node)
            if 'Integer' in node_str:
                return 'Integer'
     
            elif 'Counter' in node_str:
                return 'Counter'
     
            elif 'Gauge' in node_str:
                return 'Gauge'
     
            elif 'TimeTicks' in node_str:
                return 'TimeTicks'
     
            elif 'OctetString' in node_str:
                return 'OctetString'
     
            elif 'ObjectIdentifier' in node_str:
                return 'ObjectIdentifier'

            #end if
        except:
            pass
        
        #end try
        
        # If all methods fail, return "Unknown"
        return "Unknown"
        
    except Exception as e:
        log.debug(f"Error extracting syntax type for {object_name}: {e}")
        # Final fallback to parsed metadata
        if object_name in mib_metadata and mib_metadata[object_name]['type']:
            return mib_metadata[object_name]['type']
        
        #end if
        return "Unknown"
    #end try
#end def


def extractor(args, log):
    
    try:
        # Validate MIB file exists
        if not os.path.exists(args.mib_file):
            log.error(f"MIB file not found: {args.mib_file}")
            sys.exit(1)
        
        #end if
        
        # Parse MIB directories
        mib_dirs = [d.strip() for d in args.mib_dirs.split(',')]                            
        
        # Parse the MIB file for metadata (info, types, etc.)
        log.info("Parsing MIB file for metadata...")
        mib_metadata = parse_mib_file_for_metadata(args.mib_file, log)                      

        # Get the target MIB's OID prefix
        log.info("Get Target MIB oid prefixes metadata...")
        target_oid_prefix = get_target_mib_oid_prefix(args.mib_file, log)                 
        if target_oid_prefix:
            log.info(f"Target MIB OID prefix: {target_oid_prefix}")
            
        else:
            log.warning("Could not determine target MIB OID prefix - will use module name filtering only")
        
        #end if
        
        # Compile the MIB file first
        log.info("Compiling MIB file...")
        compiled_dir, target_mib_module = compile_mib_file(mib_file_path=args.mib_file, mib_dirs=mib_dirs, log=log)    
        
        if not compiled_dir or not target_mib_module:
            log.error("Failed to compile MIB file")
            sys.exit(1)
        
        #end if
        
        # Create MIB builder
        mibBuilder  = builder.MibBuilder()                                                  
        # Get base directory
        base_dir    = os.path.dirname(os.path.abspath(__file__))                            
        
        # Add the compiled MIB directory first
        mibBuilder.add_mib_sources(builder.DirMibSource(compiled_dir))                      
        log.info(f"Added compiled MIB directory: {compiled_dir}")
        
         # Add standard PySNMP MIB sources
        stdmibslocations = ["pysnmp_mibs/pysnmp_mibs"]                                     
        
        for stdmibs in stdmibslocations:
            mib_path = os.path.join(base_dir, stdmibs)
            if os.path.exists(mib_path):
                mibBuilder.add_mib_sources(builder.DirMibSource(mib_path))
                log.info(f"Added standard MIB directory: {stdmibs}")

            #end if
        #end for
        
        # Add user-specified MIB directories
        for mib_dir in mib_dirs:
            if os.path.exists(mib_dir):
                mibBuilder.add_mib_sources(builder.DirMibSource(mib_dir))
                log.info(f"Added MIB directory: {mib_dir}")
                
            else:
                log.warning(f"MIB directory not found: {mib_dir}")
        
            #end if
        #end try
        
        # Add the directory containing the target MIB file
        mib_file_dir = os.path.dirname(os.path.abspath(args.mib_file))
        mibBuilder.add_mib_sources(builder.DirMibSource(mib_file_dir))
        log.info(f"Added MIB file directory: {mib_file_dir}")
        
        # Load standard MIB modules first
        standard_mibs = ['SNMPv2-SMI', 'SNMPv2-TC', 'SNMPv2-MIB', 'RFC1213-MIB']
        for mib_module in standard_mibs:
            try:
                mibBuilder.load_modules(mib_module)
                log.info(f"Loaded standard MIB: {mib_module}")
                
            except Exception as e:
                log.warning(f"Could not load standard MIB {mib_module}: {e}")
        
            #end try
        #end for
        
        # Load the target MIB module
        log.info(f"Attempting to load target MIB module: {target_mib_module}")
        
        try:
            mibBuilder.load_modules(target_mib_module)
            log.info(f"Successfully loaded target MIB module: {target_mib_module}")

        except Exception as e:
            log.error(f"Failed to load target MIB module {target_mib_module}: {e}")
            sys.exit(1)
        
        #end try      
        
        
        # Create MIB view
        mibView = view.MibViewController(mibBuilder)
        
        log.info("Starting MIB walk...")
        
        # Start MIB walk
        oid, label, suffix  = mibView.get_first_node_name()
        oid_count           = 0
        oidData             = []
        
        while True:
            try:
                modName, nodeDesc, suffix = mibView.get_node_location(oid)
                mibNode, = mibBuilder.import_symbols(modName, nodeDesc)

                oid_string      = '.'.join([str(x) for x in oid])
                object_name     = nodeDesc
                info            = ""
                type_value      = ""
                oid_type        = ""

                # --- INFO EXTRACTION ---
                try:
                    # First try to get info from the compiled MIB
                    if hasattr(mibNode, 'getDescription') and callable(getattr(mibNode, 'getDescription')):
                        desc = mibNode.getDescription()
                        if desc:
                            info = str(desc).strip()
                        
                        #end if
                    elif hasattr(mibNode, 'description') and mibNode.description:
                        info = str(mibNode.description).strip()
                    
                    #end if
                    
                    # If no info found, try to get it from the parsed MIB metadata
                    if not info and object_name in mib_metadata:
                        info = mib_metadata[object_name]['info']
                        
                    #end if
                except Exception as e:
                    log.debug(f"Error extracting info for {object_name}: {e}")
                    # Try to get it from parsed metadata as fallback
                    if object_name in mib_metadata:
                        info = mib_metadata[object_name]['info']
                
                    #end if
                #end try
                
                # --- TYPE EXTRACTION ---
                type_value = extract_syntax_type(mibNode, object_name, mib_metadata, log)

                # --- OID TYPE DETERMINATION ---
                try:
                    if hasattr(mibNode, '__class__') and hasattr(mibNode.__class__, '__name__'):
                        class_name = mibNode.__class__.__name__.lower()
                        
                        if 'objecttype' in class_name:
                            # Try to determine if it's scalar, table, etc.
                            if hasattr(mibNode, 'maxAccess'):
                                access = str(mibNode.maxAccess).lower()
                                if 'not-accessible' in access:
                                    oid_type = "table"
                                    
                                else:
                                    oid_type = "scalar"

                                #end if
                            else:
                                oid_type = "object"

                            #end if
                        elif 'objectidentity' in class_name:
                            oid_type = "objectIdentity"

                        elif 'moduleidentity' in class_name:
                            oid_type = "moduleIdentity"

                        elif 'notificationtype' in class_name:
                            oid_type = "notification"

                        elif 'mibscalar' in class_name:
                            oid_type = "scalar"

                        elif 'mibtable' in class_name:
                            oid_type = "table"

                        elif 'mibtablerow' in class_name:
                            oid_type = "tableRow"

                        elif 'mibtablecolumn' in class_name:
                            oid_type = "tableColumn"

                        else:
                            oid_type = class_name

                        #end if
                    else:
                        oid_type = "unknown"

                    #end if
                except Exception as e:
                    log.debug(f"Error determining OID type for {object_name}: {e}")
                    oid_type = "unknown"

                #end try
                # IMPROVED FILTERING: Only show OIDs from the target MIB
                should_print = False
                
                # Method 1: Check if it's from the target MIB module
                if modName == target_mib_module:
                    should_print = True
                    
                # Method 2: Check if OID starts with the target MIB's prefix
                elif target_oid_prefix and oid_string.startswith(target_oid_prefix):
                    should_print = True
                
                #end if
                
                # Method 3: Additional check for MIB-specific OIDs (skip standard ones)
                # Skip common standard MIB prefixes that we don't want
                standard_prefixes = [
                    '1.3.6.1.2.1.1',    # system group
                    '1.3.6.1.2.1.2',    # interfaces group
                    '1.3.6.1.2.1.3',    # at group
                    '1.3.6.1.2.1.4',    # ip group
                    '1.3.6.1.2.1.5',    # icmp group
                    '1.3.6.1.2.1.6',    # tcp group
                    '1.3.6.1.2.1.7',    # udp group
                    '1.3.6.1.2.1.8',    # egp group
                    '1.3.6.1.2.1.10',   # transmission group
                    '1.3.6.1.2.1.11',   # snmp group
                    '1.3.6.1.6.3',      # snmpModules
                    '0',                # iso root
                    '1.3.6.1.6.3.1.1.4.1.0',  # coldStart
                ]
                
                # If it's a standard prefix, don't print unless it's specifically from our target MIB
                for std_prefix in standard_prefixes:
                    if oid_string.startswith(std_prefix) and modName != target_mib_module:
                        should_print = False
                        break
                    
                    #end if
                #end for
                if should_print:
                    print(f"oid:             {oid_string}")
                    print(f"object_name:     {object_name}")
                    print(f"info:            {info}")
                    print(f"type:            {type_value}")
                    print(f"oid_type:        {oid_type}")
                    print(f"module:          {modName}")
                    print("-" * 50)
                    oid_count += 1
                    
                    oidData.append({ "oid_string":  oid_string
                                    ,"object_name": object_name
                                    ,"info":        info
                                    ,"data_type":   type_value
                                    ,"oid_type":    oid_type
                                    ,"mib_module":  modName
                                    })
                #end if
                oid, label, suffix = mibView.get_next_node_name(oid)
                
            except error.NoSuchObjectError:
                log.info("Reached end of MIB walk")
                break
            
            except Exception as e:
                log.error(f"Error processing OID {'.'.join([str(x) for x in oid])}: {e}")
                try:
                    oid, label, suffix = mibView.get_next_node_name(oid)

                except:
                    log.error("Could not continue MIB walk")
                    break
                
                #end try
            #end try
        #end while
        log.info(f"MIB walk completed. Processed {oid_count} OIDs from target MIB.")

        # Return Recordset
        return oidData
        
    except Exception as e:
        log.error(f"Fatal error during MIB processing: {e}", exc_info=True)
        sys.exit(1)
    
    #end try        
#end def


def main():
    
    try: 
        log = logger(filename           = LOG_FILE, 
                    console_debuglevel  = CONSOLE_DEBUG_LEVEL,
                    file_debuglevel     = FILE_DEBUG_LEVEL,
                    console_format      = CONSOLE_LOG_FORMAT, 
                    file_format         = FILE_LOG_FORMAT
                )
        
    except Exception as err:
        print(f"error creating logger {err}")
        sys.exit(1)
        
    #end try
    
    
    try: 
        # Parse arguments
        args = parse_arguments(log)
        
        if args != None:
            log.info(f"Starting MIB parser for file : {args.mib_file}")
            log.info(f"MIB directories              : {args.mib_dirs}")
            log.info(f"DB Type                      : {args.db_type}")
            log.info(f"DB Host                      : {args.db_host}")
            log.info(f"DB Port                      : {args.db_port}")
            log.info(f"DB Name                      : {args.db_name}")
            log.info(f"DB User                      : {args.db_user}")
            log.info(f"DB Schema                    : {args.db_schema}")
            if args.tbl_name :
                log.info(f"DB Table                     : {args.tbl_name}")
            else:
                log.info(f"redis-key-prefix                 : {args.redis_key_prefix}")

            #end if
        else:
            print(f"Error creating logger or parsing arguments: {err}")
            sys.exit(1)
        
        #end if            
    except Exception as err:
        print(f"Error creating logger or parsing arguments: {err}")
        sys.exit(1)

    #end try
    
    
    parsed_oids = extractor(args, log)
    
    if not parsed_oids:
        log.info("No OID data extracted. Exiting.")
        exit()

    # end if
    
    # Database Insertion
    db_manager = None
    try:
        db_manager = DatabaseManager(
            db_type     = args.db_type,
            host        = args.db_host,
            port        = args.db_port,
            user        = args.db_user,
            password    = args.db_password,
            dbname      = args.db_name,
            schema      = args.db_schema,
            tbl_name    = args.tbl_name,
            key_prefix  = args.redis_key_prefix,
            logger_instance = log # Pass the logger instance
        )

        db_manager.connect()
        db_manager.insert_oid_metadata(parsed_oids)

    except Exception as e:
        log.error(f"An error occurred during database operations: {e}")

    finally:
        if db_manager:
            db_manager.close()
        
        # end if
    # end try
    
#end def
    
    

if __name__ == "__main__":
    main()