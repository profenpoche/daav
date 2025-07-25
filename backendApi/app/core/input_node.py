from __future__ import annotations
from typing import Optional, Any, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict, PrivateAttr
from app.core.connection_node import ConnectionNode
from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeData
if TYPE_CHECKING:
    from app.nodes.node import Node


class NodeInput(BaseModel):
    """Class representing an input node in a workflow.
    
    Attributes:
        id (str): Unique identifier for the input node
        _parent_node (Node): Reference to the parent node
        connection (Optional[ConnectionNode]): Connection to another node
    """

    id: str
    _parent_node: 'Node' = PrivateAttr()  # Use string literal for forward reference
    connection: Optional[ConnectionNode] = None

    def __init__(self, id: str, parent_node: 'Node'):
        """Initialize a new NodeInput instance.

        Args:
            id (str): Unique identifier for the input node
            _parent_node (Node): Reference to the parent node
        """
        super().__init__(id=id)
        self._parent_node = parent_node

    def _is_owner(self, node: 'Node') -> bool:
        """Check if the given node is the owner of this input.

        Args:
            node (Node): Node to check ownership for

        Returns:
            bool: True if the node is the owner, False otherwise
        """
        return self._parent_node and self._parent_node.id == node.id


    def get_node_data(self) -> NodeData:
        """Get the stored raw data.

        Returns:
            Any: The stored raw data
        """
        if not self.connection:
            raise ValueError(f"Cannot get node data: no connection available {self._parent_node.id}")
    
        if (self.connection.source_node.status == StatusNode.Valid):
            return self.connection.source_port.get_node_data()
        else:
            raise ValueError("Cannot get node data: parent node is not valid")        

    def get_connected_node(self):
        if self.connection:
            return self.connection.source_node


    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )