import { FileDashboardComponent } from "../components/dashboards/file-dashboard/file-dashboard.component";
import { DatasetType } from "../enums/dataset-type";
import { Dataset } from "./dataset";
import { DatasetMetadata } from "./dataset-metadata";
import { DatasetsI } from "./datasets-i";

export class DatasetFile extends Dataset {
    filePath: string;
    file: File;
    folder: string;
    inputType: string;
    csvHeader: string;
    csvDelimiter: string | null;
    metadata: DatasetMetadata;
    ifExist : 'replace' | 'append'; // Default behavior

    constructor(dataset?: DatasetsI) {
        super(dataset);
        this.type = DatasetType.FilePath;
        this.dashboardComponent = FileDashboardComponent;
        this.ifExist = 'replace'; // Default behavior
        if (dataset) {
            this.filePath = dataset.filePath;
            this.file = dataset.file;
            this.folder = dataset.folder;
            this.inputType = dataset.inputType;
            this.csvHeader = dataset.csvHeader;
            this.csvDelimiter = dataset.csvDelimiter;
            this.metadata = dataset.metadata;
            this.ifExist = dataset.ifExist || 'replace';
        }
    }

}
