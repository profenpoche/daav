import { Component, inject, OnInit } from '@angular/core';
import { DashboardComponent } from '../dashboard/dashboard.component';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { HttpHeaders } from '@angular/common/http';
import {
  MatSnackBar,
  MatSnackBarHorizontalPosition,
  MatSnackBarVerticalPosition,
} from '@angular/material/snack-bar';

interface CatalogItem {
  type: string;
  name: string;
  owner: {
    "name": string,
    "logo": string,
  };
}

interface BilateralContractsResponse {
  contracts: any[];
  endpoint: string;
  contractUri: string;
}

@Component({
  selector: 'app-ptxdashboard',
  templateUrl: './ptxdashboard.component.html',
  styleUrls: ['./ptxdashboard.component.scss'],
  imports: [CommonModule, IonicModule],
  standalone: true

})
export class PTXDashboardComponent  extends DashboardComponent implements OnInit{

  serviceOfferings: CatalogItem[] = [];
  softwareResources: CatalogItem[] = [];
  dataResources: CatalogItem[] = [];
  contractsBilaterals: any[] = [];
  contractsUseCase: any[] = [];
  pdcEndpoint: string = ''; 
  contractUri: string = '';
  private _snackBar = inject(MatSnackBar);
  isLoadingCatalog: boolean = true;

  constructor() {
    super();
  }

  ngOnInit(): void {
    this.loadCatalog();
    //this.loadContractsBilaterals();
    this.loadContractsUseCase()
  }

  triggerDataExchange(contract: any, provider, purpose) {
    const exchangeUrl = `${this.datasetService.urlBack}/ptx/trigger-data-exchange/${this.dataset.id}`;
    const purpose_url = "https://api.visionstrust.com/v1/catalog/serviceofferings/" + purpose._id;
    const resource_url = "https://api.visionstrust.com/v1/catalog/serviceofferings/" + provider._id;

    const payload = {
      "contract": contract._id,
      "purposeId": purpose_url,
      "resourceId": resource_url,
    }

    this.http.post(exchangeUrl, payload)
      .subscribe({
        next: (res: any) => {
          console.log('Exchange successful:', res);
          if (res.success) {
            this._snackBar.open('Data exchange triggered', 'x', {
              duration: 3000,
              horizontalPosition: 'start',
              verticalPosition: 'bottom',
              panelClass: ['success-snackbar']
            });
            this.datasetService.get();
          }
        },
        error: (err) => {
          this._snackBar.open('Data exchange trigger failed', 'x', {
            duration: 5000,
            horizontalPosition: 'start',
            verticalPosition: 'bottom',
            panelClass: ['error-snackbar']
          });
        }
      });
  }


  loadContractsUseCase(){
    this.http.get(this.datasetService.urlBack + '/ptx/contracts/use-case/' + this.dataset.id).subscribe((res) => {
      this.contractsUseCase = res as any[];
    })
  }

  loadContractsBilaterals() {
    this.http.get<BilateralContractsResponse>(`${this.datasetService.urlBack}/ptx/contracts/bilaterals/${this.dataset.id}`)
      .subscribe({
        next: (res) => {
          this.contractsBilaterals = res.contracts;
          //console.log('Bilateral contracts loaded:', this.contractsBilaterals);
          this.pdcEndpoint = res.endpoint;
          this.contractUri = res.contractUri;
        },
        error: (err) => {
          console.error('Failed to load bilateral contracts', err);
        }
      });
  }

  loadCatalog() {
    this.isLoadingCatalog = true;
    this.http.get<{ catalog: CatalogItem[] }>(this.datasetService.urlBack + '/ptx/' + this.dataset.id).subscribe((res) => {
      this.serviceOfferings = res.catalog.filter(item => item.type === 'ptx:serviceofferings');
      this.softwareResources = res.catalog.filter(item => item.type === 'ptx:softwareresources');
      this.dataResources = res.catalog.filter(item => item.type === 'ptx:dataresources');
      this.isLoadingCatalog = false;
    })
  }

  getCardClass(type: string): string {
    if (type === 'ptx:serviceofferings') {
      return 'card-service';
    } else if (type === 'ptx:softwaresources') {
      return 'card-software';
    } else if (type === 'ptx:dataresources') {
      return 'card-data';
    }
    return 'card-default';
  }

  getSkeletonArray(count: number = 1): number[] {
    return Array(count).fill(0).map((x, i) => i);
  }
}
