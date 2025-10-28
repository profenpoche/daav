from typing import Annotated, Any, Dict, List, Literal, Optional, Union
from bson import ObjectId
from pydantic import BaseModel, Field, model_serializer, ConfigDict
from beanie import Document, PydanticObjectId, UnionDoc, before_event, Insert 
from datetime import datetime
from app.enums.type_connection import TypeConnection
from fastapi_pagination import LimitOffsetPage

class DatasetMetadata(BaseModel):
    fileSize: Optional[str] = None
    fileType: Optional[str] = None
    modifTime: Optional[str] = None
    accessTime: Optional[str] = None
    columnCount: Optional[str] = None
    rowCount: Optional[str] = None

class Dataset(Document):
    id: Optional[str] = Field(default=None, alias="_id")
    name: Optional[str] = None
    type: Literal['mysql','mongo','elastic','file','api', 'ptx'] = None
    metadata: Optional[DatasetMetadata] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # User ownership and sharing
    owner_id: Optional[str] = Field(default=None, description="ID of the user who owns this dataset")
    shared_with: List[str] = Field(default_factory=list, description="List of user IDs this dataset is shared with")
    
    @before_event(Insert)
    async def generate_string_id(self):
        """Générer un ID string avant l'insertion"""
        if not self.id:
            self.id = str(ObjectId())
    
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True
    )
    
    class Settings:
        name = "datasets"
        use_state_management = True
        indexes = [
            [("type", 1)],
            [("name", 1)],
            [("created_at", -1)],
            [("owner_id", 1)]
        ]
    
    @model_serializer(mode='wrap')
    def serialize_model(self, serializer, info) -> Dict[str, Any]:
        data = serializer(self)
        if '_id' in data:
            data['id'] = str(data.pop('_id'))
        elif 'id' in data and data['id']:
            data['id'] = str(data['id'])
        return data

class MysqlDataset(Dataset):
    type: Literal['mysql']
    host: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    table: Optional[str] = None

class MongoDataset(Dataset):
    type: Literal['mongo']
    uri: Optional[str] = None
    database: Optional[str] = None
    collection: Optional[str] = None

class ElasticDataset(Dataset):
    type: Literal['elastic']
    url: Optional[str] = None
    user: Optional[str] = None
    key: Optional[str] = None
    bearerToken: Optional[str] = None
    password: Optional[str] = None
    index: Optional[str] = None

class PTXDataset(Dataset):
    type: Literal['ptx']
    url: Optional[str] = None
    token: Optional[str] = None
    refreshToken: Optional[str] = None
    service_key: Optional[str] = None
    secret_key: Optional[str] = None

class FileDataset(Dataset):
    type: Literal['file']
    filePath: Optional[str] = None
    folder: Optional[str] = None
    inputType: Optional[str] = None
    csvHeader: Optional[str] = None
    csvDelimiter: Optional[str] = None
    ifExist: Optional[str] = None

class ApiDataset(Dataset):
    type: Literal['api']
    apiAuth: Optional[str] = None
    url: Optional[str] = None
    authUrl: Optional[str] = None
    bearerToken: Optional[str] = None
    basicToken: Optional[str] = None
    clientId: Optional[str] = None
    clientSecret: Optional[str] = None

DatasetUnion = Annotated[
    Union[MysqlDataset, MongoDataset, ElasticDataset, PTXDataset, FileDataset, ApiDataset],
    Field(discriminator='type')
]    

class Pagination(BaseModel):
    page: Optional[int] = None
    perPage: Optional[int] = None
    nextUrl: Optional[str] = None
    
class DatasetParams(BaseModel):
    database: Optional[str] = None
    table: Optional[str] = None

class ConnectionInfo(BaseModel):
    dataset: DatasetUnion
    pagination: Pagination
    datasetParams: DatasetParams 

class BasicContentResponse(BaseModel):
    # data: Optional[List[Dict[str, Any]]] = None
    data: Optional[list | Dict] = None
    total_rows: Optional[int] = None
    limit: Optional[int] = None
    current_page: Optional[int] = None

class MySQLContentResponse(BasicContentResponse):    
    databases: Optional[list] = None
    tables: Optional[list] = None
    table_description: Optional[List[Dict[str, Any]]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "databases": ["db1", "db2", "db3"],
                "tables": ["table1", "table2", "table3"],
                "table_description": [
                    {"Field": "id", "Type": "int(11)", "Null": "NO", "Key": "PRI", "Default": None, "Extra": "auto_increment"},
                    {"Field": "name", "Type": "varchar(255)", "Null": "YES", "Key": "", "Default": None, "Extra": ""}
                ],
                "data": [
                    {"id": 1, "name": "John Doe"},
                    {"id": 2, "name": "Jane Doe"}
                ],
                "total_rows": 2,
                "current_page": 1,
                "limit": 100
            }
        }
    }

class MongoContentResponse(BasicContentResponse):
    databases: Optional[list] = None
    collections: Optional[list] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "databases": ["db1", "db2", "db3"],
                "collections": ["collection1", "collection2", "collection3"],
                "data": [
                    {"id": 1, "name": "John Doe"},
                    {"id": 2, "name": "Jane Doe"}
                ],
                "total_rows": 2,
                "current_page": 1,
                "limit": 100
            }
        }
    }
    
class ElasticContentResponse(BasicContentResponse):
    indices: Optional[list | str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "indices": ["index1", "index2", "index3"],
                "data": [
                    {"id": 1, "name": "John Doe"},
                    {"id": 2, "name": "Jane Doe"}
                ],
                "total_rows": 2,
                "current_page": 1,
                "limit": 100
            }
        }
    }

class FileContentResponse(BasicContentResponse):
    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {"id": 1, "name": "John Doe"},
                    {"id": 2, "name": "Jane Doe"}
                ],
                "total_rows": 2,
                "current_page": 1,
                "limit": 100
            }
        }
    }

class ApiContentResponse(BasicContentResponse):
    next_url: Optional[str] = None
    prev_url: Optional[str] = None
    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {"id": 1, "name": "John Doe"},
                    {"id": 2, "name": "Jane Doe"}
                ],
                "total_rows": 2,
                "current_page": 1,
                "limit": 100,
                "next_url" : "https://api.example.com/items/?page=2"
            }
        }
    }

class PandaContentResponse(BasicContentResponse):
    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {"id": 1, "name": "John Doe"},
                    {"id": 2, "name": "Jane Doe"}
                ],
                "total_rows": 2,
                "current_page": 1,
                "limit": 100
            }
        }
    } 

DatasetContentResponse =  FileContentResponse | MongoContentResponse | MySQLContentResponse | ApiContentResponse | ElasticContentResponse