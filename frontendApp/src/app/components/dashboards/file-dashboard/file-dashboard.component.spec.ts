import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { CommonModule } from '@angular/common';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { FileDashboardComponent } from './file-dashboard.component';

describe('FileDashboardComponent', () => {
  let component: FileDashboardComponent;
  let fixture: ComponentFixture<FileDashboardComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ FileDashboardComponent ],
      imports: [IonicModule.forRoot(), HttpClientTestingModule, CommonModule, MatFormFieldModule, MatSelectModule, BrowserAnimationsModule]
    }).compileComponents();

    fixture = TestBed.createComponent(FileDashboardComponent);
    component = fixture.componentInstance;
    component.dataset = { id: 'test', name: 'test', files: [] } as any; // Mock input data
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
