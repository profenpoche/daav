from __future__ import annotations
from typing import ForwardRef, Optional, Any, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict, PrivateAttr
from app.core.connection_node import ConnectionNode
from typing import List

from app.models.interface.node_data import NodeData
if TYPE_CHECKING:
    from app.nodes.node import Node

class NodeOutput(BaseModel):
    """Class representing an output node in a workflow.
    
    Attributes:
        id (str): Unique identifier for the output node
        _parent_node (Node): Reference to the parent node
        _parquet_url (Optional[str]): URL to parquet file
        _parquet_schema (Optional[str]): Schema of parquet data
        _rawData (Optional[Any]): Raw data stored in the output
        connections (List[ConnectionNode]): List of connections to other nodes
    """

    id: str
    _parent_node: 'Node' = PrivateAttr()
    _nodeData: NodeData = PrivateAttr(None)
    connections: Optional[List[ConnectionNode]] = None

    def __init__(self, id: str, parent_node: 'Node'):
        """Initialize a new NodeOutput instance.

        Args:
            id (str): Unique identifier for the output node
            parent_node (Node): Reference to the parent node
        """
        super().__init__(id=id)
        self._parent_node = parent_node
        self.connections = []

    def _is_owner(self, node: 'Node') -> bool:
        """Check if the given node is the owner of this output.

        Args:
            node (Node): Node to check ownership for

        Returns:
            bool: True if the node is the owner, False otherwise
        """
        return self._parent_node and self._parent_node.id == node.id

    def set_node_data(self, data: NodeData, node: 'Node') -> None:
        """Set raw data for this output.

        Args:
            data (Any): Data to store
            node (Node): Node attempting to set the data

        Raises:
            PermissionError: If the node is not the owner
        """
        if self._is_owner(node):
            self._nodeData = data
        else:
            raise PermissionError("Only the owner node can modify raw data")

    def get_node_data(self) -> NodeData:
        """Get the stored node data.

        Returns:
            Any: The stored node data
        """
        return self._nodeData  

    def get_connected_nodes(self):
        return [connection.target_node for connection in self.connections]


    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )    
NodeOutput.model_rebuild(raise_errors=False)