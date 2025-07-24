
import { DataMapperUtils } from './data-mapper-types';
import { NodeDataMysql } from './node-data';

describe('DataMapperUtils', () => {
  it('should transform NodeDataMysql to DatasetMapper', () => {
    const nodeData: NodeDataMysql = {
      type: 'mysql',
      name: 'testNode',
      nodeSchema: [
        {
          Field: 'id', Type: 'int',
          Null: '',
          Key: '',
          Default: undefined,
          Extra: ''
        },
        {
          Field: 'name', Type: 'varchar',
          Null: '',
          Key: '',
          Default: undefined,
          Extra: ''
        },
        {
          Field: 'email', Type: 'varchar',
          Null: '',
          Key: '',
          Default: undefined,
          Extra: ''
        },
        {
          Field: 'created_at', Type: 'datetime',
          Null: '',
          Key: '',
          Default: undefined,
          Extra: ''
        },
      ],
      dataExample: [
        { id: 1, name: 'John Doe', email: 'john@example.com', created_at: '2023-01-01' },
        { id: 2, name: 'Jane Doe', email: 'jane@example.com', created_at: '2023-01-02' },
      ],
      database: '',
      table: '',
      datasetId: ''
    };

    const result = DataMapperUtils.nodeDataToMapper(nodeData, 'sourceKey');

    expect(result).toEqual({
      id: 'sourceKey',
      name: 'testNode',
      columns: [
        {
          id: 'id',
          name: 'id',
          type: 'id',
          sample: [1, 2],
          datasetId: 'sourceKey',
        },
        {
          id: 'name',
          name: 'name',
          type: 'string',
          sample: ['John Doe', 'Jane Doe'],
          datasetId: 'sourceKey',
        },
        {
          id: 'email',
          name: 'email',
          type: 'email',
          sample: ['john@example.com', 'jane@example.com'],
          datasetId: 'sourceKey',
        },
        {
          id: 'created_at',
          name: 'created_at',
          type: 'date',
          sample: ['2023-01-01', '2023-01-02'],
          datasetId: 'sourceKey',
        },
      ],
    });
  });

  it('should detect correct DataType for MySQL fields', () => {
    expect(DataMapperUtils.detectTypeFieldMysql('int', '1', 'id')).toBe('id');
    expect(DataMapperUtils.detectTypeFieldMysql('varchar', 'john@example.com', 'email')).toBe('email');
    expect(DataMapperUtils.detectTypeFieldMysql('varchar', 'https://example.com', 'url')).toBe('url');
    expect(DataMapperUtils.detectTypeFieldMysql('varchar', '123-456-7890', 'phone')).toBe('phone');
    expect(DataMapperUtils.detectTypeFieldMysql('varchar', '50%', 'percentage')).toBe('percentage');
    expect(DataMapperUtils.detectTypeFieldMysql('datetime', '2023-01-01', 'created_at')).toBe('date');
    expect(DataMapperUtils.detectTypeFieldMysql('tinyint(1)', '1', 'is_active')).toBe('boolean');
    expect(DataMapperUtils.detectTypeFieldMysql('varchar', 'some text', 'description')).toBe('string');
  });
});
