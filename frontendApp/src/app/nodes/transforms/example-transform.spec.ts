import { AreaPlugin } from 'rete-area-plugin';
import { ExampleTransform } from './example-transform';
import { Schemes } from 'src/app/core/workflow-editor';

describe('ExempleTransform', () => {
  let area: AreaPlugin<any, any>;

  beforeEach(() => {
    const container = document.createElement('div');
    area = new AreaPlugin<Schemes, never>(container);
  });
  it('should create an instance', () => {
    expect(new ExampleTransform('label',area)).toBeTruthy();
  });
});
