import { DataConnector } from './data-connector';
import { Schema } from './schema';

export interface Project {
  id: string;
  name: string;
  revision?: string;
  dataConnectors: DataConnector[];
  schema: Schema;
  // Ownership and sharing
  owner_id?: string;
  shared_with?: string[];
}
