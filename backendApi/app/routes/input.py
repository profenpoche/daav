import json
import os
import time
from pathlib import Path
from typing import Annotated, Dict, List
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Header, Request
import requests

from app.models.interface.pdc_data_exchange_interface import PdcDataExchange, PdcDataExchangeHeaders
from app.models.interface.pdc_interface import PdcContract, PdcParticipant, PdcEcosystem
from app.services.dataset_service import DatasetService
from app.utils.utils import decodeDictionary
from app.utils.security import PathSecurityValidator
router = APIRouter(prefix="/input", tags=["connections"])

dataset_service = DatasetService()

@router.post("/")
async def read_main_input(request: Request, path: str | None = None):
    """ Read the main input posted to https://your_url/input/.
    """
    try:
        data = await request.json()
    except : 
        data = await request.body()
    data = decodeDictionary(data)
    connection = dataset_service.find_file_connection(get_folder_path("main"))
    os.makedirs(os.path.dirname(connection.folder), exist_ok=True)
    payload = {"data": data, "path": "main", "headers": request.headers.items()}
    write_input(connection.folder + str(time.time()), json.dumps(payload))
    return {"ok"}

@router.post("/pdc")
@router.get("/pdc")
async def read_input(request: Request, path: str | None = None):
    try :
        verify_bearer(request)
    except Exception as e:    
        raise HTTPException(
            status_code=401,
            detail= str(e))    
    """ Test for custom treatment of urls. Read the input posted to https://your_url/input/pdc.
    """
    try:
        data = await request.json()
    except : 
        data = await request.body()
    data = decodeDictionary(data)
    connection = dataset_service.find_file_connection(get_folder_path("pdc"))
    os.makedirs(os.path.dirname(connection.folder), exist_ok=True)
    payload = {"data": data, "path": "pdc", "headers": request.headers.items()}
    #print("payload", payload)
    write_input(connection.folder + str(time.time()), json.dumps(payload))
    return {"data": data, "path": "my pdc"}

@router.post("/{path}")
async def read_input(request: Request, path: str | None = None):
    """ Read input posted to https://your_url/input/path
    """
    try:
        data = await request.json()
    except : 
        data = await request.body()
    data = decodeDictionary(data)
    connection = dataset_service.find_file_connection(get_folder_path(path))
    os.makedirs(os.path.dirname(connection.folder), exist_ok=True)
    payload = {"data": data, "path": path, "headers": request.headers.items()}
    print("payload", payload)
    write_input(connection.folder + str(time.time()), json.dumps(payload,skipkeys = True))
    return {"data": data, "path": path}

@router.post("/{path}/{subpath}")
async def read_subpath_input(request: Request, path: str | None = None, subpath: str | None = None):
    """ Read input posted to https://your_url/input/path/subpath.
    """
    try:
        data = await request.json()
    except : 
        data = await request.body()
    data = decodeDictionary(data)
    connection = dataset_service.find_file_connection(get_folder_path(str(path) + "/" + str(subpath)))
    os.makedirs(os.path.dirname(connection.folder), exist_ok=True)
    payload = {"data": data, "path": str(path) + "/" + str(subpath), "headers": request.headers.items()}
    write_input(connection.folder + str(time.time()), json.dumps(payload))
    return {"data": data, "path": str(path) + "/" + str(subpath)}


def get_folder_path(folder: str):
    """ Build absolute path of a folder with security validation.
    """
    try:
        # Security validation to prevent path traversal
        validated_folder = PathSecurityValidator.validate_filename(folder)
        
        # Build secure base path
        dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
        base_path = str(dir_path.parent.absolute()) + "/inputs/"
        
        final_path = base_path + validated_folder + "/"
        
        # Final validation of complete path
        return PathSecurityValidator.validate_file_path(final_path, base_path)
        
    except Exception as e:
        print(f"Security validation failed for folder {folder}: {e}")
        # Return a secure default path in case of error
        dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
        return str(dir_path.parent.absolute()) + "/inputs/safe/"

def write_input(file: str, data: str):
    """Write data to file with security validation."""
    try:
        # File path validation
        validated_file = PathSecurityValidator.validate_file_path(file)
        
        # Check that parent directory exists
        parent_dir = os.path.dirname(validated_file)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        # Data size limitation
        max_data_size = 10 * 1024 * 1024  # 10MB limit
        if len(data.encode('utf-8')) > max_data_size:
            raise ValueError(f"Data too large: {len(data)} bytes (max: {max_data_size})")
        
        # Secure writing
        with open(validated_file, 'w', encoding='utf-8') as f:
            f.write(data)
            
    except Exception as e:
        print(f"Error writing input file {file}: {e}")
        raise

# SECURITY: Move token to environment variables
import os
PDC_TOKEN = os.getenv("PDC_TOKEN", "")
if not PDC_TOKEN:
    import logging
    logging.warning("PDC_TOKEN not found in environment variables - PDC authentication will fail")

def verify_bearer(request):
    try:
        if "Authorization" not in request.headers :
            raise HTTPException(
                        status_code=401, 
                        detail='Authorization header missing')
        token = get_token_auth_header(request.headers["Authorization"])
        if(token != PDC_TOKEN):
            raise HTTPException(
                status_code=401,
                detail= "Invalid token")
    except Exception as e:    
        raise HTTPException(
            status_code=401,
            detail= e.message  if hasattr(e, 'message') else str(e))

def get_token_auth_header(authorization):
    parts = authorization.split()

    if parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401, 
            detail='Authorization header must start with Bearer')
    elif len(parts) == 1:
        raise HTTPException(
            status_code=401, 
            detail='Authorization token not found')
    elif len(parts) > 2:
        raise HTTPException(
            status_code=401, 
            detail='Authorization header be Bearer token')
    
    token = parts[1]
    return token

