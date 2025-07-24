import { WorkflowPageModule } from './pages/worflow/workflow.module';
import { NgModule } from '@angular/core';
import { PreloadAllModules, RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  {
    path: '',
    loadChildren: () => import('./tabs/tabs.module').then(m => m.TabsPageModule)
  },
  {
    path: 'workflow',
    loadChildren: () => import('./pages/worflow/workflow.module').then( m => m.WorkflowPageModule)
  },
  {
    path: 'test-composant',
    loadChildren: () => import('./pages/test-composant/test-composant.module').then( m => m.TestComposantPageModule)
  }

];
@NgModule({
  imports: [
    RouterModule.forRoot(routes, { preloadingStrategy: PreloadAllModules })
  ],
  exports: [RouterModule]
})
export class AppRoutingModule {}
