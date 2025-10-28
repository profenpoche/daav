"""
Tests for MigrationService

This module tests data migration functionality including:
- Migration from config.ini to MongoDB
- Dataset migration
- Workflow migration
- Backup creation
- Error handling
"""

import pytest
import pytest_asyncio
import json
import os
from unittest.mock import Mock, AsyncMock, patch, mock_open, MagicMock
from datetime import datetime

from app.services.migration_service import MigrationService
from app.models.interface.user_interface import User
from app.models.interface.workflow_interface import IProject


@pytest_asyncio.fixture
async def test_user():
    """Create a test user for migrations"""
    user = User(
        username="migration_user",
        email="migration@example.com",
        full_name="Migration User",
        hashed_password="hashed_password",
        is_active=True,
        is_admin=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    user.id = "user_migration_123"
    return user


@pytest.fixture
def mock_config_data():
    """Mock config.ini data structure"""
    return {
        "connections": [
            {
                "id": "dataset_1",
                "name": "MongoDB Test",
                "type": "mongo",
                "host": "localhost",
                "port": 27017,
                "database": "test_db",
                "username": "user",
                "password": "pass"
            },
            {
                "id": "dataset_2",
                "name": "MySQL Test",
                "type": "mysql",
                "host": "localhost",
                "port": 3306,
                "database": "test_db",
                "username": "user",
                "password": "pass"
            }
        ],
        "workflows": [
            {
                "id": "workflow_1",
                "name": "Test Workflow",
                "description": "Test workflow description",
                "schema": {
                    "nodes": [],
                    "connections": []
                },
                "nodes": [],
                "edges": []
            },
            {
                "id": "workflow_2",
                "name": "Second Workflow",
                "description": "Another workflow",
                "schema": {
                    "nodes": [],
                    "connections": []
                },
                "nodes": [],
                "edges": []
            }
        ]
    }


# ============================================
# FILE OPERATIONS TESTS
# ============================================

@pytest.mark.asyncio
async def test_migrate_from_config_ini_file_not_found(test_user):
    """Test migration when config.ini file doesn't exist"""
    with patch('os.path.exists', return_value=False):
        result = await MigrationService.migrate_from_config_ini(test_user)
        
        assert result is False


@pytest.mark.asyncio
async def test_migrate_from_config_ini_file_read_error(test_user):
    """Test migration when file cannot be read"""
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', side_effect=IOError("Cannot read file")):
            result = await MigrationService.migrate_from_config_ini(test_user)
            
            assert result is False


@pytest.mark.asyncio
async def test_migrate_from_config_ini_invalid_json(test_user):
    """Test migration with invalid JSON in config file"""
    invalid_json = "{ invalid json }"
    
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=invalid_json)):
            result = await MigrationService.migrate_from_config_ini(test_user)
            
            assert result is False


# ============================================
# DATASET MIGRATION TESTS
# ============================================

@pytest.mark.asyncio
async def test_migrate_datasets_success(test_user, mock_config_data):
    """Test successful dataset migration"""
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_config_data))):
            with patch('app.services.migration_service.DatasetService') as MockDatasetService:
                mock_dataset_service = MockDatasetService.return_value
                mock_dataset_service.add_connection = AsyncMock(
                    return_value={"status": "Connection added"}
                )
                
                with patch('app.services.migration_service.workflow_service') as mock_workflow_service:
                    mock_workflow_service.workflow_exists = AsyncMock(return_value=False)
                    mock_workflow_service.create_workflow = AsyncMock()
                    
                    with patch('os.rename'):
                        result = await MigrationService.migrate_from_config_ini(test_user)
                    
                    assert result is True
                    assert mock_dataset_service.add_connection.call_count == 2


@pytest.mark.asyncio
async def test_migrate_datasets_already_exists(test_user, mock_config_data):
    """Test migration when datasets already exist"""
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_config_data))):
            with patch('app.services.migration_service.DatasetService') as MockDatasetService:
                mock_dataset_service = MockDatasetService.return_value
                mock_dataset_service.add_connection = AsyncMock(
                    return_value={"status": "Connection already exists"}
                )
                
                with patch('app.services.migration_service.workflow_service') as mock_workflow_service:
                    mock_workflow_service.workflow_exists = AsyncMock(return_value=True)
                    
                    with patch('os.rename'):
                        result = await MigrationService.migrate_from_config_ini(test_user)
                    
                    assert result is True
                    # Datasets were attempted to be added
                    assert mock_dataset_service.add_connection.call_count == 2


@pytest.mark.asyncio
async def test_migrate_datasets_validation_error(test_user):
    """Test migration with invalid dataset data"""
    invalid_config = {
        "connections": [
            {
                "name": "Invalid Dataset",
                # Missing required fields
            }
        ],
        "workflows": []
    }
    
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(invalid_config))):
            with patch('app.services.migration_service.DatasetService'):
                with patch('os.rename'):
                    result = await MigrationService.migrate_from_config_ini(test_user)
                    
                    # Should still complete migration (just skip invalid datasets)
                    assert result is True


