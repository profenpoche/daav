import { DatasetsI } from "./datasets-i";

export abstract class DatasetMetadata {
    fileSize: string;
    fileType: string;
    modifTime: string;
    accessTime: string;
    columnCount: string;
    rowCount: string;

    constructor(dataset?: DatasetsI) {
        if (dataset) {            
            this.fileSize = dataset.metadata.fileSize;
            this.fileType = dataset.metadata.fileType;
            this.modifTime = dataset.metadata.modifTime;
            this.accessTime = dataset.metadata.accessTime;
            this.columnCount = dataset.metadata.columnCount;
            this.rowCount = dataset.metadata.rowCount;
        }
    }

}
