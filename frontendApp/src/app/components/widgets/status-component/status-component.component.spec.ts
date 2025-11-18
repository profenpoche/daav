import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { MatTooltipModule } from '@angular/material/tooltip';
import { StatusComponentComponent } from './status-component.component';
import { StatusControl } from './status-component.component';
import { StatusNode } from 'src/app/enums/status-node';

describe('StatusComponentComponent', () => {
  let component: StatusComponentComponent;
  let fixture: ComponentFixture<StatusComponentComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ StatusComponentComponent ],
      imports: [IonicModule.forRoot(), MatTooltipModule]
    }).compileComponents();

    fixture = TestBed.createComponent(StatusComponentComponent);
    component = fixture.componentInstance;
    component.data = new StatusControl(StatusNode.Valid, 'Test message', []);
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
