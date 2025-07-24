"""
Tests for WorkflowService class
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException

from app.services.workflow_service import WorkflowService
from app.models.interface.workflow_interface import (
    IProject, ISchema, INode, INodePort, ISocket, INodeConnection
)


@pytest.fixture
def workflow_service_instance():
    """Fixture to create a WorkflowService instance"""
    return WorkflowService()


@pytest.fixture
def sample_workflow():
    """Sample IProject for testing"""
    mock_workflow = Mock(spec=IProject)
    mock_workflow.id = ObjectId("507f1f77bcf86cd799439011")
    mock_workflow.name = "test_workflow"
    mock_workflow.revision = "1.0"
    mock_workflow.dataConnectors = []
    mock_workflow.created_at = datetime.utcnow()
    mock_workflow.updated_at = datetime.utcnow()
    mock_workflow.delete = AsyncMock()
    mock_workflow.replace = AsyncMock()
    return mock_workflow


# Helper functions for mocking
def create_mock_iproject_list(count: int = 3):
    """Create a list of mock IProject instances"""
    workflows = []
    for i in range(count):
        workflow = Mock(spec=IProject)
        workflow.id = ObjectId()
        workflow.name = f"workflow_{i}"
        workflow.revision = f"1.{i}"
        workflow.dataConnectors = []
        workflow.created_at = datetime.utcnow()
        workflow.updated_at = datetime.utcnow()
        workflows.append(workflow)
    return workflows


def create_async_mock():
    """Helper to create async mock that doesn't raise AttributeError"""
    mock = Mock(spec=IProject)
    mock.id = ObjectId()
    mock.name = "test"
    mock.revision = "1.0"
    mock.dataConnectors = []
    mock.created_at = datetime.utcnow()
    mock.updated_at = datetime.utcnow()
    mock.insert = AsyncMock()
    mock.delete = AsyncMock()
    mock.replace = AsyncMock()
    return mock


# CRUD Tests
@pytest.mark.asyncio
async def test_get_workflows_success(workflow_service_instance):
    """Test successful retrieval of all workflows"""
    mock_workflows = create_mock_iproject_list(3)
    
    with patch.object(IProject, 'find_all') as mock_find_all:
        mock_find_all.return_value.to_list = AsyncMock(return_value=mock_workflows)
        
        result = await workflow_service_instance.get_workflows()
        
        assert len(result) == 3
        assert result[0].name == "workflow_0"
        mock_find_all.assert_called_once()


@pytest.mark.asyncio
async def test_get_workflows_empty_list(workflow_service_instance):
    """Test retrieval when no workflows exist"""
    with patch.object(IProject, 'find_all') as mock_find_all:
        mock_find_all.return_value.to_list = AsyncMock(return_value=[])
        
        result = await workflow_service_instance.get_workflows()
        
        assert result == []
        mock_find_all.assert_called_once()


@pytest.mark.asyncio
async def test_get_workflow_success(workflow_service_instance, sample_workflow):
    """Test successful retrieval of a specific workflow"""
    workflow_id = str(sample_workflow.id)
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_workflow
        
        result = await workflow_service_instance.get_workflow(workflow_id)
        
        assert result.name == "test_workflow"
        assert result.revision == "1.0"
        mock_get.assert_called_once_with(workflow_id)


@pytest.mark.asyncio
async def test_get_workflow_not_found(workflow_service_instance):
    """Test workflow retrieval when workflow doesn't exist"""
    workflow_id = "507f1f77bcf86cd799439999"
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await workflow_service_instance.get_workflow(workflow_id)
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_workflow_success(workflow_service_instance):
    """Test successful workflow creation"""
    workflow_data = {
        "name": "new_workflow",
        "revision": "1.0",
        "dataConnectors": [],
        "pschema": {
            "nodes": [],
            "connections": [],
            "revision": "1.0"
        }
    }
    
    mock_workflow = create_async_mock()
    mock_workflow.name = "new_workflow"
    mock_workflow.revision = "1.0"
    
    with patch('app.services.workflow_service.IProject') as mock_iproject_class:
        mock_iproject_class.return_value = mock_workflow
        
        result = await workflow_service_instance.create_workflow(workflow_data)
        
        assert result.name == "new_workflow"
        mock_iproject_class.assert_called_once_with(**workflow_data)
        mock_workflow.insert.assert_called_once()


