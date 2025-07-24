import { AreaPlugin } from 'rete-area-plugin';
import { DataMongoBlock } from './data-mongo-block';
import { Schemes } from 'src/app/core/workflow-editor';

describe('DataMongoBlock', () => {
  it('should create an instance', () => {
    let area: AreaPlugin<any, any>;

    beforeEach(() => {
      const container = document.createElement('div');
      area = new AreaPlugin<Schemes, never>(container);
    });
    expect(new DataMongoBlock('label',area)).toBeTruthy();
  });
});
