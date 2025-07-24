import sys
import os
import pytest
import json
from app.core.workflow import Workflow
from app.models.interface.workflow_interface import IProject
from app.enums.status_node import StatusNode


# Exemple de JSON
example_json = """
{
    "schema": {
    
        "nodes": [
            {
                "id": "966f9ebf2e02ba87",
                "type": "ExampleInput",
                "label": "ExampleInput",
                "revision": "",
                "data": {"status": 2},
                "outputs": {
                    "consequent": {"id": "e6cb939fd5b37f76", "label": "Colonne", "socket": {"name": "SimpleFieldSocket"}},
                    "alternate": {"id": "6df478f55155efdc", "label": "Full", "socket": {"name": "FlatObjectSocket"}},
                    "solo": {"id": "43014883639e57bf", "label": "Solo", "socket": {"name": "FlatObjectSocket"}}
                },
                "inputs": {},
                "controls": {"status": null}
            },
            {
                "id": "6b6f34ea26e30ff7",
                "type": "ExampleOutput",
                "label": "ExampleOutput",
                "revision": "",
                "data": {"status": 2},
                "outputs": {},
                "inputs": {
                    "oneColonne": {"id": "e2a70e9539fa83d1", "label": "Colonne", "socket": {"name": "SimpleFieldSocket"}},
                    "flatObject": {"id": "5f9e43225d91daee", "label": "Full", "socket": {"name": "FlatObjectSocket"}}
                },
                "controls": {"status": null}
            },
            {
                "id": "26e9e6fe0c499568",
                "type": "ExampleTransform",
                "label": "ExampleTransform",
                "revision": "",
                "data": {"status": 2, "statusMessage": "Good to launch"},
                "outputs": {
                    "alternate": {"id": "ede5e013abdeab94", "label": "Full", "socket": {"name": "FlatObjectSocket"}},
                    "new": {"id": "9023c73b2aa440b0", "label": "Lrs", "socket": {"name": "DeepObjectSocket"}}
                },
                "inputs": {
                    "colonne": {"id": "28baadfc3c391674", "label": "Colonne", "socket": {"name": "SimpleFieldSocket"}},
                    "consequent": {"id": "6fc7ca756d425ca2", "label": "Full", "socket": {"name": "FlatObjectSocket"}}
                },
                "controls": {"status": null}
            }
        ],
        "connections": [
            {"id": "16453a3ba7d29090", "sourceNode": "966f9ebf2e02ba87", "targetNode": "26e9e6fe0c499568", "sourcePort": "consequent", "targetPort": "colonne"},
            {"id": "6bb5e665a11b47d5", "sourceNode": "26e9e6fe0c499568", "targetNode": "6b6f34ea26e30ff7", "sourcePort": "alternate", "targetPort": "flatObject"}
        ],
        "revision": ""
    },
    "dataConnectors": [],
    "name":"Test",
    "revision": "",
    "id":"1"
}
"""

exampleJsonUnknowNode = """{
    "schema": {
        "nodes": [
            {
                "id": "966f9ebf2e02ba87",
                "type": "UnknowInput",
                "label": "ExampleInput",
                "revision": "",
                "data": {"status": 2},
                "outputs": {
                    "consequent": {"id": "e6cb939fd5b37f76", "label": "Colonne", "socket": {"name": "SimpleFieldSocket"}},
                    "alternate": {"id": "6df478f55155efdc", "label": "Full", "socket": {"name": "FlatObjectSocket"}},
                    "solo": {"id": "43014883639e57bf", "label": "Solo", "socket": {"name": "FlatObjectSocket"}}
                },
                "inputs": {},
                "controls": {"status": null}
            }
        ],
        "connections": [],
        "revision": ""
    },
    "dataConnectors": [],
    "name":"Test",
    "revision": "",
    "id":"1"
}"""

def test_import_project():
    workflow = Workflow()
    example_project = IProject.model_validate_json(example_json)
    workflow.import_project(example_project)
    assert workflow.project == example_project
    assert len(workflow.nodes) == 3
    
@pytest.mark.asyncio
async def test_execute_workflow():
    workflow = Workflow()
    example_project = IProject.model_validate_json(example_json)
    workflow.import_project(example_project)
    await workflow.execute_workflow()
    assert os.path.exists('output.sql')
    os.remove('output.sql')

@pytest.mark.asyncio
async def test_execute_workflow_target():
    workflow = Workflow()
    example_project = IProject.model_validate_json(example_json)
    workflow.import_project(example_project)
    await workflow.execute_workflow("26e9e6fe0c499568")
    updated_project = workflow.export_updated_project()
    assert updated_project.pschema.nodes[0].data['status'] == StatusNode.Valid
    assert updated_project.pschema.nodes[1].data['status'] == StatusNode.Complete
    assert updated_project.pschema.nodes[2].data['status'] == StatusNode.Valid
    
@pytest.mark.asyncio
async def test_export_updated_project():
    workflow = Workflow()
    example_project = IProject.model_validate_json(example_json)
    workflow.import_project(example_project)
    await workflow.execute_workflow()
    assert os.path.exists('output.sql')
    os.remove('output.sql')
    updated_project = workflow.export_updated_project()
    assert updated_project.pschema.nodes[0].data['status'] == StatusNode.Valid
    assert updated_project.pschema.nodes[1].data['status'] == StatusNode.Valid
    assert updated_project.pschema.nodes[2].data['status'] == StatusNode.Valid
   

def test_import_project_unknow_node():
    workflow = Workflow()
    example_project = IProject.model_validate_json(exampleJsonUnknowNode)       
    with pytest.raises(ValueError , match='Unknown node type: UnknowInput'):   
        workflow.import_project(example_project)


