import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { MatDialogRef } from '@angular/material/dialog';

import { WorkflowUpdateRulesModalComponent } from './workflow-update-rules-modal.component';

describe('WorkflowUpdateRulesModalComponent', () => {
  let component: WorkflowUpdateRulesModalComponent;
  let fixture: ComponentFixture<WorkflowUpdateRulesModalComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [IonicModule.forRoot(), WorkflowUpdateRulesModalComponent],
      providers: [
        { provide: MatDialogRef, useValue: jasmine.createSpyObj('MatDialogRef', ['close']) }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(WorkflowUpdateRulesModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
