import { WorkflowEditor } from './workflow-editor';
import { Injector } from '@angular/core';
import { Project } from '../models/interfaces/project';
describe('WorkflowEditor', () => {
  let container: HTMLElement;
  let injector: Injector;
  let workflowEditor: WorkflowEditor;

  beforeEach(() => {
    container = document.createElement('div');
    injector = {} as Injector;
    workflowEditor = new WorkflowEditor(container, injector);
  });

  it('should create an instance', () => {
    expect(workflowEditor).toBeTruthy();
  });

  it('should import a project', async () => {
    const project: Project = {
      id: '1',
      name: 'Test Project',
      revision: '1',
      schema: { nodes: [], connections: [], revision: null },
      dataConnectors: []
    };

    await workflowEditor.importProject(project);
    expect(workflowEditor.project).toEqual(project);
  });

  it('should export a project', () => {
    const project: Project = {
      id: '1',
      name: 'Test Project',
      revision: '1',
      schema: { nodes: [], connections: [], revision: null },
      dataConnectors: []
    };

    workflowEditor.importProject(project);
    const exportedProject = workflowEditor.exportProject();
    expect(exportedProject).toEqual(project);
  });

  it('should save a project', () => {
    const project: Project = {
      id: '1',
      name: 'Test Project',
      revision: '1',
      schema: { nodes: [], connections: [], revision: null },
      dataConnectors: []
    };

    workflowEditor.importProject(project);
    workflowEditor.saveProject();
    expect(workflowEditor.project).toEqual(project);
  });
});
