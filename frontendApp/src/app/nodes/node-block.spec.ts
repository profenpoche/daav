import { AreaPlugin } from 'rete-area-plugin';
import { Schemes } from '../core/workflow-editor';
import { NodeBlock } from './node-block';
import { StatusNode } from '../enums/status-node';

// Classe concrète pour les tests
class TestNodeBlock extends NodeBlock {
  override getRevision(): string {
    throw new Error('Method not implemented.');
  }
  constructor(label: string, area: AreaPlugin<Schemes, any>) {
    super(label, area);
  }
}

describe('NodeBlock', () => {
  let area: AreaPlugin<any, any>;

  beforeEach(() => {
    const container = document.createElement('div');
    area = new AreaPlugin<Schemes, never>(container);
  });

  it('should create an instance', () => {
    expect(new TestNodeBlock('label', area)).toBeTruthy();
  });

  it('should initialize with default values', () => {
    const nodeBlock = new TestNodeBlock('label', area);
    expect(nodeBlock.status).toBe(StatusNode.Incomplete);
    expect(nodeBlock.statusMessage).toBeUndefined();
    expect(nodeBlock.errorStacktrace).toBeUndefined();
    expect(nodeBlock.dataOutput.size).toBe(0);
  });

  it('should update status correctly', () => {
    const nodeBlock = new TestNodeBlock('label', area);
    nodeBlock.updateStatus(StatusNode.Complete, 'Completed', ['No errors']);
    expect(nodeBlock.status).toBe(StatusNode.Complete);
    expect(nodeBlock.statusMessage).toBe('Completed');
    expect(nodeBlock.errorStacktrace).toEqual(['No errors']);
  });

  it('should show loader correctly', () => {
    const nodeBlock = new TestNodeBlock('label', area);
    nodeBlock.showLoader(true);
    expect(nodeBlock.nodeLoader.loading).toBe(true);
    nodeBlock.showLoader(false);
    expect(nodeBlock.nodeLoader.loading).toBe(false);
  });

  it('should serialize data correctly', () => {
    const nodeBlock = new TestNodeBlock('label', area);
    nodeBlock.updateStatus(StatusNode.Complete, 'Completed', ['No errors']);
    const data = nodeBlock.data();
    expect(data.status).toBe(StatusNode.Complete);
    expect(data.statusMessage).toBe('Completed');
    expect(data.errorStacktrace).toEqual(['No errors']);
    expect(data.dataOutput).toEqual({});
  });
});
