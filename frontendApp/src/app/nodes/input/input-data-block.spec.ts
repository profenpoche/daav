import { AreaPlugin } from 'rete-area-plugin';
import { Schemes } from 'src/app/core/workflow-editor';
import { InputDataBlock } from './input-data-block';

describe('InputDataBlock', () => {
  it('should create an instance', () => {
    let area: AreaPlugin<any, any>;

    beforeEach(() => {
      const container = document.createElement('div');
      area = new AreaPlugin<Schemes, never>(container);
    });
    expect(new InputDataBlock('label',area)).toBeTruthy();
  });
});
