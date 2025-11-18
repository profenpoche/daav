import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { DragDropModule } from '@angular/cdk/drag-drop';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

import { DataMapperComponent } from './data-mapper.component';

describe('DataMapperComponent', () => {
  let component: DataMapperComponent;
  let fixture: ComponentFixture<DataMapperComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ DataMapperComponent ],
      imports: [IonicModule.forRoot(), DragDropModule, MatCardModule, MatIconModule, MatTooltipModule]
    }).compileComponents();

    fixture = TestBed.createComponent(DataMapperComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
