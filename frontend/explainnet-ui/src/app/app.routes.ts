import { Routes } from '@angular/router';

export const routes: Routes = [
  { 
    path: '', 
    loadComponent: () => import('./pages/landing/landing.component').then(m => m.LandingComponent)
  },
  { 
    path: 'locker', 
    loadComponent: () => import('./pages/locker/locker.component').then(m => m.LockerComponent)
  },
  { 
    path: 'create-analysis', 
    loadComponent: () => import('./pages/terminal/terminal.component').then(m => m.TerminalComponent)
  },
  { 
    path: 'analysis/:id', 
    loadComponent: () => import('./pages/analysis/analysis.component').then(m => m.AnalysisComponent)
  }
];
