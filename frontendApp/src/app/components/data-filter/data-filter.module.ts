// src/app/data-mapper/data-mapper.module.ts

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DataFilterComponent } from './data-filter.component';
import { NgxAngularQueryBuilderModule } from 'ngx-angular-query-builder';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';

@NgModule({
  declarations: [
    DataFilterComponent
  ],
  imports: [
    CommonModule, NgxAngularQueryBuilderModule, FormsModule, IonicModule
  ],
  exports: [
    DataFilterComponent
  ]
})
export class DataFilterModule { }
