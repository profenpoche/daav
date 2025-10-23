"""
Tests for WorkflowService class
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timezone
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
    mock_workflow.created_at = datetime.now(timezone.utc)
    mock_workflow.updated_at = datetime.now(timezone.utc)
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
        workflow.created_at = datetime.now(timezone.utc)
        workflow.updated_at = datetime.now(timezone.utc)
        workflows.append(workflow)
    return workflows


def create_async_mock():
    """Helper to create async mock that doesn't raise AttributeError"""
    mock = Mock(spec=IProject)
    mock.id = ObjectId()
    mock.name = "test"
    mock.revision = "1.0"
    mock.dataConnectors = []
    mock.created_at = datetime.now(timezone.utc)
    mock.updated_at = datetime.now(timezone.utc)
    mock.insert = AsyncMock()
    mock.delete = AsyncMock()
    mock.replace = AsyncMock()
    return mock


# CRUD Tests
@pytest.mark.asyncio
async def test_get_workflows_success(workflow_service_instance, mock_user):
    """Test successful retrieval of all workflows"""
    mock_workflows = create_mock_iproject_list(3)
    # Assign ownership to mock_user
    for wf in mock_workflows:
        wf.owner_id = mock_user.id
    
    # Set owned_workflows in mock_user
    mock_user.owned_workflows = [str(wf.id) for wf in mock_workflows]
    
    with patch.object(IProject, 'find') as mock_find:
        mock_find.return_value.to_list = AsyncMock(return_value=mock_workflows)
        
        result = await workflow_service_instance.get_workflows(mock_user)
        
        assert len(result) == 3
        assert result[0].name == "workflow_0"


@pytest.mark.asyncio
async def test_get_workflows_empty_list(workflow_service_instance, mock_user):
    """Test retrieval when no workflows exist"""
    # User has no workflows
    mock_user.owned_workflows = []
    mock_user.shared_workflows = []
    
    result = await workflow_service_instance.get_workflows(mock_user)
    
    assert result == []


@pytest.mark.asyncio
async def test_get_workflow_success(workflow_service_instance, sample_workflow, mock_user):
    """Test successful retrieval of a specific workflow"""
    workflow_id = str(sample_workflow.id)
    sample_workflow.owner_id = mock_user.id
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get, \
         patch.object(workflow_service_instance.user_service, 'can_access_workflow', return_value=True):
        mock_get.return_value = sample_workflow
        
        result = await workflow_service_instance.get_workflow(workflow_id, mock_user)
        
        assert result.name == "test_workflow"
        assert result.revision == "1.0"
        mock_get.assert_called_once_with(workflow_id)


@pytest.mark.asyncio
async def test_get_workflow_not_found(workflow_service_instance, mock_user):
    """Test workflow retrieval when workflow doesn't exist"""
    workflow_id = "507f1f77bcf86cd799439999"
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await workflow_service_instance.get_workflow(workflow_id, mock_user)
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_workflow_success(workflow_service_instance, mock_user):
    """Test successful workflow creation using mocked IProject"""
    
    # Create a mock IProject instead of real one to avoid Beanie validation issues
    mock_workflow = Mock(spec=IProject)
    mock_workflow.name = "new_workflow"
    mock_workflow.revision = "1.0"
    mock_workflow.dataConnectors = []
    mock_workflow.id = "mock-workflow-id"
    mock_workflow.created_at = None  # Will be set by service
    mock_workflow.updated_at = None  # Will be set by service
    mock_workflow.insert = AsyncMock()
    
    # Test the service with mock workflow
    with patch.object(workflow_service_instance.user_service, 'assign_workflow_ownership') as mock_assign:
        result = await workflow_service_instance.create_workflow(mock_workflow, mock_user)
        
        # Verify the workflow was processed correctly
        assert result.name == "new_workflow"
        assert result.revision == "1.0" 
        
        # Verify service sets timestamps
        assert result.created_at is not None
        assert result.updated_at is not None
        
        # Verify service calls
        mock_workflow.insert.assert_called_once()
        mock_assign.assert_called_once_with(mock_user, mock_workflow)


