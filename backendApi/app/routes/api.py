import json
from typing import Annotated, Optional
from fastapi import APIRouter, HTTPException, Request, Header
from app.services.dataset_service import DatasetService
from app import main
import os
from fastapi.responses import JSONResponse

from app.services.workflow_service import WorkflowService


router = APIRouter(prefix="/api", tags=["api"])

dataset_service = DatasetService()
workflow_service = WorkflowService()

@router.get("/{custom_path}")
async def get_output_from_custom_path(custom_path: str, request: Request):
    workflows = await workflow_service.get_workflows()
    node = next(
        (
            node
            for wf in workflows
            for node in wf.get("pschema", {}).get("nodes", [])
            if node.get("type") == "ApiOutput"
            and node.get("data", {}).get("urlInput", {}).get("value") == custom_path
        ),
        None
    )

    if node is None:
        raise HTTPException(status_code=404, detail="No data found with this URL")

    expected_token = node.get("data", {}).get("tokenInput", {}).get("value")
    verify_bearer(request, expected_token)

    node_id = node["id"]
    file_path = f"{node_id}-output.json"
    print(file_path)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Output file not found")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading output file: {str(e)}")

@router.get("/workflow/{workflow_id}")
async def get_workflow_output(workflow_id: str , request: Request):

    workflows = await workflow_service.get_workflows()
    
    workflow = next((wf for wf in workflows if wf['id'] == workflow_id), None)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    api_node = next(
        (node for node in workflow["pschema"]["nodes"] if node.get("type") == "ApiOutput"),
        None
    )
    if api_node is None:
        raise HTTPException(status_code=400, detail="ApiOutput node not found")
    
    expected_token = api_node.get("data", {}).get("tokenInput", {}).get("value")
    verify_bearer(request, expected_token)

    node_id = api_node["id"]
    file = f"{node_id}-output.json"

    if not os.path.isfile(file):
        raise HTTPException(status_code=404, detail=f"Unkown file")

    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
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