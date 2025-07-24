import aiohttp
import requests
from typing import Any, Dict, Optional
from fastapi import HTTPException

from app.models.interface.pdc_interface import (
    PdcContract, 
    PdcEcosystem, 
    PdcParticipant, 
    PdcServiceOffering,
    PdcContractBilateral,
    PdcDataResource
)
from app.utils.singleton import SingletonMeta


class PdcService(metaclass=SingletonMeta):
    """Service for handling PDC (Prometheus Data Connector) API requests"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.default_headers = {
            "Accept": "application/json",
            "User-Agent": "PDC-Service/1.0"
        }
        self._servicechain_storage: Dict[str, Dict[str, Any]] = {}
    
    def _make_request(self, url: str, headers: Optional[dict] = None) -> dict:
        """Make a GET request to PDC API with error handling"""
        request_headers = {**self.default_headers}
        if headers:
            request_headers.update(headers)
            
        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers=request_headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch data from {url}: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing data from {url}: {str(e)}"
            )
    
    def fetch_dataResource(self, dataResource_url: str, headers: Optional[dict] = None ) -> PdcDataResource:
        """Fetch PDC DataResources from the given URL"""
        data = self._make_request(dataResource_url, headers )
        return PdcDataResource.model_validate(data)
    
    def fetch_contract(self, contract_url: str) -> PdcContract:
        """Fetch PDC Contract from the given URL"""
        data = self._make_request(contract_url)
        return PdcContract.model_validate(data)
    
    def fetch_contract_bilateral(self, contract_url: str) -> PdcContractBilateral:
        """Fetch PDC Contract from the given URL"""
        data = self._make_request(contract_url)
        return PdcContractBilateral.model_validate(data)
    
    def fetch_participant(self, participant_url: str) -> PdcParticipant:
        """Fetch PDC Participant from the given URL"""
        data = self._make_request(participant_url)
        return PdcParticipant.model_validate(data)
    
    def fetch_ecosystem(self, ecosystem_url: str) -> PdcEcosystem:
        """Fetch PDC Ecosystem from the given URL"""
        data = self._make_request(ecosystem_url)
        return PdcEcosystem.model_validate(data)
    
    def fetch_service_offering(self, service_offering_url: str) -> PdcServiceOffering:
        """Fetch PDC Service Offering from the given URL"""
        data = self._make_request(service_offering_url)
        return PdcServiceOffering.model_validate(data)
    
    def get_ecosystem_name_from_contract(self, contract: PdcContract) -> Optional[str]:
        """Extract ecosystem name from PDC contract"""
        if contract.ecosystem:
            ecosystem = self.fetch_ecosystem(contract.ecosystem)
            return ecosystem.name
        return None
    
    def get_provider_name_from_contract(self, contract: PdcContract) -> Optional[str]:
        """Extract provider name from PDC contract following priority order"""
        if contract.purpose and len(contract.purpose) > 0:
            service_offering = self.fetch_service_offering(contract.purpose[0]['purpose'])
            return service_offering.name
        elif contract.dataProvider:
            data_provider = self.fetch_participant(contract.dataProvider)
            return data_provider.legalName
        elif contract.ecosystem:
            ecosystem = self.fetch_ecosystem(contract.ecosystem)
            return ecosystem.name
        return None
    
    def get_provider_name_and_img_from_contract(self, contract: PdcContractBilateral) -> Optional[str]:
        """Extract provider name from PDC contract following priority order"""
        if contract.purpose and len(contract.purpose) > 0:
            service_offering = self.fetch_service_offering(contract.purpose[0]['purpose'])
            return {
                "name": service_offering.name,
                "img": service_offering.image
            }
        
        elif contract.dataProvider:
            data_provider = self.fetch_participant(contract.dataProvider)
            return { 
                "name": data_provider.legalName,
                "img": data_provider.logo
            }
        elif contract.ecosystem:
            ecosystem = self.fetch_ecosystem(contract.ecosystem)
            return {
                "name": ecosystem.name,
                "img": ecosystem.logo
            }
        return None

    def store_servicechain_data(self, service_chain_id: str, data: Dict[str, Any]) -> bool:
        """save service chain data"""
        self._servicechain_storage[service_chain_id] = {
            "service_chain_id": service_chain_id,
            "data": data,
        }
        return True
    
    def get_servicechain_data(self, service_chain_id: str):
        """get service chain data"""
        if service_chain_id in self._servicechain_storage:
            return self._servicechain_storage.get(service_chain_id)
    
    def delete_servicechain_data(self, service_chain_id: str) -> bool:
        """delete service chain data by its ID"""
        if service_chain_id in self._servicechain_storage:
            del self._servicechain_storage[service_chain_id]
            return True
        return False
    

    async def fetch_service_offering_async(self, session: aiohttp.ClientSession, url: str):
        """Fetch service offering asynchronously"""
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return PdcServiceOffering.model_validate(data)
        return None

    async def fetch_ecosystem_async(self, session: aiohttp.ClientSession, url: str):
        """Fetch ecosystem asynchronously"""
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return PdcEcosystem.model_validate(data)
        return None

    async def fetch_participant_async(self, session: aiohttp.ClientSession, url: str):
        """Fetch participant asynchronously"""
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
        return None