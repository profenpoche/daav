import base64
import json
import logging
import os
from typing import Dict, List, Optional

import duckdb
import pandas as pd
import numpy as np
from app.config.settings import settings
from app.models.interface.dataset_interface import Pagination, FileContentResponse
from app.models.interface.dataset_schema import PandasColumn, PandasSchema
from app.utils.security import PathSecurityValidator
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Schéma minimal JSON:API pour validation avec jsonschema
json_api_schema = {
    "type": "object",
    "properties": {
        "data": {"type": ["array", "object"]},
        "links": {
            "type": "object",
            "properties": {
                "self": {"type": "string"},
                "next": {"type": ["string", "null"]},
                "prev": {"type": ["string", "null"]}
            },
            "required": ["self"]
        },
        "meta": {"type": "object"}
    },
    "required": ["data", "links"]
}

custom_api_schema = {
    "type": "object",
    "properties": {
        "data": {"type": "array"},
        "count": {"type": "integer"},
        "self": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "href": {"type": "string"}
            },
            "required": ["href"]
        },
        "next": {
            "type": ["object", "null"],
            "properties": {
                "title": {"type": "string"},
                "href": {"type": "string"}
            },
            "required": ["href"]
        },
        "prev": {
            "type": ["object", "null"],
            "properties": {
                "title": {"type": "string"},
                "href": {"type": "string"}
            },
            "required": ["href"]
        }
    },
    "required": ["data", "count", "self"]
}

def convert_numpy_type_to_python(value) -> str:
    """Convert numpy types to standard Python type names to avoid deprecation warnings."""
    if isinstance(value, (np.bool_, bool)):
        return "bool"
    elif isinstance(value, (np.int8, np.int16, np.int32, np.int64)):
        return "int"
    elif isinstance(value, (np.uint8, np.uint16, np.uint32, np.uint64)):
        return "int"
    elif isinstance(value, (np.float16, np.float32, np.float64)):
        return "float"
    elif isinstance(value, (np.complex64, np.complex128)):
        return "complex"
    elif isinstance(value, np.str_):
        return "str"
    elif isinstance(value, np.bytes_):
        return "bytes"
    else:
        # For other types, use the standard type name
        type_name = type(value).__name__
        # Handle some common numpy array dtypes
        if hasattr(value, 'dtype'):
            dtype_str = str(value.dtype)
            if 'int' in dtype_str:
                return "int"
            elif 'float' in dtype_str:
                return "float"
            elif 'bool' in dtype_str:
                return "bool"
            elif 'str' in dtype_str or 'object' in dtype_str:
                return "str"
        return type_name


def convert_size(size: str) -> str:
    import math

    if size == 0:
        return "0B"
    size_units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, 2)
    return "%s %s" % (s, size_units[i])

