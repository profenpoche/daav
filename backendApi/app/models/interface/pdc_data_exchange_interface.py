from typing import Any, Dict, List
from pydantic import BaseModel, Field


class PdcDataExchangeHeaders(BaseModel):
    authorization: str | None = Field(default=None)
    x_ptx_service_chain_id: str | None = Field(default=None)
    x_ptx_target_id: str | None = Field(default=None)
    x_ptx_contracturl: str | None = Field(default=None)
    x_ptx_contractid: str | None = Field(default=None)
    x_ptx_dataexchangeid: str | None = Field(default=None)
    x_ptx_incomingdataspaceconnectoruri: str | None = Field(default=None)


class PdcDataExchange(BaseModel):
    data: str | Dict | List
    contract: str | None
    params: Dict[str, Any] | None
    previousNodeParams: Dict[str, Any]  | None  




