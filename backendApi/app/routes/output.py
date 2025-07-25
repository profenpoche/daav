import json
import os
import logging
from typing import Annotated, Optional
from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import JSONResponse

from app.services.dataset_service import DatasetService
from app.services.workflow_service import WorkflowService
from app.models.interface.pdc_chain_interface import PdcChainHeaders, PdcChainResponse, PdcChainRequest

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/output", tags=["outputs"])

# Initialize services
dataset_service = DatasetService()
workflow_service = WorkflowService()

@router.get("/{custom_path}")
async def get_output_from_custom_path(custom_path: str):
    """Get output from custom path by searching through workflows"""
    try:
        logger.info(f"Searching for output with custom path: {custom_path}")
        
        # Get all workflows from the service
        workflows = await workflow_service.get_workflows()
        
        # Look for the workflow that has PdcOutput with urlInput == custom_path
        node = None
        for wf in workflows:
            for wf_node in wf.pschema.nodes:
                if ((wf_node.type == "PdcOutput" or wf_node.type == "ApiOutput") and 
                    wf_node.data.get("urlInput", {}).get("value") == custom_path):
                    node = wf_node
                    break
            if node:
                break

        if node is None:
            logger.warning(f"No PdcOutput node found with URL: {custom_path}")
            raise HTTPException(status_code=404, detail="No PdcOutput node with this URL found")
        
        pdc_id = node.id
        file_path = f"{pdc_id}-output.json"
        logger.debug(f"Looking for output file: {file_path}")

        if not os.path.exists(file_path):
            logger.error(f"Output file not found: {file_path}")
            raise HTTPException(status_code=404, detail="Output file not found")

        # Read and return the output file
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        logger.info(f"Successfully returned output for path: {custom_path}")
        return JSONResponse(content=data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading output file for path {custom_path}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error reading output file: {str(e)}")

@router.get("/workflow/{workflow_id}")
async def get_workflow_output(workflow_id: str, pdc_token: str, request: Request):
    """Get workflow output by workflow ID"""
    try:
        logger.info(f"Getting workflow output for ID: {workflow_id}")
        
        # Get specific workflow from the service
        workflow = await workflow_service.get_workflow(workflow_id)
        
        if workflow is None:
            logger.warning(f"Workflow not found: {workflow_id}")
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Find PdcOutput node in the workflow
        pdc_output = None
        for node in workflow.pschema.nodes:
            if node.type == "PdcOutput":
                pdc_output = node
                break
        
        if pdc_output is None:
            logger.error(f"No PdcOutput node found in workflow: {workflow_id}")
            raise HTTPException(status_code=400, detail="PdcOutput node not found")

        # Construct output file path
        pdc_id = pdc_output.id
        file_path = f"{pdc_id}-output.json"
        logger.debug(f"Looking for workflow output file: {file_path}")

        if not os.path.isfile(file_path):
            logger.error(f"Workflow output file not found: {file_path}")
            raise HTTPException(status_code=404, detail="Output file not found")

        # Read and return the output file
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        logger.info(f"Successfully returned workflow output for ID: {workflow_id}")
        return JSONResponse(content=data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading workflow output for ID {workflow_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Can't read the output file: {str(e)}")

def verify_bearer(request: Request, pdc_token: str):
    """Verify Bearer token in Authorization header"""
    try:
        logger.debug("Verifying Bearer token")
        
        if "Authorization" not in request.headers:
            logger.warning("Authorization header missing in request")
            raise HTTPException(status_code=401, detail='Authorization header missing')
        
        token = get_token_auth_header(request.headers["Authorization"])
        
        if token != pdc_token:
            logger.warning("Invalid token provided")
            raise HTTPException(status_code=401, detail="Invalid token")
        
        logger.debug("Bearer token verified successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying bearer token: {e}", exc_info=True)
        raise HTTPException(
            status_code=401,
            detail=e.message if hasattr(e, 'message') else str(e)
        )

def get_token_auth_header(authorization: str) -> str:
    """Extract token from Authorization header"""
    logger.debug("Extracting token from Authorization header")
    
    parts = authorization.split()

    if parts[0].lower() != "bearer":
        logger.warning("Authorization header doesn't start with Bearer")
        raise HTTPException(
            status_code=401, 
            detail='Authorization header must start with Bearer'
        )
    elif len(parts) == 1:
        logger.warning("Authorization token not found in header")
        raise HTTPException(
            status_code=401, 
            detail='Authorization token not found'
        )
    elif len(parts) > 2:
        logger.warning("Invalid Authorization header format")
        raise HTTPException(
            status_code=401, 
            detail='Authorization header must be Bearer token'
        )
    
    token = parts[1]
    logger.debug("Token extracted successfully from Authorization header")
    return token