import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';

import { InputAutoCompleteWidgetComponent } from './input-auto-complete-widget.component';

describe('InputAutoCompleteWidgetComponent', () => {
  let component: InputAutoCompleteWidgetComponent;
  let fixture: ComponentFixture<InputAutoCompleteWidgetComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ InputAutoCompleteWidgetComponent ],
      imports: [IonicModule.forRoot()]
    }).compileComponents();

    fixture = TestBed.createComponent(InputAutoCompleteWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