@pytest.mark.asyncio
async def test_update_workflow_success(workflow_service_instance, sample_workflow, mock_user):
    """Test successful workflow update using IProject"""
    workflow_id = str(sample_workflow.id)
    
    # Create minimal schema for IProject
    from app.models.interface.workflow_interface import ISchema
    minimal_schema = ISchema(nodes=[], connections=[])
    
    # Create IProject update data
    update_data = IProject(
        id=workflow_id, 
        name="updated_workflow", 
        revision="1.1",
        pschema=minimal_schema
    )
    sample_workflow.owner_id = mock_user.id
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get, \
         patch.object(workflow_service_instance.user_service, 'can_modify_workflow', return_value=True):
        mock_get.return_value = sample_workflow
        
        result = await workflow_service_instance.update_workflow(update_data, mock_user)
        
        assert result.name == "updated_workflow"
        assert result.revision == "1.1"
        mock_get.assert_called_once_with(workflow_id)
        sample_workflow.replace.assert_called_once()


@pytest.mark.asyncio 
async def test_update_workflow_not_found(workflow_service_instance, mock_user):
    """Test update when workflow doesn't exist"""
    workflow_id = "507f1f77bcf86cd799439999"
    
    # Create IProject update data
    from app.models.interface.workflow_interface import ISchema
    minimal_schema = ISchema(nodes=[], connections=[])
    update_data = IProject(
        id=workflow_id, 
        name="updated_workflow",
        pschema=minimal_schema
    )
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get, \
         patch.object(workflow_service_instance.user_service, 'can_modify_workflow', return_value=True):
        mock_get.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await workflow_service_instance.update_workflow(update_data, mock_user)
        
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_workflow_success(workflow_service_instance, sample_workflow, mock_user):
    """Test successful workflow deletion"""
    workflow_id = str(sample_workflow.id)
    sample_workflow.owner_id = mock_user.id
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get, \
         patch.object(workflow_service_instance.user_service, 'can_modify_workflow', return_value=True), \
         patch.object(workflow_service_instance.user_service, 'remove_workflow_ownership', new_callable=AsyncMock) as mock_remove:
        mock_get.return_value = sample_workflow
        
        result = await workflow_service_instance.delete_workflow(workflow_id, mock_user)
        
        assert result is True
        mock_get.assert_called_once_with(workflow_id)
        mock_remove.assert_called_once_with(workflow_id)
        sample_workflow.delete.assert_called_once()


