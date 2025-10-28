"""
Tests for ExecutionContext

These tests verify that the execution context correctly stores and retrieves
user and workflow information across async boundaries.
"""

import pytest
from app.core.execution_context import ExecutionContext
from app.models.interface.user_interface import User
from app.models.interface.workflow_interface import IProject, ISchema
from app.enums.user_role import UserRole


class TestExecutionContext:
    """Test suite for ExecutionContext functionality"""
    
    def setup_method(self):
        """Clear context before each test"""
        ExecutionContext.clear()
    
    def teardown_method(self):
        """Clear context after each test"""
        ExecutionContext.clear()
    
    def test_set_and_get_user(self):
        """Test setting and retrieving user context"""
        # Create test user with all required fields
        test_user = User(
            id="test-user-123",
            username="test_user",
            email="test@example.com",
            full_name="Test User",
            hashed_password="$argon2id$test_hash",
            role=UserRole.USER
        )
        
        # Set user context
        ExecutionContext.set_user(test_user)
        
        # Retrieve user
        retrieved_user = ExecutionContext.get_user()
        
        assert retrieved_user is not None
        assert retrieved_user.id == "test-user-123"
        assert retrieved_user.username == "test_user"
        assert retrieved_user.role == UserRole.USER
    
    def test_set_and_get_workflow(self):
        """Test setting and retrieving workflow context"""
        # Create test workflow
        test_workflow = IProject(
            id="workflow-456",
            name="Test Workflow",
            revision="1.0",
            pschema=ISchema(nodes=[], connections=[])
        )
        
        # Set workflow context
        ExecutionContext.set_workflow(test_workflow)
        
        # Retrieve workflow
        retrieved_workflow = ExecutionContext.get_workflow()
        
        assert retrieved_workflow is not None
        assert retrieved_workflow.id == "workflow-456"
        assert retrieved_workflow.name == "Test Workflow"
        assert retrieved_workflow.revision == "1.0"
    
    def test_get_workflow_id(self):
        """Test convenience method for getting workflow ID"""
        test_workflow = IProject(
            id="workflow-789",
            name="ID Test Workflow",
            pschema=ISchema(nodes=[], connections=[])
        )
        
        ExecutionContext.set_workflow(test_workflow)
        
        workflow_id = ExecutionContext.get_workflow_id()
        assert workflow_id == "workflow-789"
    
    def test_get_workflow_name(self):
        """Test convenience method for getting workflow name"""
        test_workflow = IProject(
            id="workflow-999",
            name="Name Test Workflow",
            pschema=ISchema(nodes=[], connections=[])
        )
        
        ExecutionContext.set_workflow(test_workflow)
        
        workflow_name = ExecutionContext.get_workflow_name()
        assert workflow_name == "Name Test Workflow"
    
    def test_clear_context(self):
        """Test clearing all context variables"""
        # Set both user and workflow
        test_user = User(
            id="clear-test-user",
            username="clear_user",
            email="clear@example.com",
            full_name="Clear Test User",
            hashed_password="$argon2id$test_hash",
            role=UserRole.USER
        )
        test_workflow = IProject(
            id="clear-workflow",
            name="Clear Test",
            pschema=ISchema(nodes=[], connections=[])
        )
        
        ExecutionContext.set_user(test_user)
        ExecutionContext.set_workflow(test_workflow)
        
        # Verify they're set
        assert ExecutionContext.get_user() is not None
        assert ExecutionContext.get_workflow() is not None
        
        # Clear context
        ExecutionContext.clear()
        
        # Verify they're cleared
        assert ExecutionContext.get_user() is None
        assert ExecutionContext.get_workflow() is None
    
    def test_get_context_summary(self):
        """Test getting context summary for debugging"""
        test_user = User(
            id="summary-user",
            username="summary_test",
            email="summary@example.com",
            full_name="Summary Test User",
            hashed_password="$argon2id$test_hash",
            role=UserRole.ADMIN
        )
        test_workflow = IProject(
            id="summary-workflow",
            name="Summary Workflow",
            revision="2.0",
            pschema=ISchema(nodes=[], connections=[])
        )
        
        ExecutionContext.set_user(test_user)
        ExecutionContext.set_workflow(test_workflow)
        
        summary = ExecutionContext.get_context_summary()
        
        assert summary["user"]["id"] == "summary-user"
        assert summary["user"]["username"] == "summary_test"
        assert summary["user"]["role"] == "admin"  # Role value is lowercase
        assert summary["workflow"]["id"] == "summary-workflow"
        assert summary["workflow"]["name"] == "Summary Workflow"
        assert summary["workflow"]["revision"] == "2.0"
    
    def test_no_context_returns_none(self):
        """Test that getting context without setting returns None"""
        assert ExecutionContext.get_user() is None
        assert ExecutionContext.get_workflow() is None
        assert ExecutionContext.get_workflow_id() is None
        assert ExecutionContext.get_workflow_name() is None
    
    def test_set_none_clears_context(self):
        """Test that setting None explicitly clears the context"""
        test_user = User(
            id="none-test",
            username="none_user",
            email="none@example.com",
            full_name="None Test User",
            hashed_password="$argon2id$test_hash",
            role=UserRole.USER
        )
        
        ExecutionContext.set_user(test_user)
        assert ExecutionContext.get_user() is not None
        
        ExecutionContext.set_user(None)
        assert ExecutionContext.get_user() is None
    
    @pytest.mark.asyncio
    async def test_context_preserved_across_async(self):
        """Test that context is preserved across async boundaries"""
        import asyncio
        
        test_user = User(
            id="async-user",
            username="async_test",
            email="async@example.com",
            full_name="Async Test User",
            hashed_password="$argon2id$test_hash",
            role=UserRole.USER
        )
        
        ExecutionContext.set_user(test_user)
        
        async def async_function():
            """Nested async function"""
            await asyncio.sleep(0.01)
            user = ExecutionContext.get_user()
            return user
        
        retrieved_user = await async_function()
        
        assert retrieved_user is not None
        assert retrieved_user.id == "async-user"
        assert retrieved_user.username == "async_test"
    
    def test_context_summary_with_no_context(self):
        """Test context summary when no context is set"""
        summary = ExecutionContext.get_context_summary()
        
        assert summary["user"] is None
        assert summary["workflow"] is None
