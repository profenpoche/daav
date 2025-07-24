import { AreaPlugin } from 'rete-area-plugin';
import { MysqlOutput } from './mysql-output';
import { Schemes } from 'src/app/core/workflow-editor';

describe('MysqlOutput', () => {
  let area: AreaPlugin<any, any>;
  beforeEach(() => {
    const container = document.createElement('div');
    area = new AreaPlugin<Schemes, never>(container);
  });

  it('should create an instance', () => {
    expect(new MysqlOutput('label', area)).toBeTruthy();
  });
});