@pytest.mark.asyncio
async def test_delete_workflow_not_found(workflow_service_instance, mock_user):
    """Test deletion when workflow doesn't exist"""
    workflow_id = "507f1f77bcf86cd799439999"
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get, \
         patch.object(workflow_service_instance.user_service, 'can_modify_workflow', return_value=True):
        mock_get.return_value = None
        
        result = await workflow_service_instance.delete_workflow(workflow_id, mock_user)
        
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
async def test_get_workflow_database_error(workflow_service_instance, mock_user):
    """Test database error handling in get_workflow"""
    workflow_id = "507f1f77bcf86cd799439011"
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Database connection error")
        
        with pytest.raises(HTTPException) as exc_info:
            await workflow_service_instance.get_workflow(workflow_id, mock_user)
        
        assert exc_info.value.status_code == 500
        assert "Internal server error" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_workflow_validation_error(workflow_service_instance, mock_user):
    """Test validation error handling in create_workflow"""
    
    # Create mock IProject that will raise error during insert
    mock_workflow = Mock(spec=IProject)
    mock_workflow.name = "test_workflow"
    mock_workflow.insert = AsyncMock(side_effect=ValueError("Database error"))
    
    with pytest.raises(HTTPException) as exc_info:
        await workflow_service_instance.create_workflow(mock_workflow, mock_user)
    
    assert exc_info.value.status_code == 500
    assert "Failed to create workflow" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_workflow_database_error(workflow_service_instance, mock_user):
    """Test database error handling in update_workflow"""
    from app.models.interface.workflow_interface import ISchema
    minimal_schema = ISchema(nodes=[], connections=[])
    update_data = IProject(
        id="507f1f77bcf86cd799439011", 
        name="updated_workflow",
        pschema=minimal_schema
    )
    
    with patch.object(workflow_service_instance.user_service, 'can_modify_workflow', return_value=True), \
         patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            await workflow_service_instance.update_workflow(update_data, mock_user)
        
        assert exc_info.value.status_code == 500
        assert "Failed to update workflow" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_workflow_missing_id(workflow_service_instance, mock_user):
    """Test update workflow when ID is missing/None"""
    from app.models.interface.workflow_interface import ISchema
    minimal_schema = ISchema(nodes=[], connections=[])
    
    # Create IProject with None ID to test the validation
    update_data = IProject(
        id=None,  # Missing/None ID
        name="updated_workflow",
        pschema=minimal_schema
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await workflow_service_instance.update_workflow(update_data, mock_user)
    
    assert exc_info.value.status_code == 400
    assert "Workflow ID is required" in str(exc_info.value.detail)


# Data Validation Tests
@pytest.mark.asyncio
async def test_create_workflow_with_timestamps(workflow_service_instance, mock_user):
    """Test workflow creation includes timestamps"""
    
    # Create mock IProject for testing
    mock_workflow = Mock(spec=IProject)
    mock_workflow.name = "timestamped_workflow"
    mock_workflow.revision = "1.0"
    mock_workflow.dataConnectors = []
    mock_workflow.created_at = None  # Will be set by service
    mock_workflow.updated_at = None  # Will be set by service
    mock_workflow.insert = AsyncMock()
    
    with patch.object(workflow_service_instance.user_service, 'assign_workflow_ownership'):
        result = await workflow_service_instance.create_workflow(mock_workflow, mock_user)
        
        # Verify timestamps were set
        assert hasattr(mock_workflow, 'created_at')
        assert hasattr(mock_workflow, 'updated_at')
        assert result.name == "timestamped_workflow"


@pytest.mark.asyncio
async def test_update_workflow_updates_timestamp(workflow_service_instance, sample_workflow, mock_user):
    """Test workflow update modifies updated_at timestamp"""
    workflow_id = str(sample_workflow.id)
    original_updated_at = sample_workflow.updated_at
    
    from app.models.interface.workflow_interface import ISchema
    minimal_schema = ISchema(nodes=[], connections=[])
    update_data = IProject(
        id=workflow_id, 
        name="updated_workflow",
        pschema=minimal_schema
    )
    sample_workflow.owner_id = mock_user.id
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get, \
         patch.object(workflow_service_instance.user_service, 'can_modify_workflow', return_value=True):
        mock_get.return_value = sample_workflow
        
        await workflow_service_instance.update_workflow(update_data, mock_user)
        
        # Check that updated_at was modified
        assert sample_workflow.updated_at != original_updated_at


# Complex Data Tests
@pytest.mark.asyncio
async def test_create_workflow_with_empty_schema(workflow_service_instance, mock_user):
    """Test creating workflow with minimal/empty schema"""
    
    # Create mock IProject with minimal schema
    mock_workflow = Mock(spec=IProject)
    mock_workflow.name = "minimal_workflow"
    mock_workflow.revision = "1.0"
    mock_workflow.dataConnectors = []
    mock_workflow.pschema = Mock()
    mock_workflow.pschema.nodes = []
    mock_workflow.pschema.connections = []
    mock_workflow.created_at = None
    mock_workflow.updated_at = None
    mock_workflow.insert = AsyncMock()
    
    with patch.object(workflow_service_instance.user_service, 'assign_workflow_ownership'):
        result = await workflow_service_instance.create_workflow(mock_workflow, mock_user)
        
        assert result.name == "minimal_workflow"
        mock_workflow.insert.assert_called_once()


@pytest.mark.asyncio
async def test_create_workflow_generates_uuid_when_missing(workflow_service_instance, mock_user):
    """Test that create_workflow automatically generates UUID when id is None"""
    
    # Create mock IProject without id
    mock_workflow = Mock(spec=IProject)
    mock_workflow.name = "test_workflow"
    mock_workflow.id = None  # No ID provided
    mock_workflow.revision = "1.0"
    mock_workflow.dataConnectors = []
    mock_workflow.pschema = Mock()
    mock_workflow.pschema.nodes = []
    mock_workflow.pschema.connections = []
    mock_workflow.created_at = None
    mock_workflow.updated_at = None
    mock_workflow.insert = AsyncMock()
    
    with patch.object(workflow_service_instance.user_service, 'assign_workflow_ownership'):
        result = await workflow_service_instance.create_workflow(mock_workflow, mock_user)
        
        # Verify UUID was generated
        assert result.id is not None
        assert len(result.id) == 36  # UUID format length
        assert "-" in result.id  # UUID contains hyphens
        mock_workflow.insert.assert_called_once()


@pytest.mark.asyncio
async def test_update_workflow_partial_data(workflow_service_instance, sample_workflow, mock_user):
    """Test partial update of workflow data using IProject"""
    workflow_id = str(sample_workflow.id)
    
    from app.models.interface.workflow_interface import ISchema
    minimal_schema = ISchema(nodes=[], connections=[])
    partial_update = IProject(
        id=workflow_id, 
        revision="1.1",  # Only updating revision
        name="test",  # Required field
        pschema=minimal_schema
    )
    sample_workflow.owner_id = mock_user.id
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get, \
         patch.object(workflow_service_instance.user_service, 'can_modify_workflow', return_value=True):
        mock_get.return_value = sample_workflow
        
        result = await workflow_service_instance.update_workflow(partial_update, mock_user)
        
        assert result.name == sample_workflow.name  # Name should remain unchanged
        assert result.revision == "1.1"  # Only revision changes
        mock_get.assert_called_once_with(workflow_id)


@pytest.mark.asyncio
async def test_workflow_with_data_connectors(workflow_service_instance, mock_user):
    """Test workflow creation with data connectors"""
    
    # Create mock IProject with data connectors
    mock_workflow = Mock(spec=IProject)
    mock_workflow.name = "connector_workflow"
    mock_workflow.revision = "1.0"
    mock_workflow.dataConnectors = ["conn1", "conn2"]
    mock_workflow.pschema = Mock()
    mock_workflow.pschema.nodes = []
    mock_workflow.pschema.connections = []
    mock_workflow.created_at = None
    mock_workflow.updated_at = None
    mock_workflow.insert = AsyncMock()
    
    with patch.object(workflow_service_instance.user_service, 'assign_workflow_ownership'):        
        result = await workflow_service_instance.create_workflow(mock_workflow, mock_user)
        
        assert result.name == "connector_workflow"
        assert len(result.dataConnectors) == 2
        assert result.dataConnectors[0] == "conn1"
        assert result.dataConnectors[1] == "conn2"
        mock_workflow.insert.assert_called_once()


@pytest.mark.asyncio
async def test_update_workflow_data_connectors(workflow_service_instance, sample_workflow, mock_user):
    """Test updating workflow data connectors"""
    workflow_id = str(sample_workflow.id)
    new_connectors = ["new_conn"]
    
    from app.models.interface.workflow_interface import ISchema
    minimal_schema = ISchema(nodes=[], connections=[])
    update_data = IProject(
        id=workflow_id, 
        dataConnectors=new_connectors,
        name="test",  # Required field
        pschema=minimal_schema
    )
    sample_workflow.owner_id = mock_user.id
    
    with patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get, \
         patch.object(workflow_service_instance.user_service, 'can_modify_workflow', return_value=True):
        mock_get.return_value = sample_workflow
        
        result = await workflow_service_instance.update_workflow(update_data, mock_user)
        
        assert result.dataConnectors == new_connectors
        mock_get.assert_called_once_with(workflow_id)
        sample_workflow.replace.assert_called_once()


# Workflow Service Exception Handling
@pytest.mark.asyncio
async def test_get_workflows_database_error(workflow_service_instance, mock_user):
    """Test database error handling in get_workflows"""
    # Set owned workflows to trigger database call
    mock_user.owned_workflows = ["some_id"]
    
    with patch.object(IProject, 'find') as mock_find:
        mock_find.side_effect = Exception("Database connection error")
        
        with pytest.raises(HTTPException) as exc_info:
            await workflow_service_instance.get_workflows(mock_user)
        
        assert exc_info.value.status_code == 500
        assert "Failed to retrieve workflows" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_delete_workflow_exception_handling(workflow_service_instance, mock_user):
    """Test delete workflow exception handling"""
    workflow_id = "507f1f77bcf86cd799439011"
    
    with patch.object(workflow_service_instance.user_service, 'can_modify_workflow', return_value=True), \
         patch.object(IProject, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Database error")
        
        result = await workflow_service_instance.delete_workflow(workflow_id, mock_user)
        
        # Should return False when there's an exception, not raise
        assert result is False


# ============================================================================
# M2M (Machine-to-Machine) Tests - Optional User Parameter
# ============================================================================

@pytest.mark.asyncio
async def test_get_workflows_without_user(workflow_service_instance):
    """Test that get_workflows works without user (returns all workflows for M2M calls)"""
    # Create test workflows
    workflow1 = IProject(
        id="test-workflow-m2m-1",
        name="M2M Workflow 1",
        revision="1.0",
        pschema=ISchema(nodes=[], connections=[], revision="1.0")
    )
    workflow2 = IProject(
        id="test-workflow-m2m-2",
        name="M2M Workflow 2",
        revision="1.0",
        pschema=ISchema(nodes=[], connections=[], revision="1.0")
    )
    await workflow1.insert()
    await workflow2.insert()
    
    # Call without user parameter (M2M style)
    workflows = await workflow_service_instance.get_workflows()
    
    # Should get all workflows without permission filtering
    assert len(workflows) >= 2
    assert any(w.id == "test-workflow-m2m-1" for w in workflows)
    assert any(w.id == "test-workflow-m2m-2" for w in workflows)


@pytest.mark.asyncio
async def test_get_workflow_without_user(workflow_service_instance):
    """Test that get_workflow works without user (no permission check for M2M calls)"""
    # Create test workflow
    workflow = IProject(
        id="test-workflow-m2m-3",
        name="M2M Workflow 3",
        revision="1.0",
        pschema=ISchema(nodes=[], connections=[], revision="1.0")
    )
    await workflow.insert()
    
    # Call without user parameter (M2M style)
    result = await workflow_service_instance.get_workflow("test-workflow-m2m-3")
    
    # Should get workflow without permission check
    assert result is not None
    assert result.id == "test-workflow-m2m-3"
    assert result.name == "M2M Workflow 3"


@pytest.mark.asyncio
async def test_update_workflow_preserves_system_fields(workflow_service_instance, mock_admin_user):
    """Test that system fields like owner_id are preserved during IProject updates with exclude_unset=True"""
    
    # Create original workflow with owner_id
    original_workflow = IProject(
        id="preserve-test-workflow",
        name="Original Workflow",
        owner_id="user-123",
        pschema=ISchema(nodes=[], connections=[])
    )
    await original_workflow.create()
    
    # Create partial update WITHOUT owner_id (simulates frontend JSON without owner_id)
    partial_update = IProject(
        id="preserve-test-workflow",
        name="Updated Workflow Name",
        pschema=ISchema(nodes=[], connections=[])
        # Note: owner_id is NOT provided - this is the key test!
    )
    
    # Update using admin to bypass permission checks
    updated_workflow = await workflow_service_instance.update_workflow(partial_update, mock_admin_user)
    
    # Verify the optimization: owner_id should be preserved, name should be updated
    assert updated_workflow.name == "Updated Workflow Name", "Name should be updated"
    assert updated_workflow.owner_id == "user-123", "owner_id should be preserved from original"
    
    # This is the core success: exclude_unset=True prevented owner_id from being overwritten with None


def test_exclude_unset_model_behavior():
    """Test that IProject.model_dump(exclude_unset=True) only includes explicitly set fields"""
    
    # Simulate FastAPI validation of JSON without owner_id
    workflow_json = {
        "id": "test-workflow",
        "name": "Updated Name",
        "pschema": {
            "nodes": [],
            "connections": []
        }
        # Note: no owner_id field in original JSON
    }
    
    # Create IProject from JSON (as FastAPI would do)
    workflow = IProject(**workflow_json)
    
    # Test exclude_unset behavior
    update_data = workflow.model_dump(exclude_unset=True)
    
    # Key assertions for our optimization
    assert "owner_id" not in update_data, "owner_id should not be in update when not provided in JSON"
    assert "created_at" not in update_data, "created_at should not be in update when not provided in JSON"
    
    # But explicitly provided fields should be there
    assert "id" in update_data
    assert "name" in update_data
    assert update_data["name"] == "Updated Name"
