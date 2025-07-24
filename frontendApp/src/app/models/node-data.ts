import { MysqlSchema, PandasSchema , ParquetSchema} from "./dataset-schema";

/**
 * Generic interface representing node data produce by an output
 * @template T - The type of the schema.
 */
export interface NodeData<T> {
  /** Example data of any type. */
  type: string;
  dataExample: any;
  /** Schema of type T. */
  nodeSchema: T;
  /** Name of the node. */
  name: string;
}

/**
 * Interface representing MySQL node data.
 * Extends NodeData with MysqlSchema.
 */
export interface NodeDataMysql extends NodeData<MysqlSchema> {
  /** typeguard */
  type: 'mysql';
  /** Name of the database. */
  database: string;
  /** Name of the table. */
  table: string;
  /** Datasource Unique identifier. */
  datasetId: string;
}


/**
 * Interface representing Panda Dataframe node data.
 * Extends NodeData with PandaSchema.
 */
export interface NodeDataPandasDf extends NodeData<PandasSchema> {
  /** typeguard */
  type: 'pandasdf';
}

export interface NodeDataParquet extends NodeData<ParquetSchema> {
  /** typeguard */ 
  type: 'parquet';
}


export interface NodeDataJson extends NodeData<any> {
  /** typeguard */
  type: 'json';
}


export interface NodeDataFile extends NodeData<any> {
  /** typeguard */
  type: 'file';
}