# Folder reading function
def folder(folder: str, pagination: Pagination = None) -> FileContentResponse | list:
    from datetime import datetime, timezone
    import magic
    import math
    
    # SECURITY: Input path validation (uses centralized security bypass)
    from app.utils.security import PathSecurityValidator, FileAccessController
    from app.config.security import SecurityConfig
    
    # Use centralized security validation (automatically handles test environment bypass)
    validated_folder = PathSecurityValidator.validate_file_path(folder)
    # Get allowed directories list (including dynamic upload_dir)
    allowed_base_dirs = SecurityConfig.get_allowed_base_directories()
    if not FileAccessController.can_read_file(validated_folder, allowed_base_dirs):
        raise PermissionError(f"Access denied to directory: {folder}")
    # Use validated path for processing
    folder = validated_folder
            
    donnees = []
    max_size = settings.max_file_size  # Get max file size from settings
    file_count = 0  # Total file counter
    
    # calculate pagination indices
    if pagination:
        start_index = (pagination.page - 1) * pagination.perPage
        end_index = start_index + pagination.perPage
    else:
        start_index = 0
        end_index = float('inf')  # No limit
    
    def explorer_recursif(folder_path):
        nonlocal file_count
        try:
            with os.scandir(folder_path) as entries:
                for entry in entries:
                    try:
                        if entry.is_dir():
                            explorer_recursif(entry.path)
                        elif entry.is_file():
                            # Increment count for each file processed
                            current_file_index = file_count
                            file_count += 1
                            
                            # Retrieve detailand add on result only if within pagination range
                            if start_index <= current_file_index < end_index:
                                stats = entry.stat()
                                mime = magic.from_file(entry.path, mime=True)
                                size = str(convert_size(stats.st_size))
                                created = str(datetime.fromtimestamp(stats.st_ctime, tz=timezone.utc)).rsplit('.', 1)[0]
                                modified = str(datetime.fromtimestamp(stats.st_mtime)).rsplit('.', 1)[0]
                                
                                content = None
                                base_64 = None
                                file_ext = entry.name.lower().split('.')[-1] if '.' in entry.name else ''
                                
                                # JSON files
                                if mime == 'application/json' or file_ext == 'json':
                                    try:
                                        with open(entry.path, 'r', encoding='utf-8') as json_file:
                                            content = json.load(json_file) 
                                    except Exception as e:
                                        print(f"Error opening JSON file {entry.name}: {e}")
            
                                # CSV files
                                elif mime == 'text/csv' or file_ext == 'csv':
                                    try:
                                        import csv
                                        with open(entry.path, 'r', encoding='utf-8') as csv_file:
                                            reader = csv.DictReader(csv_file)
                                            content = list(reader)
                                    except Exception as e:
                                        print(f"Error opening CSV file {entry.name}: {e}")
                
                                # XML files
                                elif mime == 'application/xml' or file_ext in ['xml', 'xsd']:
                                    try:
                                        with open(entry.path, 'r', encoding='utf-8') as xml_file:
                                            content = xml_file.read()
                                    except Exception as e:
                                        print(f"Error opening XML file {entry.name}: {e}")
                
                                # YAML files
                                elif file_ext in ['yml', 'yaml']:
                                    try:
                                        import yaml
                                        with open(entry.path, 'r', encoding='utf-8') as yaml_file:
                                            content = yaml.safe_load(yaml_file)
                                    except Exception as e:
                                        print(f"Error opening YAML file {entry.name}: {e}")
                
                                # Plain text files
                                elif mime.startswith('text/') or file_ext in ['txt', 'log', 'md', 'py', 'js', 'html', 'css']:
                                    try:
                                        with open(entry.path, 'r', encoding='utf-8') as text_file:
                                            content = text_file.read()
                                    except Exception as e:
                                        print(f"Error opening text file {entry.name}: {e}")
                
                                # Media files
                                elif (mime.startswith(('image/', 'audio/', 'video/')) or
                                    file_ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico',
                                                'mp3', 'wav', 'ogg', 'aac', 'flac', 'm4a', 'wma',
                                                'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', '3gp']):
                                    try:                                                                       
                                        if stats.st_size > max_size:
                                            print(f"Media file {entry.name} too large ({convert_size(stats.st_size)}) - 50 MB limit")
                                            base_64 = None
                                        else:
                                            with open(entry.path, "rb") as media_file:
                                                convert = base64.b64encode(media_file.read())
                                                base_64 = convert.decode('utf-8')
                                    except Exception as e:
                                        print(f"Error during base64 conversion of media file {entry.name}: {e}")
                                                        
                                data = {
                                    'media': base_64, 
                                    'path': entry.path, 
                                    'folder': folder_path, 
                                    'file': entry.name, 
                                    'mime_type': mime, 
                                    'size': size, 
                                    'created': created, 
                                    'modified': modified, 
                                    'content': content
                                }
                                donnees.append(data)
                    except (OSError, PermissionError) as e:
                        print(f"Access error to {entry.path}: {e}")
        except (OSError, PermissionError) as e:
            print(f"Access error to folder {folder_path}: {e}")
    
    # Use the folder (already security validated)
    explorer_recursif(folder)
    
    # Return according to requested format
    if pagination is None:
        return donnees
    else:
        return FileContentResponse(
            data=donnees,
            total_rows=file_count,
            current_page=pagination.page,
            limit=pagination.perPage
        )


