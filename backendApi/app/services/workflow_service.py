import logging
from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException, status
from app.models.interface.workflow_interface import IProject
from app.utils.singleton import SingletonMeta
import uuid

logger = logging.getLogger(__name__)

class WorkflowService(metaclass=SingletonMeta):
    
    def __init__(self):
        logger.info("WorkflowService initialized")

    async def get_workflows(self) -> List[IProject]:
        """Retrieve all workflows"""
        try:
            logger.debug("Fetching all workflows from database")
            workflows = await IProject.find_all().to_list()
            logger.info(f"Successfully retrieved {len(workflows)} workflows")
            return workflows
        except Exception as e:
            logger.error(f"Error retrieving workflows: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to retrieve workflows")

    async def get_workflow(self, workflow_id: str) -> IProject:
        """Retrieve a workflow by its ID"""
        try:
            logger.debug(f"Fetching workflow with ID: {workflow_id}")
            workflow = await IProject.get(workflow_id)
            if not workflow:
                logger.warning(f"Workflow not found with ID: {workflow_id}")
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            logger.info(f"Successfully retrieved workflow: {workflow.name} (ID: {workflow_id})")
            return workflow
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving workflow {workflow_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

    async def create_workflow(self, workflow_data: dict) -> IProject:
        """Create a new workflow"""
        try:
            # Generate UUID if not provided
            '''if not workflow_data.get('id'):
                workflow_data['id'] = str(uuid.uuid4())'''
            
            logger.info(f"Creating new workflow: {workflow_data.get('name')} (ID: {workflow_data.get('id')})")
            
            # Create workflow instance
            workflow = IProject(**workflow_data)
            workflow.created_at = datetime.utcnow()
            workflow.updated_at = datetime.utcnow()
            
            # Save to MongoDB
            await workflow.insert()
            logger.info(f"Successfully created workflow: {workflow.name} (ID: {workflow.id})")
            return workflow
            
        except Exception as e:
            logger.error(f"Error creating workflow: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to create workflow")

    async def update_workflow(self, workflow_data: dict) -> IProject:
        """Update an existing workflow"""
        try:
            workflow_id = workflow_data.get('id')
            if not workflow_id:
                raise HTTPException(status_code=400, detail="Workflow ID is required")
            
            logger.info(f"Updating workflow with ID: {workflow_id}")
            
            # Find existing workflow
            existing_workflow = await IProject.get(workflow_id)
            if not existing_workflow:
                logger.warning(f"Workflow not found for update: {workflow_id}")
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            # Update fields
            for key, value in workflow_data.items():
                if hasattr(existing_workflow, key):
                    setattr(existing_workflow, key, value)
            
            existing_workflow.updated_at = datetime.utcnow()
            
            # Save changes
            await existing_workflow.replace()
            logger.info(f"Successfully updated workflow: {existing_workflow.name} (ID: {workflow_id})")
            return existing_workflow
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating workflow {workflow_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to update workflow")

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        try:
            logger.info(f"Attempting to delete workflow with ID: {workflow_id}")
            
            workflow = await IProject.get(workflow_id)
            if not workflow:
                logger.warning(f"Attempted to delete non-existent workflow: {workflow_id}")
                return False
            
            workflow_name = workflow.name
            await workflow.delete()
            
            logger.info(f"Successfully deleted workflow: {workflow_name} (ID: {workflow_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting workflow {workflow_id}: {e}", exc_info=True)
            return False

    async def workflow_exists(self, workflow_id: str) -> bool:
        """Check if a workflow exists"""
        try:
            workflow = await IProject.get(workflow_id)
            return workflow is not None
        except Exception:
            return False

# Singleton instance
workflow_service = WorkflowService()