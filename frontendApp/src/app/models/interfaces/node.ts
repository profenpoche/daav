import { NodeControl } from './node-control';
import { NodePort } from './node-port';

export interface Node {
  id: string;
  type: string;
  label : string
  inputs: NodePort[];
  outputs: NodePort[];
  controls: NodeControl[];
  revision? : string;
  data?:any;
  position?: {x: number, y : number};
}
