import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { DataFilterWidgetComponent, DataFilterControl } from './data-filter-widget.component';
import { HasDatasetsPipe } from 'src/app/models/data-mapper-types';

describe('DataFilterWidgetComponent', () => {
  let component: DataFilterWidgetComponent;
  let fixture: ComponentFixture<DataFilterWidgetComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ DataFilterWidgetComponent, HasDatasetsPipe ],
      imports: [IonicModule.forRoot()]
    }).compileComponents();

    fixture = TestBed.createComponent(DataFilterWidgetComponent);
    component = fixture.componentInstance;
    component.data = new DataFilterControl([]);
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
