import base64
from datetime import timedelta
import json
import os
from pathlib import Path
import re
import time
import traceback
from fastapi import APIRouter, BackgroundTasks, Header, status, Request, Response , HTTPException
from app.models.interface.dataset_interface import *
import requests
import logging
import httpx
import asyncio
import pyarrow as pa
import pyarrow.parquet as pq
import xml.etree.ElementTree as ET

from app.models.interface.pdc_chain_interface import PdcChainHeaders, PdcChainRequest, PdcChainResponse
from app.models.interface.pdc_interface import PdcContract, PdcEcosystem, PdcParticipant, PdcServiceOffering, PdcContractBilateral, PdcDataResource
from app.models.interface.pdc_data_exchange_interface import PdcDataExchangeHeaders
from app.models.interface.workflow_interface import IProject
from app.routes.workflows import import_and_execute_workflow
from app.services.dataset_service import DatasetService
from app.services.pdc_service import PdcService
from typing import Annotated, List, Optional

logger = logging.getLogger(__name__)

from app.services.workflow_service import WorkflowService
from app.utils.utils import decodeDictionary

router = APIRouter(prefix="/ptx", tags=["prometheus-x"])

logging.basicConfig(filename = 'app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

dataset_service = DatasetService()
workflow_service = WorkflowService()
pdc_service = PdcService()

_config_cache = {}
_config_timestamp = {}

@router.get("/{id}")
async def get_ptx_data(id: str):
    connection = await dataset_service.get_dataset(id)
    config = get_private_configuration(connection)
    catalog_uri = config.get("catalogUri")
    pdc_data = pdc_get_request(connection, "/")

    async def fetch_catalog_item(client: httpx.AsyncClient, content: dict):
        response = await client.get(content["@id"])
        res = response.json()
        participant_id = None
        owner_name = "Unknown"
        owner_logo = None

        if content["@type"] in ["ptx:serviceofferings", "ptx:softwareresources"]:
            participant_id = res.get("providedBy")
        elif content["@type"] == "ptx:dataresources":
            participant_id = res.get("producedBy")

        if participant_id and catalog_uri:
            try:
                participant_response = await client.get(f"{catalog_uri}participants/{participant_id}")
                participant = participant_response.json()
                owner_name = participant.get("legalName")
                owner_logo = participant.get("logo")
            except Exception:
                pass

        return {
            "type": content["@type"],
            "name": res["name"],
            "owner": {
                "name": owner_name,
                "logo": owner_logo
            }
        }

    catalog = []
    if "content" in pdc_data and "ptx:catalog" in pdc_data["content"]:
        async with httpx.AsyncClient() as client:
            tasks = [fetch_catalog_item(client, content) 
                    for content in pdc_data["content"]["ptx:catalog"]]
            catalog = await asyncio.gather(*tasks)

    return {"catalog": catalog}

@router.put("/dataResources/{connection_id}")
async def update_data_resource(connection_id: str, request: Request):
    """
    Update a data resource in a PDC connection.
    """
    try:
        connection = await dataset_service.get_dataset(connection_id)
        if (not isinstance (connection,PTXDataset)):
            raise HTTPException(status_code=400, detail="Invalid connection type. Expected PTXDataset.")

        config = get_private_configuration(connection)
        
        body = await request.json()
        dataResourcesId = body.get("dataResourceId")
        newUrl = body.get("newUrl")

        headers = {
            'Authorization': f'Bearer {connection.token}',
            'Content-Type': 'application/json'
        }

        dataResource_url = f"{config.get('catalogUri')}dataresources/{dataResourcesId}"
        dataResources = pdc_service.fetch_dataResource(dataResource_url, headers)
        representation = dataResources.representation
        representation.url = newUrl

        payload = representation.model_dump_json()

        api_url = f"{config.get('catalogUri')}datarepresentations/{representation.id}"
        async with httpx.AsyncClient() as client:
            response = await client.put(api_url, data=payload, headers=headers)
            if response.status_code == 200:
                return {
                    "response": response.json()
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Url update failed: {response.text}"
            )
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/dataResources/{connection_id}")
async def get_data_resources(connection_id: str):
    """
    Get data resources from a PDC connection.
    """
    try:
        connection = await dataset_service.get_dataset(connection_id)
        pdc_data = pdc_get_request(connection, "/")
        
        data_resources = []
        if "content" in pdc_data and "ptx:catalog" in pdc_data["content"]:
            for content in pdc_data["content"]["ptx:catalog"]:
                if content["@type"] == "ptx:dataresources":
                    res = requests.get(content["@id"]).json()
                    data = PdcDataResource.model_validate(res)
                    data_resources.append(data)
        
        return {"dataResources": data_resources}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/executeChainService", status_code=status.HTTP_200_OK)
async def executeChainService(
    background_tasks: BackgroundTasks,
    payload: PdcChainRequest,
    request: Request,
    x_ptx_service_chain_id: Annotated[str | None, Header(alias="x-ptx-service-chain-id")] = None,
    x_ptx_target_id: Annotated[str | None, Header(alias="x-ptx-target-id")] = None,
    Authorization: Annotated[str, Header()] = None,
):  
    requestjson = await request.json()
    service_chain_id = re.search(r"@supervisor:([a-f0-9]{24})", x_ptx_service_chain_id).group(1)
    pdc_service.store_servicechain_data(
        service_chain_id=service_chain_id,
        data=payload.data
    )
    pdc_headers = PdcChainHeaders(
        Authorization=Authorization if Authorization is not None else "",
        x_ptx_service_chain_id=x_ptx_service_chain_id,
        x_ptx_target_id=x_ptx_target_id,
    )
    logger.info(f"requestjson {pdc_service.get_servicechain_data(service_chain_id)}...")

    dataset_service.pdcChainData = payload.data
    print(requestjson)
    dataset_service.pdcChainHeaders = pdc_headers
    workflow_data = await workflow_service.get_workflow(payload.params["workflowId"] if "workflowId" in payload.params else "e492c405-300f-4bf3-967e-c3db614e18f6")
    print(type(workflow_data))
    background_tasks.add_task(import_and_execute_workflow, workflow_data)
    return True

@router.get("/serviceChain/data/{service_chain_id}")
async def get_servicechain_data(service_chain_id: str):
    """retrieve service chain data by its ID"""
    return pdc_service.get_servicechain_data(service_chain_id)


@router.delete("/serviceChain/data/remove/{service_chain_id}")
async def delete_service_chain_data(service_chain_id: str):
    """delete service chain data  in pdc_service"""
    status =  pdc_service.delete_servicechain_data(service_chain_id)
    if status:
        logger.info(f"{service_chain_id} deleted in pdc service")
        return True
    return False

@router.post("/pdcInput")
async def read_input(request: Request, response: Response, headers: Annotated[PdcDataExchangeHeaders, Header()]):
    """ pdc input endpoint to handle PDC data exchange.
    This endpoint processes the input data and headers, fetches the PDC contract,
    retrieves the data provider or ecosystem information, and writes the data to a file.
    """
    fileFormat ="text"
    if (request.headers.get("Content-Type") == "application/json"):
        try:
            data = await request.json()
            fileFormat ="json"
        except : 
            data = await request.body()
    elif (request.headers.get("Content-Type") == "application/x-www-form-urlencoded"):
        try:
            data = await request.form()
            data = dict(data)
            fileFormat ="xml"
        except : 
            data = await request.body()
    else:
        data = await request.body()
    data = decodeDictionary(data)
    #print(f"Received data: {data}")
    
    # Fetch PDC Contract and extract provider name using the service
    pdc_contract = pdc_service.fetch_contract(headers.x_ptx_contracturl)
    provider_name = pdc_service.get_provider_name_from_contract(pdc_contract)
    print(f"Provider name: {provider_name}")
    os.makedirs(os.path.dirname(get_folder_path("pdc")), exist_ok=True)
    connection = await dataset_service.find_file_connection(
        folder=get_folder_path("pdc"),
        name=f"{provider_name}_{pdc_contract.id}" if provider_name else str(pdc_contract.id)
    )
    payload = {"data": data, "path": "pdc"}
    
    serialized_data = serialize_data(data, fileFormat)
    file_ext = ".json" if fileFormat == "json" else ".xml" if fileFormat == "xml" else ".txt"

    if connection.ifExist == "append" and connection.filePath and os.path.exists(connection.filePath):
        complete_filepath = connection.filePath
        print(f" before Appending to existing file: {complete_filepath}")
        write_input_append(complete_filepath, serialized_data)
        print(f"Appended data to existing file: {complete_filepath}")
    else:
        filename_prefix = f"{provider_name}_{pdc_contract.id}_" if provider_name else "{pdc_contract.id}_"
        folder_path = connection.folder if connection.folder else get_folder_path("pdc")
        complete_filepath = f"{folder_path}{filename_prefix}{str(time.time())}{file_ext}"
        if connection.filePath and os.path.exists(connection.filePath):
            try:
                os.remove(connection.filePath)
                print(f"Removed old file: {connection.filePath}")
            except OSError as e:
                print(f"Error removing old file {connection.filePath}: {e}")
        write_input(complete_filepath, serialized_data)
        connection.filePath = complete_filepath
        connection.ifExist = "replace"
        print(f"Created new file: {complete_filepath}")
    
    connection.inputType = "file"
    await dataset_service.edit_dataset(connection)
   
    return {"data": payload, "path": "my pdc"}

@router.get("/participants_id/{connection_id}")
async def get_participants_id_from_connection(connection_id: str) -> List[str]:
    """
    Extract unique participants from a connection's catalog
    """
    connection = await dataset_service.get_dataset(connection_id)
    pdc_data = pdc_get_request(connection, "/")
    participants_id = set()

    if "content" in pdc_data and "ptx:catalog" in pdc_data["content"]:
        async with httpx.AsyncClient() as client:
            tasks = [fetch_participant_id(client, content) 
                    for content in pdc_data["content"]["ptx:catalog"]]
            results = await asyncio.gather(*tasks)
            participants_id.update(pid for pid in results if pid)

        if participants_id:
            return list(participants_id)

async def fetch_participant_id(client: httpx.AsyncClient, content: dict) -> Optional[str]:
    """Fetch participant ID from content URL"""
    try:
        response = await client.get(content["@id"])
        if response.status_code == 200:
            res = response.json()
            
            if content["@type"] in ["ptx:serviceofferings", "ptx:softwareresources"]:
                return res.get("providedBy")
            elif content["@type"] == "ptx:dataresources":
                return res.get("producedBy")
                
    except Exception as e:
        print(f"Error fetching {content['@id']}: {e}")
    return None

@router.get("/contracts/use-case/{connection_id}")
async def get_use_case_contract(connection_id: str, hasSigned:Optional[bool] = None):
    #URI pointing to your participant in the catalog, encode it in base64
    connection = await dataset_service.get_dataset(connection_id)
    config = get_private_configuration(connection)
    catalog_uri = config.get("catalogUri")
    contract_uri = config.get("contractUri")
    participants_id = await get_participants_id_from_connection(connection_id)

    all_use_case_contracts = []
    
    # create a new async client for making requests
    async with httpx.AsyncClient() as client:
        for participant_id in participants_id:
            participant_url = f"{catalog_uri}catalog/participants/{participant_id}"
            encoded_url = b64_encode(participant_url)
            contract_url = f"{contract_uri}contracts/for/{encoded_url}"
            
            params = {}
            if hasSigned is not None:
                params["hasSigned"] = "true" if hasSigned else "false"

            # use the async client to fetch contracts
            response = await client.get(contract_url, params=params)

            if response.status_code == 200:
                contracts_data = response.json()
                for contract in contracts_data.get("contracts"):
                    try:
                        contract = PdcContract.model_validate(contract)
                        
                        # Fetch ecosystem
                        ecosystem = await pdc_service.fetch_ecosystem_async(client, contract.ecosystem) if contract.ecosystem else None
                        
                        if participant_id == ecosystem.orchestrator:
                            contract.name = ecosystem.name
                            
                            # Fetch orchestrator
                            if contract.orchestrator:
                                orchestrator = await pdc_service.fetch_participant_async(client, contract.orchestrator)
                                contract.logo = orchestrator.get("logo", "") if orchestrator else ""
                            
                            all_use_case_contracts.append(contract)

                            signed_participants = {
                                invitation.get("participant") 
                                for invitation in ecosystem.invitations 
                                if invitation.get("status") == "Signed"
                            }

                            # Fetch all service offerings in parallel for data providers
                            data_provider_tasks = []
                            for participant in ecosystem.participants:
                                has_data_provider_role = (
                                    not participant.roles or 
                                    "Data provider for Organisational Data" in participant.roles or
                                    "https://registry.visionstrust.com/static/references/roles/dataProviderForOrganisationalData.json" in participant.roles
                                )
                                if (participant.participant in signed_participants and 
                                    participant_id != participant.participant and 
                                    has_data_provider_role):
                                    for service in participant.offerings:
                                        url = f"{catalog_uri}catalog/serviceofferings/{service.serviceOffering}"
                                        data_provider_tasks.append(pdc_service.fetch_service_offering_async(client, url))

                            data_provider_services = await asyncio.gather(*data_provider_tasks)
                            contract.dataProviders.extend([
                                service for service in data_provider_services 
                                if service and service.dataResources and len(service.dataResources) > 0
                            ])

                            # Fetch all service offerings in parallel for purposes
                            purpose_tasks = []
                            for participant in ecosystem.participants:
                                if participant_id == participant.participant:
                                    for service in participant.offerings:
                                        url = f"{catalog_uri}catalog/serviceofferings/{service.serviceOffering}"
                                        purpose_tasks.append(pdc_service.fetch_service_offering_async(client, url))

                            purpose_services = await asyncio.gather(*purpose_tasks)
                            contract.purposes.extend([
                                service for service in purpose_services 
                                if service and service.softwareResources and len(service.softwareResources) > 0
                            ])

                    except Exception as e:
                        logger.error(f"Error processing contract data: {str(e)}")
                        traceback.print_exc()
            else:
                print("Failed to get bilateral contracts for participants")

    return all_use_case_contracts

@router.get("/serviceChain/{connection_id}")
async def get_service_Chain(connection_id: str):
    connection = await dataset_service.get_dataset(connection_id)
    config = get_private_configuration(connection)
    catalog_uri = config.get("catalogUri")
    contract_uri = config.get("contractUri")
    participants_id = await get_participants_id_from_connection(connection_id)
    
    result = []
    for participant_id in participants_id:
        participant_url = f"{catalog_uri}catalog/participants/{participant_id}"
        encoded_url = b64_encode(participant_url)
        contract_url = f"{contract_uri}/contracts/for/{encoded_url}"

        response = requests.get(contract_url)

        if response.status_code == 200:
            contracts_data = response.json()
            for contract in contracts_data.get("contracts"):
                try:
                    contract = PdcContract.model_validate(contract)
                    ecosystem = pdc_service.fetch_ecosystem(contract.ecosystem) if contract.ecosystem else None
                    if participant_id == ecosystem.orchestrator	: 
                        result.append({
                            "contract_id": contract.id,
                            "service_chains": ecosystem.serviceChains
                        })

                except Exception as e:
                    print(f"Error processing contract data: {e}")
                    traceback.print_exc()
        else:
            print("Failed to get bilateral contracts for participants")

    return result

@router.post("/trigger-data-exchange/{connection_id}")
async def trigger_data_exchange(connection_id: str, request: Request):
    try:
        connection = await dataset_service.get_dataset(connection_id)
        
        config = get_private_configuration(connection)
        pdc_endpoint = config.get("endpoint")
        contract_uri = config.get("contractUri")
        
        body = await request.json()
        contract_id = body.get("contract")
        

        contract_url = f"{contract_uri}contracts/{contract_id}"
        
        payload = {
            "contract": contract_url,
            "purposeId": body.get("purposeId"),
            "resourceId": body.get("resourceId"),
        }
        
        exchange_url = f"{pdc_endpoint}exchange"
        headers = {
            'Authorization': f'Bearer {connection.token}',
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(exchange_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            return {
                "success": True,
                "response": response.json()
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Data exchange failed: {response.text}"
            )
            
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/triggerServiceChain/{connection_id}")
async def trigger_service_chain(connection_id: str, request: Request):
    try:
        connection = await dataset_service.get_dataset(connection_id)
        
        config = get_private_configuration(connection)
        pdc_endpoint = config.get("endpoint")
        contract_uri = config.get("contractUri")
        
        body = await request.json()
        contract_id = body.get("contractId")
        

        contract_url = f"{contract_uri}contracts/{contract_id}"
        
        payload = {
            "contract": contract_url,
            "serviceChainId": body.get("serviceChainId")
        }
        
        exchange_url = f"{pdc_endpoint}exchange"
        headers = {
            'Authorization': f'Bearer {connection.token}',
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(exchange_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            return {
                "success": True,
                "response": response.json()
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Data exchange failed: {response.text}"
            )
            
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/contracts/bilaterals/{connection_id}")
async def get_billateral_contract(connection_id: str):
    #URI pointing to your participant in the catalog, encode it in base64
    try:
        connection = await dataset_service.get_dataset(connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding connection: {str(e)}")
    
    try:
        config = get_private_configuration(connection)
        catalog_uri = config.get("catalogUri")
        contract_uri = config.get("contractUri")
        endpoint = config.get("endpoint")
        if not catalog_uri or not contract_uri:
            raise ValueError("Missing catalogUri or contractUri in config")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading private configuration: {str(e)}")
    
    try:
        participants_id = await get_participants_id_from_connection(connection_id)
        if not participants_id:
            raise ValueError("No participants found for this connection")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving participants: {str(e)}")

    all_bilateral_contracts = []
    for participant_id in participants_id:
        participant_url = f"{catalog_uri}catalog/participants/{participant_id}"
        encoded_url = b64_encode(participant_url)
        bilateral_url = f"{contract_uri}/bilaterals/for/{encoded_url}"

        response = requests.get(bilateral_url)

        if response.status_code == 200:
            contracts_data = response.json()

            for contract in contracts_data.get("contracts"):
                try:
                    contract = PdcContractBilateral.model_validate(contract)
                    contract_info = pdc_service.get_provider_name_and_img_from_contract(contract)
                    contract.name = contract_info.get("name") if contract_info.get("name") else "Unknown"
                    contract.img = contract_info.get("img") if contract_info.get("img") else ""
                    all_bilateral_contracts.append(contract)
                except Exception as e:
                    print(f"Error processing contract data: {e}")
        else:
            print("Failed to get bilateral contracts for participants")

    return {
        "contracts": all_bilateral_contracts,
        "endpoint": endpoint,
        "contractUri": contract_uri
    }

def b64_encode(url: str):
    encoded_url = base64.b64encode(url.encode('utf-8')).decode('utf-8')
    return encoded_url

def pdc_get_request(connection: Dataset, url):
    r = requests.get(connection.url + url, headers={
        "Authorization": "Bearer " + connection.token
    })
    if 'json' in r.headers['Content-Type']:
        res = r.json()
    else:
        res = r.content
    return res

def write_input_append(file: str, data: str):
    """Append data to existing file with proper JSON merging."""
    try:
        
        new_data = json.loads(data)
        
        if os.path.exists(file):
            print(f"Appending data to file: {file}")
            # Read existing data
            with open(file, 'r') as f:
                content = f.read().strip()
            
            if content:
                # Parse existing JSON
                existing_data = json.loads(content)
                print(f"Existing data type: {type(existing_data)}")
                print(f"New data type: {type(new_data)}")

                if isinstance(existing_data, list) and not isinstance(new_data, list):
                    print("Merging existing list with new data")
                    merged_data = existing_data + [new_data]

                elif not isinstance(existing_data, list) and not isinstance(new_data, list):
                    print("Merging existing data with new data")
                    merged_data = [existing_data, new_data]

                elif isinstance(existing_data, list) and isinstance(new_data, list):
                    print("Merging two lists")
                    merged_data = existing_data + new_data    

                else:
                    print("Merging existing data with new data")
                    merged_data = [existing_data] + new_data
                with open(file, 'w') as f:
                    f.write(json.dumps(merged_data, indent=2))
            else:
                with open(file, 'w') as f:
                    f.write(json.dumps(new_data, indent=2))
        else:
            print(f"Creating new file: {file}")
            # Create new file
            with open(file, 'w') as f:
                f.write(json.dumps(new_data, indent=2))
                
    except json.JSONDecodeError:
        # If not valid JSON, append as tezzzxt
        with open(file, 'a') as f:
            f.write('\n' + data)

def write_input(file: str, data: str):
    """ Write data to file (overwrite).
    """
    with open(file, 'w') as f:
        f.write(data)

def get_folder_path(folder: str):
    """ build absolute path of a folder.
    """
    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    return str(dir_path.parent.absolute()) + "/ptx/"+folder+"/"    

def get_private_configuration(connection):
    """Get private configuration with caching"""
    cache_key = f"{connection.id}"
    
    # check if the configuration is already cached and not expired
    now = datetime.now()
    if (cache_key in _config_cache and 
        cache_key in _config_timestamp and
        now - _config_timestamp[cache_key] < timedelta(minutes=5)):
        return _config_cache[cache_key]
    
    # if not cached, fetch the configuration
    res = pdc_get_request(connection, "/private/configuration/")
    if "content" in res:
        config = {
            "endpoint": res["content"].get("endpoint"),
            "catalogUri": res["content"].get("catalogUri"),
            "contractUri": res["content"].get("contractUri"),
            "consentUri": res["content"].get("consentUri"),
        }
        # store in cache
        _config_cache[cache_key] = config
        _config_timestamp[cache_key] = now
        return config
    else:
        raise ValueError("Error retrieving configuration")

def get_serviceoffering_by_id(id: str, connection):
    conf = get_private_configuration(connection)
    url = conf["catalogUri"] + "catalog/serviceofferings/" + id
    return pdc_service.fetch_service_offering(url)

def serialize_data(data, fileFormat):
    if fileFormat == "json":
        return json.dumps(data, indent=2)
    elif fileFormat == "xml":
        # if XML string return or convert
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            # Simple dict to XML conversion
            root = ET.Element("root")
            for k, v in data.items():
                child = ET.SubElement(root, k)
                child.text = str(v)
            return ET.tostring(root, encoding="unicode")
        else:
            return str(data)
    else:
        # raw text
        return data.decode() if isinstance(data, bytes) else str(data)
