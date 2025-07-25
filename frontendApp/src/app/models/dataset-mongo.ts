import { DatasetType } from "../enums/dataset-type";
import { Dataset } from "./dataset";
import { DatasetsI } from "./datasets-i";

export class DatasetMongo extends Dataset {
    uri: string;
    database: string;
    collection: string;

    constructor(dataset?: DatasetsI) {
        super(dataset);
        this.type = DatasetType.Mongo;
        if (dataset) {
            this.uri = dataset.uri;
            this.database = dataset.database;
            this.collection = dataset.collection;
        }
    }
}
