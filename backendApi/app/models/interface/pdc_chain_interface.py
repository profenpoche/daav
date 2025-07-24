from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel


class EndpointDataProvider(BaseModel):
    id: str
    workflowId: str
    nodeId: str
    authToken: str
    endpoint: str
    method: str
    src:str
    lastUpdated: str

class Participant(BaseModel):
    name: str
    connectorUrl: str
    id: str

class AdditionalDataItem(BaseModel):
    participant: Participant
    params: Dict[str, Any]
    data: Dict[str, Any]

class PdcChainRequestData(BaseModel):
    additionalData: Optional[List[AdditionalDataItem]] = None
    origin: Dict[str, Any]


class PdcChainRequest(BaseModel):
    data: Union[PdcChainRequestData, str, List[Any],Dict[str, Any]]
    contract: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

class PdcChainResponse(BaseModel):
    chainId: str | None
    targetId: str |None
    data: Dict | List | None
    params: Optional[Dict[str, Any]] = None

class PdcChainHeaders(BaseModel):
    Authorization: str
    x_ptx_service_chain_id: str | None = None
    x_ptx_target_id: str | None = None

