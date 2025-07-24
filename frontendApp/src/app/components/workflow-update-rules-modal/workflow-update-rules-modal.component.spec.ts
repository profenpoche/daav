import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';

import { WorkflowUpdateRulesModalComponent } from './workflow-update-rules-modal.component';

describe('WorkflowUpdateRulesModalComponent', () => {
  let component: WorkflowUpdateRulesModalComponent;
  let fixture: ComponentFixture<WorkflowUpdateRulesModalComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ WorkflowUpdateRulesModalComponent ],
      imports: [IonicModule.forRoot()]
    }).compileComponents();

    fixture = TestBed.createComponent(WorkflowUpdateRulesModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
