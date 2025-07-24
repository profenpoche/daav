from typing import Optional,Any

from pydantic import ConfigDict
from app.nodes.node import Node
from app.enums.status_node import StatusNode

class OutputNode(Node):

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new OutputNode instance.

        Args:
            data (Any): Data associated with the node
            id (str): Unique identifier for the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)   
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )    


