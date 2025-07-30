import json
from typing import Annotated, Optional
from fastapi import APIRouter, HTTPException, Query, Request, Header
from app.services.dataset_service import DatasetService
from app import main
import os
from fastapi.responses import JSONResponse

from app.services.workflow_service import WorkflowService
from app.utils.utils import filter_data_with_duckdb


router = APIRouter(prefix="/api", tags=["api"])

dataset_service = DatasetService()
workflow_service = WorkflowService()

UPLOADS_DIR = os.path.join("app", "uploads")

@router.get("/{custom_path}")
async def get_output_from_custom_path(
        custom_path: str, 
        request: Request, 
        token: str,
        select: Optional[str] = Query(None, description="Columns to select, comma separated"),
        where: Optional[str] = Query(None, description="WHERE clause conditions") 
    ):
    workflows = await workflow_service.get_workflows()
    node = None
    for wf in workflows:
        for wf_node in wf.pschema.nodes:
            if ((wf_node.type == "ApiOutput") and 
                wf_node.data.get("urlInput", {}).get("value") == custom_path):
                node = wf_node
                tokenInput = wf_node.data.get("tokenInput", {}).get("value")
                break
        if node:
            break

    if node is None:
        raise HTTPException(status_code=404, detail="No data found with this URL")
    if token != tokenInput:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    node_id = node.id
    file_path = os.path.join(UPLOADS_DIR, f"{node_id}-output.json")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Output file not found")

    try:
        data = filter_data_with_duckdb(file_path, select, where)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading output file: {str(e)}")

@router.get("/workflow/{workflow_id}")
async def get_workflow_output(workflow_id: str, select: Optional[str] = Query(None, description="Columns to select, comma separated"),
    where: Optional[str] = Query(None, description="WHERE clause conditions")):

    workflow = await workflow_service.get_workflow(workflow_id)
    
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    api_node = None
    for node in workflow.pschema.nodes:
            if node.type == "ApiOutput":
                api_node = node
                break
    if api_node is None:
        raise HTTPException(status_code=400, detail="ApiOutput node not found")
    
    node_id = api_node.id
    file = os.path.join(UPLOADS_DIR, f"{node_id}-output.json")

    if not os.path.isfile(file):
        raise HTTPException(status_code=404, detail=f"Unkown file")

    try:
        data = filter_data_with_duckdb(file, select, where)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Can't read the file : {str(e)}")

        
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