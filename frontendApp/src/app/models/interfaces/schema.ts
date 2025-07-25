import { Node } from "./node"
import { NodeConnection } from "./node-connection"

  export interface Schema {
    nodes : Node[]
    connections : NodeConnection[]
    revision? : string
  }
