import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { DataFilterComponent } from './data-filter.component';

describe('DataFilterComponent', () => {
  let component: DataFilterComponent;
  let fixture: ComponentFixture<DataFilterComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ DataFilterComponent ],
      imports: [IonicModule.forRoot()],
      schemas: [CUSTOM_ELEMENTS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(DataFilterComponent);
    component = fixture.componentInstance;
    component.filterControl = { query: {}, config: {} } as any; // Mock input data
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