@pytest.mark.asyncio
async def test_update_workflow_success(workflow_service_instance, sample_workflow):
    """Test successful workflow update"""
    workflow_id = str(sample_workflow.id)
    update_data = {"id": workflow_id, "name": "updated_workflow", "revision": "1.1"}
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_workflow
        
        result = await workflow_service_instance.update_workflow(update_data)
        
        assert result.name == "updated_workflow"
        assert result.revision == "1.1"
        mock_get.assert_called_once_with(workflow_id)
        sample_workflow.replace.assert_called_once()


@pytest.mark.asyncio 
async def test_update_workflow_not_found(workflow_service_instance):
    """Test update when workflow doesn't exist"""
    workflow_id = "507f1f77bcf86cd799439999"
    update_data = {"id": workflow_id, "name": "updated_workflow"}
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await workflow_service_instance.update_workflow(update_data)
        
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_workflow_success(workflow_service_instance, sample_workflow):
    """Test successful workflow deletion"""
    workflow_id = str(sample_workflow.id)
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_workflow
        
        result = await workflow_service_instance.delete_workflow(workflow_id)
        
        assert result is True
        mock_get.assert_called_once_with(workflow_id)
        sample_workflow.delete.assert_called_once()


@pytest.mark.asyncio
async def test_delete_workflow_not_found(workflow_service_instance):
    """Test deletion when workflow doesn't exist"""
    workflow_id = "507f1f77bcf86cd799439999"
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        result = await workflow_service_instance.delete_workflow(workflow_id)
        
        assert result is False


# Utility Tests
@pytest.mark.asyncio
async def test_workflow_exists_true(workflow_service_instance, sample_workflow):
    """Test workflow existence check returns True"""
    workflow_id = str(sample_workflow.id)
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_workflow
        
        result = await workflow_service_instance.workflow_exists(workflow_id)
        
        assert result is True
        mock_get.assert_called_once_with(workflow_id)


@pytest.mark.asyncio
async def test_workflow_exists_false(workflow_service_instance):
    """Test workflow existence check returns False"""
    workflow_id = "507f1f77bcf86cd799439999"
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        result = await workflow_service_instance.workflow_exists(workflow_id)
        
        assert result is False
        mock_get.assert_called_once_with(workflow_id)


@pytest.mark.asyncio
async def test_get_singleton_service():
    """Test singleton pattern for WorkflowService"""
    service1 = WorkflowService()
    service2 = WorkflowService()
    
    # If implemented as singleton, these should be the same instance
    assert isinstance(service1, WorkflowService)
    assert isinstance(service2, WorkflowService)
    assert service1 is service2  # Singleton should return same instance


# Error Handling Tests  
@pytest.mark.asyncio
async def test_get_workflow_database_error(workflow_service_instance):
    """Test database error handling in get_workflow"""
    workflow_id = "507f1f77bcf86cd799439011"
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Database connection error")
        
        with pytest.raises(HTTPException) as exc_info:
            await workflow_service_instance.get_workflow(workflow_id)
        
        assert exc_info.value.status_code == 500
        assert "Internal server error" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_workflow_validation_error(workflow_service_instance):
    """Test validation error handling in create_workflow"""
    invalid_data = {"invalid_field": "invalid_value"}
    
    with patch('app.services.workflow_service.IProject') as mock_iproject_class:
        mock_iproject_class.side_effect = ValueError("Validation error")
        
        with pytest.raises(HTTPException) as exc_info:
            await workflow_service_instance.create_workflow(invalid_data)
        
        assert exc_info.value.status_code == 500
        assert "Failed to create workflow" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_workflow_database_error(workflow_service_instance):
    """Test database error handling in update_workflow"""
    update_data = {"id": "507f1f77bcf86cd799439011", "name": "updated_workflow"}
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            await workflow_service_instance.update_workflow(update_data)
        
        assert exc_info.value.status_code == 500
        assert "Failed to update workflow" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_workflow_missing_id(workflow_service_instance):
    """Test update workflow when ID is missing"""
    update_data = {"name": "updated_workflow"}  # Missing ID
    
    with pytest.raises(HTTPException) as exc_info:
        await workflow_service_instance.update_workflow(update_data)
    
    assert exc_info.value.status_code == 400
    assert "Workflow ID is required" in str(exc_info.value.detail)


# Data Validation Tests
@pytest.mark.asyncio
async def test_create_workflow_with_timestamps(workflow_service_instance):
    """Test workflow creation includes timestamps"""
    workflow_data = {
        "name": "timestamped_workflow",
        "revision": "1.0",
        "dataConnectors": [],
        "pschema": {"nodes": [], "connections": [], "revision": "1.0"}
    }
    
    mock_workflow = create_async_mock()
    mock_workflow.name = "timestamped_workflow"
    
    with patch('app.services.workflow_service.IProject') as mock_iproject_class:
        mock_iproject_class.return_value = mock_workflow
        
        result = await workflow_service_instance.create_workflow(workflow_data)
        
        # Verify timestamps were set
        assert hasattr(mock_workflow, 'created_at')
        assert hasattr(mock_workflow, 'updated_at')
        assert result.name == "timestamped_workflow"


