import { DatasetApi } from './dataset-api';
import { DatasetType } from '../enums/dataset-type';
import { DatasetsI } from './datasets-i';
import { Folder } from './folder';
describe('DatasetApi', () => {
  it('should create an instance', () => {
    const datasetApi = new DatasetApi();
    expect(datasetApi).toBeTruthy();
  });

  it('should set type to API', () => {
    const datasetApi = new DatasetApi();
    expect(datasetApi.type).toBe(DatasetType.API);
  });

  it('should initialize properties from dataset', () => {
    const dataset: DatasetsI = {
      url: 'http://example.com',
      bearerToken: 'token',
      apiAuth: 'auth',
      clientId: 'clientId',
      clientSecret: 'clientSecret',
      authUrl: 'http://auth.com',
      basicToken: 'basicToken',
      id: '',
      name: '',
      description: '',
      parentFolder: new Folder,
      type: DatasetType.Mongo,
      folder: '',
      inputType: '',
      filePath: '',
      fileSize: '',
      fileType: '',
      modifTime: '',
      accessTime: '',
      columnCount: '',
      rowCount: '',
      csvHeader: '',
      csvDelimiter: '',
      file: undefined,
      uri: '',
      database: '',
      collection: '',
      host: '',
      user: '',
      password: '',
      table: '',
      index: '',
      username: '',
      key: ''
    };
    const datasetApi = new DatasetApi(dataset);
    expect(datasetApi.url).toBe(dataset.url);
    expect(datasetApi.bearerToken).toBe(dataset.bearerToken);
    expect(datasetApi.apiAuth).toBe(dataset.apiAuth);
    expect(datasetApi.clientId).toBe(dataset.clientId);
    expect(datasetApi.clientSecret).toBe(dataset.clientSecret);
    expect(datasetApi.authUrl).toBe(dataset.authUrl);
    expect(datasetApi.basicToken).toBe(dataset.basicToken);
  });

  it('should handle undefined dataset', () => {
    const datasetApi = new DatasetApi(undefined);
    expect(datasetApi.url).toBeUndefined();
    expect(datasetApi.bearerToken).toBeUndefined();
    expect(datasetApi.apiAuth).toBeUndefined();
    expect(datasetApi.clientId).toBeUndefined();
    expect(datasetApi.clientSecret).toBeUndefined();
    expect(datasetApi.authUrl).toBeUndefined();
    expect(datasetApi.basicToken).toBeUndefined();
  });
});

