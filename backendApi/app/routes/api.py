import json
from typing import Annotated, Optional
from fastapi import APIRouter, HTTPException, Query, Request, Header
from app.routes.workflows import execute_workflow, import_and_execute_workflow
from app.services.dataset_service import DatasetService
from app import main
from app.core.workflow import Workflow
import os
from fastapi.responses import JSONResponse

from app.services.workflow_service import WorkflowService
from app.utils.drupal_filter_converter import DrupalFilterConverter
from app.utils.utils import filter_data_with_duckdb
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["api"])

dataset_service = DatasetService()
workflow_service = WorkflowService()
drupal_filter_converter = DrupalFilterConverter()

UPLOADS_DIR = os.path.join("app", "uploads")

@router.get("/{custom_path}")
async def get_output_from_custom_path(
        custom_path: str, 
        request: Request, 
        token: Optional[str] = None
    ):
    """
    Get output from custom path by searching through workflows with optional filtering.
    Args:
        custom_path (str): The custom URL path to search for
        request (Request): FastAPI request object containing query parameters
        token (str, optional): Security token to validate access
    Returns:
        JSONResponse: Filtered or unfiltered output data
    Raises:
        HTTPException: 401 if token invalid, 404 if path not found,
                      500 for server errors
    """
    try:
        logger.info(f"Searching for output with custom path: {custom_path}")
        
        # Get all workflows and search for matching node
        workflows = await workflow_service.get_workflows()
        
        # Find ApiOutput node with matching URL and its workflow
        node = None
        workflow = None
        tokenInput = None
        for wf in workflows:
            for wf_node in wf.pschema.nodes:
                if ((wf_node.type == "ApiOutput") and 
                    wf_node.data.get("urlInput", {}).get("value") == custom_path):
                    node = wf_node
                    workflow = wf
                    tokenInput = wf_node.data.get("tokenInput", {}).get("value")
                    break
            if node:
                break

        if node is None:
            logger.warning(f"No ApiOutput node found with URL: {custom_path}")
            raise HTTPException(status_code=404, detail="No data found with this URL")

        # Validate token if required
        if tokenInput and token != tokenInput:
            logger.warning("Invalid token provided")
            raise HTTPException(status_code=401, detail="Invalid token")

        # Construct output file path
        file_path = os.path.join(UPLOADS_DIR, f"{node.id}-output.json")
        
        # Execute workflow if output doesn't exist
        if not os.path.isfile(file_path):
            logger.info(f"Output file not found, executing workflow: {workflow.id}")
            try:
                await import_and_execute_workflow(workflow)
            except Exception as exec_error:
                logger.error(f"Workflow execution failed: {exec_error}", exc_info=True)
                raise HTTPException(
                    status_code=500, 
                    detail=f"Workflow execution failed: {str(exec_error)}"
                )

            if not os.path.isfile(file_path):
                logger.error(f"Output file not generated after execution: {file_path}")
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to generate output file"
                )

        # Apply filters if query parameters exist
        where_clause = None
        params = None
        if request.query_params:
            logger.info(f"Applying filters with parameters: {request.query_params}")
            try:
                where_clause, params = drupal_filter_converter.convert_query_string_to_where(
                    str(request.query_params)
                )
            except Exception as filter_error:
                logger.error(f"Filter parsing failed: {filter_error}", exc_info=True)
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid filter parameters: {str(filter_error)}"
                )

        # Get filtered data
        try:
            data = filter_data_with_duckdb(file_path, where=where_clause, params=params)
            return JSONResponse(content=data)
        except Exception as filter_error:
            logger.error(f"Data filtering failed: {filter_error}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error filtering data: {str(filter_error)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing custom path {custom_path}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/workflow/{workflow_id}")
async def get_workflow_output(workflow_id: str, request: Request, token: str):
    """
    Get workflow output data with optional filtering.
    Args:
        workflow_id (str): The ID of the workflow
        request (Request): FastAPI request object containing query parameters
    Returns:
        JSONResponse: Filtered or unfiltered workflow output data
    """
    try:
        logger.info(f"Getting output for workflow: {workflow_id}")
        
        # Get workflow and validate
        workflow = await workflow_service.get_workflow(workflow_id)
        if not workflow:
            logger.warning(f"Workflow not found: {workflow_id}")
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Find ApiOutput node
        api_node = next(
            (node for node in workflow.pschema.nodes if node.type == "ApiOutput"), 
            None
        )
        if not api_node:
            logger.error(f"No ApiOutput node in workflow: {workflow_id}")
            raise HTTPException(status_code=400, detail="ApiOutput node not found")
    
        # Validate token
        expected_token = api_node.data.get("tokenInput", {}).get("value")
        if token != expected_token:
            logger.warning(f"Invalid token provided for workflow: {workflow_id}")
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Construct output file path
        output_file = os.path.join(UPLOADS_DIR, f"{api_node.id}-output.json")

        # Execute workflow if output doesn't exist
        if not os.path.isfile(output_file):
            logger.info(f"Output file not found, executing workflow: {workflow_id}")
            try:
                await import_and_execute_workflow(workflow)
            except Exception as exec_error:
                logger.error(f"Workflow execution failed: {exec_error}", exc_info=True)
                raise HTTPException(
                    status_code=500, 
                    detail=f"Workflow execution failed: {str(exec_error)}"
                )

            if not os.path.isfile(output_file):
                logger.error(f"Output file not generated after execution: {output_file}")
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to generate output file"
                )

        # Apply filters if query parameters exist
        where_clause = None
        params = None
        if request.query_params:
            logger.info(f"Applying filters with parameters: {request.query_params}")
            try:
                where_clause, params = drupal_filter_converter.convert_query_string_to_where(
                    str(request.query_params)
                )
            except Exception as filter_error:
                logger.error(f"Filter parsing failed: {filter_error}", exc_info=True)
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid filter parameters: {str(filter_error)}"
                )

        # Get filtered data
        try:
            data = filter_data_with_duckdb(output_file, where=where_clause, params=params)
            return JSONResponse(content=data)
        except Exception as filter_error:
            logger.error(f"Data filtering failed: {filter_error}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail=f"Error filtering data: {str(filter_error)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
      
def verify_bearer(request, expected_token: str):
    try:
        if "Authorization" not in request.headers :
            raise HTTPException(
                        status_code=401, 
                        detail='Authorization header missing')
        token = get_token_auth_header(request.headers["Authorization"])
        if(token != expected_token):
            raise HTTPException(
                status_code=401,
                detail= "Invalid token")
    except Exception as e:    
        raise HTTPException(
            status_code=401,
            detail= e.message  if hasattr(e, 'message') else str(e))
def get_token_auth_header(authorization):
    parts = authorization.split()

    if parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401, 
            detail='Authorization header must start with Bearer')
    elif len(parts) == 1:
        raise HTTPException(
            status_code=401, 
            detail='Authorization token not found')
    elif len(parts) > 2:
        raise HTTPException(
            status_code=401, 
            detail='Authorization header be Bearer token')
    
    token = parts[1]
    return token



