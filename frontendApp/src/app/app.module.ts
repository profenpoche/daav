import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { IonicStorageModule } from '@ionic/storage-angular';
import { RouteReuseStrategy } from '@angular/router';

import { IonicModule, IonicRouteStrategy } from '@ionic/angular';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { HttpClientJsonpModule, HttpClientModule } from '@angular/common/http';
import { ComponentsModule } from './components-module';
import { ReteModule } from 'rete-angular-plugin/16';
import { TransformNodeComponent } from './components/nodes/transform/nodes.component';
import { InputNodeComponent } from './components/nodes/input/nodes.component';
import { OutputNodeComponent } from './components/nodes/output/nodes.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { StatusComponentComponent } from './components/widgets/status-component/status-component.component';
import { MatTooltipModule } from '@angular/material/tooltip';
import { NgxAngularQueryBuilderModule } from "ngx-angular-query-builder";
import { CdkAccordionModule } from '@angular/cdk/accordion';


@NgModule({
  declarations: [AppComponent, TransformNodeComponent, OutputNodeComponent, InputNodeComponent,StatusComponentComponent],
  imports: [BrowserModule, IonicModule.forRoot(),ReteModule, BrowserAnimationsModule,AppRoutingModule, HttpClientModule, HttpClientJsonpModule, ComponentsModule, IonicStorageModule.forRoot(), MatTooltipModule, NgxAngularQueryBuilderModule],
  providers: [{ provide: RouteReuseStrategy, useClass: IonicRouteStrategy }],
  bootstrap: [AppComponent],
})
export class AppModule {}
