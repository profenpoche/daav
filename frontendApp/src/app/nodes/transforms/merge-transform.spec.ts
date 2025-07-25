import { MergeTransform } from './merge-transform';
import { AreaPlugin } from 'rete-area-plugin';
import { Node } from 'src/app/models/interfaces/node';
import { StatusNode } from 'src/app/enums/status-node';
import { DataMapperControl } from 'src/app/components/widgets/data-mapper-widget/data-mapper-widget.component';
import { Schemes } from 'src/app/core/workflow-editor';


describe('MergeTransform', () => {
  let area: AreaPlugin<any, any>;

  beforeEach(() => {
    const container = document.createElement('div');
    area = new AreaPlugin<Schemes, never>(container);

    // Améliorer le mock avec plus de détails
    area.parent = {
      getNode: jasmine.createSpy('getNode').and.returnValue({
        label: 'Test Node',
        data: { output: ['someData'] }
      }),
      getConnections: jasmine.createSpy('getConnections').and.returnValue([])
    };
  });

  it('should create an instance', () => {
    const instance = new MergeTransform('Test Label', area);
    expect(instance).toBeTruthy();
  });

  it('should initialize with default values when no node is provided', () => {
    const instance = new MergeTransform('Test Label', area);
    expect(instance.width).toBe(180);
    expect(instance.height).toBe(192);
    expect(instance.dataMapperControl).toBeInstanceOf(DataMapperControl);
    expect(instance.dataMapperControl.mappings).toEqual([]);
    expect(instance.dataMapperControl.datasets).toEqual([]);
  });

  it('should initialize with node data when node is provided', () => {
    const node: Node = {
      id: '1',
      data: {
        dataMapping: [{ source: 'source1', target: 'target1' }],
        datasets: ['dataset1']
      }
    } as Node;
    const instance = new MergeTransform('Test Label', area, node);
    expect(instance.dataMapperControl.mappings).toEqual(node.data.dataMapping);
    expect(instance.dataMapperControl.datasets).toEqual(node.data.datasets);
  });

  it('should update status to Incomplete when no node is provided', () => {
    const instance = new MergeTransform('Test Label', area);
    expect(instance.status).toBe(StatusNode.Incomplete);
  });

  it('should add input and output on connection created', () => {
    const instance = new MergeTransform('Test Label', area);
    const connection = {
      source: 'sourceNode',
      target: instance.id,
      targetInput: 'datasource'
    } as any;

    instance['onConnectionChange'](connection, 'connectioncreated');
    expect(Object.keys(instance.inputs)).toContain('datasource_1');
    expect(Object.keys(instance.outputs)).toContain('out');
  });

  it('should remove input and output on connection removed', () => {
    const instance = new MergeTransform('Test Label', area);
    const connection = {
      id: 'connection1',
      source: 'sourceNode',
      sourceOutput: 'output1',
      target: instance.id,
      targetInput: 'datasource'
    };

    (area.parent.getNode as jasmine.Spy).and.returnValue({
      label: 'Source Node',
      data: { output: ['someData'] }
    });

    instance['onConnectionChange'](connection, 'connectioncreated');
    instance['onConnectionChange'](connection, 'connectionremoved');
    expect(Object.keys(instance.inputs)).not.toContain('datasource_1');
    expect(Object.keys(instance.outputs)).not.toContain('out');
  });

  it('should build dataset on connection created', () => {
    const instance = new MergeTransform('Test Label', area);
    const mockSourceNode = {
      label: 'Source Node',
      id: 'sourceNode',
      data: {
        output: ['someData'],
        schema: {
          get: () => ({ fields: [{ name: 'field1', type: 'string' }] })
        }
      }
    };

    const mockConnection = {
      source: 'sourceNode',
      target: instance.id,
      targetInput: 'datasource',
      sourceOutput: 'output1'
    };

    (area.parent.getNode as jasmine.Spy).and.returnValue(mockSourceNode);
    (area.parent.getConnections as jasmine.Spy).and.returnValue([mockConnection]);

    instance['buildDataset']('connectioncreated');
    expect(instance.dataMapperControl.datasets.length).toBeGreaterThan(0);
  });

  it('should clear datasets and mappings on connection removed', () => {
    const instance = new MergeTransform('Test Label', area);
    instance['buildDataset']('connectionremoved');
    expect(instance.dataMapperControl.datasets).toEqual([]);
    expect(instance.dataMapperControl.mappings).toEqual([]);
  });
});