def generate_pandas_schema(data: pd.DataFrame | pd.Series | dict) -> PandasSchema:
    schema: List[PandasColumn] = []
    
    # Handle DataFrame
    if isinstance(data, pd.DataFrame):
        for column in data.columns:
            col_name = str(column)
            
            # Basic column info
            col_schema = PandasColumn(
                name=col_name,
                dtype=str(data[column].dtype),
                nullable=data[column].isnull().any(),
                count=data[column].notnull().sum(),
                nested=None
            )
            

            if isinstance(data[column], (pd.Series, pd.DataFrame, dict)):
                nested_schema = generate_pandas_schema(data[column])
                col_schema.nested = nested_schema.root
                if isinstance(data[column], pd.Series) and isinstance(data[column].index, pd.RangeIndex) and data.index.start == 0 :
                    col_schema.dtype = nested_schema.root[0].dtype
                    col_schema.count = data[column].size
                    if(nested_schema.root[0].name == "#array_item#"):
                        col_schema.nested = None
            schema.append(col_schema)
    
    # Handle Series
    elif isinstance(data, pd.Series):
        # for item collection without name use a key tag to remove the upper nested and just type the parent collection
        array_item_tag = "#array_item#"
        if len(data) == 0:
            return PandasSchema(root=[])

        if not data.empty:
            non_null_values = data.dropna()
            if len(non_null_values) > 0:
                sample_value = non_null_values.iloc[0]
                
                # S'il s'agit d'une Series de types simples (pas de structures imbriquées)
                if not isinstance(sample_value, (dict, list, pd.Series, pd.DataFrame)):
                    col_schema = PandasColumn(
                        name=array_item_tag,
                        dtype=convert_numpy_type_to_python(sample_value),
                        nullable=data.isnull().any(),
                        count=data.size,
                        nested=None
                    )
                    schema.append(col_schema)
                # Pour les Series contenant des dictionnaires ou des structures plus complexes
                else:
                    # Itérer sur les index de la Series
                    for idx in data.index:
                        nested_schema = None
                        item_name = str(idx)
                        value = data.get(idx)                        
                        if not isinstance(value, list) and pd.isna(value):
                            col_schema = PandasColumn(
                                name=item_name,
                                dtype="NaN",
                                nullable=True,
                                count=0,
                                nested=None
                            )
                        # Series with array-like structure    
                        else:
                            value_type = convert_numpy_type_to_python(value)
                            col_schema = PandasColumn(
                                name=item_name,
                                dtype=value_type,
                                nullable=False,
                                count=1,
                                nested=None
                            )
                            
                            # Gérer les structures imbriquées dans la Series
                            if isinstance(value, (pd.Series, pd.DataFrame, dict)):
                                nested_schema = generate_pandas_schema(value)
                                col_schema.nested = nested_schema.root
                            # list with object item inside -> continue detection   
                            elif isinstance(value, list) and value and isinstance(value[0], dict):
                                nested_schema = generate_pandas_schema(value[0])
                                col_schema.nested = nested_schema.root
                                # list with simple type replace the schema with only one item
                            elif isinstance(value, list) and len(value) > 0 :   
                                nested_schema = PandasSchema(root=schema)
                                col_schema = PandasColumn(
                                name="#value",
                                dtype=f"Array[{convert_numpy_type_to_python(value[0])}]",
                                nullable=False,
                                count=1,
                                nested=None
                                )
                                nested_schema.root.append(col_schema)                    
                        schema.append(col_schema)
                    # If it's an array-like Series, break after first column and return inner nested object of first row
                        if isinstance(data.index, pd.RangeIndex) and data.index.start == 0 and nested_schema and len(nested_schema.root)>0:
                            schema = nested_schema.root
                            break
            else:
                # Series vide
                col_schema = PandasColumn(
                    name=array_item_tag,
                    dtype=str(data.dtype),
                    nullable=True,
                    count=0,
                    nested=None
                )
                schema.append(col_schema)
    
    # Handle dictionary
    elif isinstance(data, dict):
        for key, value in data.items():
            key_name = str(key)
            
            # Determine type and nullable properties based on the value
            value_type = convert_numpy_type_to_python(value)
            
            col_schema = PandasColumn(
                name=key_name,
                dtype=value_type,
                nullable=value is None,
                count=0 if value is None else 1,
                nested=None
            )
            
            # Recursive handling of nested structures
            if isinstance(value, (pd.Series, pd.DataFrame, dict)):
                nested_schema = generate_pandas_schema(value)
                col_schema.nested = nested_schema.root
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                nested_schema = generate_pandas_schema(value[0])
                col_schema.nested = nested_schema.root
                
            schema.append(col_schema)
    
    return PandasSchema(root=schema)


