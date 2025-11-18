import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TransformationComponent } from './transformation.component';
import { LoadingService } from 'src/app/services/loading.service';

describe('TransformationComponent', () => {
  let component: TransformationComponent;
  let fixture: ComponentFixture<TransformationComponent>;

  beforeEach(waitForAsync(() => {
    const loadingSpy = jasmine.createSpyObj('LoadingService', ['present', 'dismiss']);

    TestBed.configureTestingModule({
      declarations: [ TransformationComponent ],
      imports: [IonicModule.forRoot(), HttpClientTestingModule],
      providers: [
        { provide: LoadingService, useValue: loadingSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(TransformationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
