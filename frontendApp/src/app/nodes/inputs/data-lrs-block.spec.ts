import { Schemes } from 'src/app/core/workflow-editor';
import { DataLrsBlock } from './data-lrs-block';
import { AreaPlugin } from 'rete-area-plugin';

describe('DataLrsBlock', () => {
  it('should create an instance', () => {
    let area: AreaPlugin<any, any>;

    beforeEach(() => {
      const container = document.createElement('div');
      area = new AreaPlugin<Schemes, never>(container);
    });
    expect(new DataLrsBlock('label',area)).toBeTruthy();
  });
});
