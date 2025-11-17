import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: '/locker', pathMatch: 'full' },
  { 
    path: 'locker', 
    loadComponent: () => import('./pages/locker/locker.component').then(m => m.LockerComponent)
  },
  { 
    path: 'analysis/:id', 
    loadComponent: () => import('./pages/analysis/analysis.component').then(m => m.AnalysisComponent)
  }
];
