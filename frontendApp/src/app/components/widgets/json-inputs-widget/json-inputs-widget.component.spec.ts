import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { JsonInputsWidgetComponent, JsonInputsControl } from './json-inputs-widget.component';

describe('JsonInputsWidgetComponent', () => {
  let component: JsonInputsWidgetComponent;
  let fixture: ComponentFixture<JsonInputsWidgetComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ JsonInputsWidgetComponent ],
      imports: [IonicModule.forRoot()]
    }).compileComponents();

    fixture = TestBed.createComponent(JsonInputsWidgetComponent);
    component = fixture.componentInstance;
    component.data = new JsonInputsControl([]);
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
