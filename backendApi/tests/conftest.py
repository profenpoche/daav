import pytest
import pytest_asyncio
import asyncio
import os
from mongomock_motor import AsyncMongoMockClient
from beanie import init_beanie
from app.models.interface.dataset_interface import (
    Dataset, FileDataset, MongoDataset, MysqlDataset, 
    PTXDataset, ApiDataset, ElasticDataset
)
from app.models.interface.workflow_interface import IProject

_test_database = None

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Setup test database once for all tests."""
    global _test_database
    
    if _test_database is None:
        client = AsyncMongoMockClient()
        _test_database = client.get_database("test_db")
        
        # Initialize Beanie with mock database
        await init_beanie(
            database=_test_database,
            document_models=[
                Dataset,
                FileDataset,
                MongoDataset,
                MysqlDataset,
                PTXDataset,
                ApiDataset,
                ElasticDataset,
                IProject
            ]
        )
    
    yield _test_database

@pytest_asyncio.fixture(autouse=True)
async def clean_collections():
    """Clean all collections before each test."""
    if _test_database is not None:
        # Clean collections
        for model in [Dataset, FileDataset, MongoDataset, MysqlDataset, PTXDataset, ApiDataset, ElasticDataset]:
            try:
                await model.delete_all()
            except Exception:
                pass
    yield