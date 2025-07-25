import { DatasetType } from "src/app/enums/dataset-type";
import { DatasetsI } from "../datasets-i";


  export interface DataConnector  extends DatasetsI {
    revision : string
  }
