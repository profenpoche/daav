import { DatasetType } from "../enums/dataset-type";
import { Dataset } from "./dataset";
import { DatasetsI } from "./datasets-i";

export class DatasetElasticSearch extends Dataset {
    url: string;
    user: string;
    password: string;
    index: string;
    key: string;
    bearerToken: string;

    constructor(dataset?: DatasetsI) {
        super(dataset);
        this.type = DatasetType.ElasticSearch;
        if (dataset) {
            this.url = dataset.url;
            this.user = dataset.user;
            this.password = dataset.password;
            this.index = dataset.index;
            this.key = dataset.key;
            this.bearerToken = dataset.bearerToken;
        }
    }
}