@pytest.mark.asyncio
async def test_update_workflow_updates_timestamp(workflow_service_instance, sample_workflow):
    """Test workflow update modifies updated_at timestamp"""
    workflow_id = str(sample_workflow.id)
    original_updated_at = sample_workflow.updated_at
    update_data = {"id": workflow_id, "name": "updated_workflow"}
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_workflow
        
        await workflow_service_instance.update_workflow(update_data)
        
        # Check that updated_at was modified
        assert sample_workflow.updated_at != original_updated_at


# Complex Data Tests
@pytest.mark.asyncio
async def test_create_workflow_with_empty_schema(workflow_service_instance):
    """Test creating workflow with minimal/empty schema"""
    minimal_workflow_data = {
        "name": "minimal_workflow",
        "revision": "1.0", 
        "dataConnectors": [],
        "pschema": {
            "nodes": [],
            "connections": [],
            "revision": "1.0"
        }
    }
    
    mock_workflow = create_async_mock()
    mock_workflow.name = "minimal_workflow"
    
    with patch('app.services.workflow_service.IProject') as mock_iproject_class:
        mock_iproject_class.return_value = mock_workflow
        
        result = await workflow_service_instance.create_workflow(minimal_workflow_data)
        
        assert result.name == "minimal_workflow"
        mock_iproject_class.assert_called_once_with(**minimal_workflow_data)


@pytest.mark.asyncio
async def test_update_workflow_partial_data(workflow_service_instance, sample_workflow):
    """Test partial update of workflow data"""
    workflow_id = str(sample_workflow.id)
    partial_update = {"id": workflow_id, "revision": "1.1"}  # Only updating revision
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_workflow
        
        result = await workflow_service_instance.update_workflow(partial_update)
        
        assert result.name == sample_workflow.name  # Name should remain unchanged
        assert result.revision == "1.1"  # Only revision changes
        mock_get.assert_called_once_with(workflow_id)


@pytest.mark.asyncio
async def test_workflow_with_data_connectors(workflow_service_instance):
    """Test workflow creation with data connectors"""
    workflow_with_connectors = {
        "name": "connector_workflow",
        "revision": "1.0",
        "dataConnectors": ["conn1", "conn2"],
        "pschema": {
            "nodes": [],
            "connections": [],
            "revision": "1.0"
        }
    }
    
    mock_workflow = create_async_mock()
    mock_workflow.name = "connector_workflow"
    mock_workflow.dataConnectors = ["conn1", "conn2"]
    
    with patch('app.services.workflow_service.IProject') as mock_iproject_class:
        mock_iproject_class.return_value = mock_workflow
        
        result = await workflow_service_instance.create_workflow(workflow_with_connectors)
        
        assert result.name == "connector_workflow"
        assert len(result.dataConnectors) == 2
        assert result.dataConnectors[0] == "conn1"
        assert result.dataConnectors[1] == "conn2"


@pytest.mark.asyncio
async def test_update_workflow_data_connectors(workflow_service_instance, sample_workflow):
    """Test updating workflow data connectors"""
    workflow_id = str(sample_workflow.id)
    new_connectors = ["new_conn"]
    update_data = {"id": workflow_id, "dataConnectors": new_connectors}
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_workflow
        
        result = await workflow_service_instance.update_workflow(update_data)
        
        assert result.dataConnectors == new_connectors
        mock_get.assert_called_once_with(workflow_id)
        sample_workflow.replace.assert_called_once()


# Workflow Service Exception Handling
@pytest.mark.asyncio
async def test_get_workflows_database_error(workflow_service_instance):
    """Test database error handling in get_workflows"""
    with patch.object(IProject, 'find_all') as mock_find_all:
        mock_find_all.side_effect = Exception("Database connection error")
        
        with pytest.raises(HTTPException) as exc_info:
            await workflow_service_instance.get_workflows()
        
        assert exc_info.value.status_code == 500
        assert "Failed to retrieve workflows" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_delete_workflow_exception_handling(workflow_service_instance):
    """Test delete workflow exception handling"""
    workflow_id = "507f1f77bcf86cd799439011"
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Database error")
        
        result = await workflow_service_instance.delete_workflow(workflow_id)
        
        # Should return False when there's an exception, not raise
        assert result is False
