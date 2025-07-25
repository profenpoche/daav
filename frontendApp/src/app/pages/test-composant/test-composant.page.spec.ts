import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TestComposantPage } from './test-composant.page';

describe('TestComposantPage', () => {
  let component: TestComposantPage;
  let fixture: ComponentFixture<TestComposantPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(TestComposantPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