@pytest.mark.asyncio
async def test_migrate_datasets_service_error(test_user, mock_config_data):
    """Test migration when dataset service throws error"""
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_config_data))):
            with patch('app.services.migration_service.DatasetService') as MockDatasetService:
                mock_dataset_service = MockDatasetService.return_value
                mock_dataset_service.add_connection = AsyncMock(
                    side_effect=Exception("Database connection error")
                )
                
                with patch('app.services.migration_service.workflow_service') as mock_workflow_service:
                    mock_workflow_service.workflow_exists = AsyncMock(return_value=True)
                    
                    with patch('os.rename'):
                        result = await MigrationService.migrate_from_config_ini(test_user)
                    
                    # Should continue despite errors
                    assert result is True


# ============================================
# WORKFLOW MIGRATION TESTS
# ============================================

@pytest.mark.asyncio
async def test_migrate_workflows_success(test_user, mock_config_data):
    """Test successful workflow migration"""
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_config_data))):
            with patch('app.services.migration_service.DatasetService') as MockDatasetService:
                mock_dataset_service = MockDatasetService.return_value
                mock_dataset_service.add_connection = AsyncMock(
                    return_value={"status": "Connection added"}
                )
                
                with patch('app.services.migration_service.workflow_service') as mock_workflow_service:
                    mock_workflow_service.workflow_exists = AsyncMock(return_value=False)
                    mock_workflow_service.create_workflow = AsyncMock()
                    
                    with patch('os.rename'):
                        result = await MigrationService.migrate_from_config_ini(test_user)
                    
                    assert result is True
                    assert mock_workflow_service.create_workflow.call_count == 2


@pytest.mark.asyncio
async def test_migrate_workflows_already_exists(test_user, mock_config_data):
    """Test migration when workflows already exist"""
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_config_data))):
            with patch('app.services.migration_service.DatasetService') as MockDatasetService:
                mock_dataset_service = MockDatasetService.return_value
                mock_dataset_service.add_connection = AsyncMock(
                    return_value={"status": "Connection added"}
                )
                
                with patch('app.services.migration_service.workflow_service') as mock_workflow_service:
                    mock_workflow_service.workflow_exists = AsyncMock(return_value=True)
                    mock_workflow_service.create_workflow = AsyncMock()
                    
                    with patch('os.rename'):
                        result = await MigrationService.migrate_from_config_ini(test_user)
                    
                    assert result is True
                    # Workflows should not be created if they exist
                    assert mock_workflow_service.create_workflow.call_count == 0


@pytest.mark.asyncio
async def test_migrate_workflows_validation_error(test_user):
    """Test migration with invalid workflow data"""
    invalid_config = {
        "connections": [],
        "workflows": [
            {
                "name": "Invalid Workflow"
                # Missing required fields
            }
        ]
    }
    
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(invalid_config))):
            with patch('app.services.migration_service.DatasetService'):
                with patch('app.services.migration_service.workflow_service'):
                    with patch('os.rename'):
                        result = await MigrationService.migrate_from_config_ini(test_user)
                        
                        # Should still complete migration (just skip invalid workflows)
                        assert result is True


@pytest.mark.asyncio
async def test_migrate_workflows_service_error(test_user, mock_config_data):
    """Test migration when workflow service throws error"""
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_config_data))):
            with patch('app.services.migration_service.DatasetService') as MockDatasetService:
                mock_dataset_service = MockDatasetService.return_value
                mock_dataset_service.add_connection = AsyncMock(
                    return_value={"status": "Connection added"}
                )
                
                with patch('app.services.migration_service.workflow_service') as mock_workflow_service:
                    mock_workflow_service.workflow_exists = AsyncMock(return_value=False)
                    mock_workflow_service.create_workflow = AsyncMock(
                        side_effect=Exception("Database error")
                    )
                    
                    with patch('os.rename'):
                        result = await MigrationService.migrate_from_config_ini(test_user)
                    
                    # Should continue despite errors
                    assert result is True


# ============================================
# BACKUP TESTS
# ============================================

@pytest.mark.asyncio
async def test_config_backup_created(test_user, mock_config_data):
    """Test that config.ini is backed up after migration"""
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_config_data))):
            with patch('app.services.migration_service.DatasetService') as MockDatasetService:
                mock_dataset_service = MockDatasetService.return_value
                mock_dataset_service.add_connection = AsyncMock(
                    return_value={"status": "Connection added"}
                )
                
                with patch('app.services.migration_service.workflow_service') as mock_workflow_service:
                    mock_workflow_service.workflow_exists = AsyncMock(return_value=True)
                    
                    with patch('os.rename') as mock_rename:
                        result = await MigrationService.migrate_from_config_ini(test_user)
                        
                        assert result is True
                        # Verify backup was created
                        mock_rename.assert_called_once()
                        call_args = mock_rename.call_args[0]
                        assert call_args[0] == "./app/config.ini"
                        assert call_args[1] == "./app/config.ini.backup"


# ============================================
# EMPTY DATA TESTS
# ============================================

