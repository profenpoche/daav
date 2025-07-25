import { AreaPlugin } from 'rete-area-plugin';
import { Schemes } from 'src/app/core/workflow-editor';
import { ExampleOutput } from './example-output';

describe('ExampleOutput', () => {
  let area: AreaPlugin<any, any>;

  beforeEach(() => {
    const container = document.createElement('div');
    area = new AreaPlugin<Schemes, never>(container);
  });
  it('should create an instance', () => {
    expect(new ExampleOutput('label',area)).toBeTruthy();
  });
});
