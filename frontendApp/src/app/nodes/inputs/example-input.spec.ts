import { Schemes } from 'src/app/core/workflow-editor';
import { ExampleInput } from './example-input';
import { AreaPlugin } from 'rete-area-plugin';

describe('ExempleInput', () => {
  let area: AreaPlugin<any, any>;

  beforeEach(() => {
    const container = document.createElement('div');
    area = new AreaPlugin<Schemes, never>(container);
  });
  it('should create an instance', () => {
    expect(new ExampleInput('label',area)).toBeTruthy();
  });
});
