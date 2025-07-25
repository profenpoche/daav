import { ComponentFixture, TestBed } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { WorkflowPage } from './workflow.page';

describe('WorkflowPage', () => {
  let component: WorkflowPage;
  let fixture: ComponentFixture<WorkflowPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [WorkflowPage],
      imports: [IonicModule.forRoot()]
    }).compileComponents();

    fixture = TestBed.createComponent(WorkflowPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
