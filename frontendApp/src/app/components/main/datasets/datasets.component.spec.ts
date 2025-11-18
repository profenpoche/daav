import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NO_ERRORS_SCHEMA, Component, Input } from '@angular/core';
import { DatasetsComponent } from './datasets.component';
import { LoadingService } from 'src/app/services/loading.service';
import { Dataset } from 'src/app/models/dataset';

// Stub du composant datasets-modal pour éviter le problème de propriété read-only
@Component({
  selector: 'app-datasets-modal',
  template: ''
})
class DatasetsModalStubComponent {
  @Input() dataset: Dataset | null = null;
  modal = { isOpen: false };
}

describe('DatasetsComponent', () => {
  let component: DatasetsComponent;
  let fixture: ComponentFixture<DatasetsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ DatasetsComponent, DatasetsModalStubComponent ],
      imports: [IonicModule.forRoot(), HttpClientTestingModule],
      providers: [
        { provide: LoadingService, useValue: jasmine.createSpyObj('LoadingService', ['show', 'hide']) }
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(DatasetsComponent);
    component = fixture.componentInstance;
  }));

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });
});
