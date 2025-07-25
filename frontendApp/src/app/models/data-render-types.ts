import { Dataset } from 'src/app/models/dataset';
import { Pagination } from './dataset-content-response';

export interface DataRenderTypes {
    dbNames: Array<string> | null,
    tableNames: Array<string[]> | Array<string> | null,
    displayedColumns: Array<string> | null,
    fiche: { items: Array<string> | null, limit: number | null, total: number | null, current_page: number | null,  nextUrl?: string | null,  prevUrl?: string | null} | null,
    selectedDataset: Dataset | null,
    renderTabIndex: number,
    pagination: Pagination,
    datasetParams: { database: string, table: string },
}
