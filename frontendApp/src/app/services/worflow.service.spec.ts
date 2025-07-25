import { TestBed } from '@angular/core/testing';

import { WorkflowService } from './worflow.service';

describe('WorflowService', () => {
  let service: WorkflowService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(WorkflowService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
