import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { DatasetService } from './dataset.service';

describe('DatasetService', () => {
  let service: DatasetService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(DatasetService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
