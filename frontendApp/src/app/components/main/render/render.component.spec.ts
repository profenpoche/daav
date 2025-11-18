import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { MatTabsModule } from '@angular/material/tabs';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { RenderComponent } from './render.component';
import { LoadingService } from 'src/app/services/loading.service';

describe('RenderComponent', () => {
  let component: RenderComponent;
  let fixture: ComponentFixture<RenderComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ RenderComponent ],
      imports: [IonicModule.forRoot(), HttpClientTestingModule, MatTabsModule, BrowserAnimationsModule],
      providers: [
        { provide: LoadingService, useValue: jasmine.createSpyObj('LoadingService', ['show', 'hide']) }
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(RenderComponent);
    component = fixture.componentInstance;
    component.dataset = { 
      name: 'Test Dataset',
      id: 'test-id',
      type: 'test-type',
      data: [],
      schema: { fields: [] },
      columns: []
    } as any;
    component.data = {
      dbNames: [],
      tableNames: [],
      displayedColumns: [],
      fiche: { items: [], limit: 10, total: 0, current_page: 1 },
      selectedDataset: { name: 'Test Dataset', id: 'test-id' },
      renderTabIndex: 0,
      pagination: { perPage: 100, page: 1 },
      datasetParams: { database: '', table: '' }
    } as any;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
