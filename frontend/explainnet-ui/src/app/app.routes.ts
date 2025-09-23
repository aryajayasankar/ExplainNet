import { Routes } from '@angular/router';
import { Locker } from './pages/locker/locker';
import { Analysis } from './pages/analysis/analysis.component';

export const routes: Routes = [
    { path: 'locker', component: Locker },
    { path: 'analysis', component: Analysis },
    // Redirect any empty path to the analysis page by default
    { path: '', redirectTo: '/analysis', pathMatch: 'full' },
];