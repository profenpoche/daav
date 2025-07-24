import { AreaPlugin } from 'rete-area-plugin';
import { MongoOutput } from './mongo-output';
import { Schemes } from 'src/app/core/workflow-editor';

describe('MongoOutput', () => {
  let area: AreaPlugin<any, any>;
  beforeEach(() => {
    const container = document.createElement('div');
    area = new AreaPlugin<Schemes, never>(container);
  });

  it('should create an instance', () => {
    expect(new MongoOutput('label', area)).toBeTruthy();
  });
});

