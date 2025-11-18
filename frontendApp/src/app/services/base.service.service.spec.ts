import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { BaseService } from './base.service.service';

describe('BaseServiceService', () => {
  let service: BaseService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(BaseService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
