import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { PTXDashboardComponent } from './ptxdashboard.component';

describe('PTXDashboardComponent', () => {
  let component: PTXDashboardComponent;
  let fixture: ComponentFixture<PTXDashboardComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [IonicModule.forRoot(), HttpClientTestingModule, PTXDashboardComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(PTXDashboardComponent);
    component = fixture.componentInstance;
    component.dataset = { id: 'test', name: 'test' } as any; // Mock input data
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
