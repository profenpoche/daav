import { AreaPlugin } from 'rete-area-plugin';
import { OutputDataBlock } from './output-data-block';
import { Schemes } from 'src/app/core/workflow-editor';

describe('OutputDataBlock', () => {
  let area: AreaPlugin<any, any>;

  beforeEach(() => {
    const container = document.createElement('div');
    area = new AreaPlugin<Schemes, never>(container);
  });
  it('should create an instance', () => {
    expect(new OutputDataBlock('label',area)).toBeTruthy();
  });
});
