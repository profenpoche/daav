import { DatasetType } from "../enums/dataset-type";
import { Dataset } from "./dataset";
import { DatasetsI } from "./datasets-i";

export class DatasetApi extends Dataset {
    url: string;
    bearerToken: string;
    apiAuth: string;
    clientId: string;
    clientSecret: string;
    authUrl: string;
    basicToken: string;

    constructor(dataset?: DatasetsI) {
        super(dataset);
        this.type = DatasetType.API;
        if (dataset) {
            this.url = dataset.url;
            this.bearerToken = dataset.bearerToken;
            this.apiAuth = dataset.apiAuth;
            this.clientId = dataset.clientId;
            this.clientSecret = dataset.clientSecret;
            this.authUrl = dataset.authUrl;
            this.basicToken = dataset.basicToken;
        }
    }
}
