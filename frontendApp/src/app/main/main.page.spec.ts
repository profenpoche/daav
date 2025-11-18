import { ComponentFixture, TestBed } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { MainPage } from './main.page';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { LoadingService } from '../services/loading.service';

describe('MainPage', () => {
  let component: MainPage;
  let fixture: ComponentFixture<MainPage>;

  beforeEach(async () => {
    const loadingServiceSpy = jasmine.createSpyObj('LoadingService', ['show', 'hide']);

    await TestBed.configureTestingModule({
      declarations: [MainPage],
      imports: [IonicModule.forRoot(),HttpClientTestingModule],
      providers: [
        { provide: LoadingService, useValue: loadingServiceSpy }
      ],
      schemas: [CUSTOM_ELEMENTS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(MainPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
