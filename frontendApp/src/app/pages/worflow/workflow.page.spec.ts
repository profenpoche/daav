import { ComponentFixture, TestBed } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';
import { WorkflowPage } from './workflow.page';

describe('WorkflowPage', () => {
  let component: WorkflowPage;
  let fixture: ComponentFixture<WorkflowPage>;

  beforeEach(async () => {
    const activatedRouteSpy = {
      params: of({ id: 'test' }),
      snapshot: { params: { id: 'test' } },
      paramMap: of({ get: (key: string) => 'test' }),
      queryParams: of({ projectId: 'test' })
    };

    await TestBed.configureTestingModule({
      declarations: [WorkflowPage],
      imports: [IonicModule.forRoot(), HttpClientTestingModule],
      providers: [
        { provide: ActivatedRoute, useValue: activatedRouteSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(WorkflowPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
