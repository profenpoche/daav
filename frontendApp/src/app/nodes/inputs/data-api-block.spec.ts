import { AreaPlugin } from 'rete-area-plugin';
import { Schemes } from 'src/app/core/workflow-editor';
import { DataApiBlock } from './data-api-block';

describe('DataApiBlock', () => {
  it('should create an instance', () => {
    let area: AreaPlugin<any, any>;

    beforeEach(() => {
      const container = document.createElement('div');
      area = new AreaPlugin<Schemes, never>(container);
    });
    expect(new DataApiBlock('label',area)).toBeTruthy();
  });
});