def slice_generator(df, chunk_size=1000):
    current_row = 0
    total_rows = df.shape[0]
    while current_row < total_rows:
        yield df[current_row:current_row + chunk_size]
        current_row += chunk_size


def decodeDictionary(dictionary):
    if type(dictionary) == dict:
        for key in dictionary.keys():
            dictionary[key] = decodeDictionary(dictionary[key])
    elif type(dictionary) == bytes:
        dictionary = dictionary.decode('ISO-8859-1') 
    return dictionary

def resolve_file_name(filename: str, expected_ext: str) -> str:
        """
        Ensures the filename ends with the correct extension.
        - Adds the extension if it's missing.
        - Replaces the extension if it's different from the expected one.
        - Returns the filename as-is if the extension matches.
        
        Args:
            filename (str): The original file name.
            expected_ext (str): The desired extension (without dot), e.g. 'csv', 'json'.
        
        Returns:
            str: The corrected filename with the expected extension.
            
        Raises:
            ValueError: If the file extension is not allowed by security validator.
        """
        expected_ext = expected_ext.lower()
        base, ext = os.path.splitext(filename)
        ext = ext.lstrip(".").lower()
        
        # Determine the final filename
        if not ext:
            final_filename = f"{filename}.{expected_ext}"
        elif ext != expected_ext:
            final_filename = f"{base}.{expected_ext}"
        else:
            final_filename = filename
        
        # Validate the final filename for security
        if not PathSecurityValidator.validate_file_extension(final_filename):
            raise ValueError(f"File extension '{expected_ext}' is not allowed for security reasons")
        
        return final_filename

def filter_data_with_duckdb(filepath: str, select: Optional[str] = None, where: Optional[str] = None) -> dict:
    """
    Filter JSON data using DuckDB with optional SELECT and WHERE clauses
    
    Args:
        filepath: path to the JSON file
        select: Columns to select (comma separated)
        where: WHERE clause conditions
    
    Returns:
        Filtered data as list of dictionaries
    """
    try:
        # Read and return the output file
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not (select or where):
            return data
            
        # Convert JSON data to DuckDB table
        # Convert JSON data to DuckDB table
        con = duckdb.connect(":memory:")
        
        con.execute("CREATE TABLE temp_data AS SELECT * FROM read_json(?)", [filepath])
        
        # Construct SQL query
        query = "SELECT "
        query += select if select else "*"
        query += " FROM temp_data"
        if where:
            query += f" WHERE {where}"
        
        # Execute query and fetch results
        result = con.execute(query).fetchall()
        column_names = con.execute("SELECT * FROM temp_data LIMIT 0").description
        
        # Convert results to dict format
        filtered_data = [
            {column_names[i][0]: value for i, value in enumerate(row)}
            for row in result
        ]

        # Close the connection
        con.close()
        return filtered_data
        
    except Exception as e:
        logger.error(f"Error filtering data with DuckDB: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error filtering data: {str(e)}")