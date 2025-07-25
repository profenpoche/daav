import { NodeEditor } from 'rete';
import { WorkflowNodeEditor } from './workflow-node-editor';
import { Injector } from "@angular/core";

describe('WorkflowNodeEditor', () => {
  let injector: Injector;

  beforeEach(() => {
    injector = jasmine.createSpyObj('Injector', ['get']);
  });

  it('should create an instance', () => {
    const editor = new WorkflowNodeEditor(injector);
    expect(editor).toBeTruthy();
  });

  it('should have an injector', () => {
    const editor = new WorkflowNodeEditor(injector);
    expect(editor.injector).toBe(injector);
  });

  it('should call super constructor', () => {
    spyOn(NodeEditor.prototype, 'constructor' as any);
    const editor = new WorkflowNodeEditor(injector);
    expect(NodeEditor.prototype.constructor).toHaveBeenCalled();
  });
});
