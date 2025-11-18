import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { DataMapperWidgetComponent, DataMapperControl } from './data-mapper-widget.component';
import { HasDatasetsPipe } from 'src/app/models/data-mapper-types';

describe('DataMapperWidgetComponent', () => {
  let component: DataMapperWidgetComponent;
  let fixture: ComponentFixture<DataMapperWidgetComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ DataMapperWidgetComponent, HasDatasetsPipe ],
      imports: [IonicModule.forRoot()]
    }).compileComponents();

    fixture = TestBed.createComponent(DataMapperWidgetComponent);
    component = fixture.componentInstance;
    component.data = new DataMapperControl([], []);
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