@pytest.mark.asyncio
async def test_migrate_empty_connections(test_user):
    """Test migration with no datasets"""
    empty_config = {
        "connections": [],
        "workflows": []
    }
    
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(empty_config))):
            with patch('app.services.migration_service.DatasetService'):
                with patch('app.services.migration_service.workflow_service'):
                    with patch('os.rename'):
                        result = await MigrationService.migrate_from_config_ini(test_user)
                        
                        assert result is True


@pytest.mark.asyncio
async def test_migrate_empty_workflows(test_user):
    """Test migration with no workflows"""
    config = {
        "connections": [
            {
                "id": "dataset_1",
                "name": "MongoDB Test",
                "type": "mongo",
                "host": "localhost",
                "port": 27017,
                "database": "test_db",
                "username": "user",
                "password": "pass"
            }
        ],
        "workflows": []
    }
    
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(config))):
            with patch('app.services.migration_service.DatasetService') as MockDatasetService:
                mock_dataset_service = MockDatasetService.return_value
                mock_dataset_service.add_connection = AsyncMock(
                    return_value={"status": "Connection added"}
                )
                
                with patch('app.services.migration_service.workflow_service'):
                    with patch('os.rename'):
                        result = await MigrationService.migrate_from_config_ini(test_user)
                        
                        assert result is True


# ============================================
# INTEGRATION TESTS
# ============================================

@pytest.mark.asyncio
async def test_full_migration_workflow(test_user, mock_config_data):
    """Test complete migration workflow with datasets and workflows"""
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_config_data))):
            with patch('app.services.migration_service.DatasetService') as MockDatasetService:
                mock_dataset_service = MockDatasetService.return_value
                mock_dataset_service.add_connection = AsyncMock(
                    return_value={"status": "Connection added"}
                )
                
                with patch('app.services.migration_service.workflow_service') as mock_workflow_service:
                    mock_workflow_service.workflow_exists = AsyncMock(return_value=False)
                    mock_workflow_service.create_workflow = AsyncMock()
                    
                    with patch('os.rename') as mock_rename:
                        result = await MigrationService.migrate_from_config_ini(test_user)
                        
                        assert result is True
                        
                        # Verify datasets were migrated
                        assert mock_dataset_service.add_connection.call_count == 2
                        
                        # Verify workflows were migrated
                        assert mock_workflow_service.workflow_exists.call_count == 2
                        assert mock_workflow_service.create_workflow.call_count == 2
                        
                        # Verify backup was created
                        mock_rename.assert_called_once()


@pytest.mark.asyncio
async def test_migration_with_mixed_results(test_user):
    """Test migration where some items succeed and some fail"""
    mixed_config = {
        "connections": [
            {
                "id": "dataset_1",
                "name": "Valid Dataset",
                "type": "mongo",
                "host": "localhost",
                "port": 27017,
                "database": "test_db",
                "username": "user",
                "password": "pass"
            },
            {
                "name": "Invalid Dataset"
                # Missing required fields - will fail validation
            }
        ],
        "workflows": [
            {
                "id": "workflow_1",
                "name": "Valid Workflow",
                "description": "Valid",
                "schema": {
                    "nodes": [],
                    "connections": []
                },
                "nodes": [],
                "edges": []
            },
            {
                "name": "Invalid Workflow"
                # Missing required fields - will fail validation
            }
        ]
    }
    
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(mixed_config))):
            with patch('app.services.migration_service.DatasetService') as MockDatasetService:
                mock_dataset_service = MockDatasetService.return_value
                mock_dataset_service.add_connection = AsyncMock(
                    return_value={"status": "Connection added"}
                )
                
                with patch('app.services.migration_service.workflow_service') as mock_workflow_service:
                    mock_workflow_service.workflow_exists = AsyncMock(return_value=False)
                    mock_workflow_service.create_workflow = AsyncMock()
                    
                    with patch('os.rename'):
                        result = await MigrationService.migrate_from_config_ini(test_user)
                        
                        # Migration should complete successfully
                        assert result is True
                        
                        # Only valid items should be migrated
                        # Note: Invalid items will fail validation but won't crash the migration


@pytest.mark.asyncio
async def test_migration_user_parameter_passed(test_user, mock_config_data):
    """Test that user parameter is correctly passed to services"""
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_config_data))):
            with patch('app.services.migration_service.DatasetService') as MockDatasetService:
                mock_dataset_service = MockDatasetService.return_value
                mock_dataset_service.add_connection = AsyncMock(
                    return_value={"status": "Connection added"}
                )
                
                with patch('app.services.migration_service.workflow_service') as mock_workflow_service:
                    mock_workflow_service.workflow_exists = AsyncMock(return_value=False)
                    mock_workflow_service.create_workflow = AsyncMock()
                    
                    with patch('os.rename'):
                        result = await MigrationService.migrate_from_config_ini(test_user)
                        
                        assert result is True
                        
                        # Verify user was passed to add_connection
                        for call in mock_dataset_service.add_connection.call_args_list:
                            assert call[0][1] == test_user  # Second parameter should be user
                        
                        # Verify user was passed to create_workflow
                        for call in mock_workflow_service.create_workflow.call_args_list:
                            assert call[0][1] == test_user  # Second parameter should be user
