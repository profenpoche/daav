import { AreaPlugin } from 'rete-area-plugin';
import { Schemes } from 'src/app/core/workflow-editor';
import { DataFileBlock } from './data-file-block';

describe('DataFileBlock', () => {
  it('should create an instance', () => {
    let area: AreaPlugin<any, any>;

    beforeEach(() => {
      const container = document.createElement('div');
      area = new AreaPlugin<Schemes, never>(container);
    });
    expect(new DataFileBlock('label',area)).toBeTruthy();
  });
});
