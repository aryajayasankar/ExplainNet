import { Routes } from '@angular/router';
import { LockerComponent } from './pages/locker/locker.component';
import { Analysis } from './pages/analysis/analysis.component';
import { TopicDetail } from './pages/topic-detail/topic-detail';

export const routes: Routes = [
    { path: 'locker', component: LockerComponent },
    { path: 'locker/:id', component: TopicDetail }, // Changed to TopicDetail
    { path: 'analysis', component: Analysis },
    { path: '', redirectTo: '/analysis', pathMatch: 'full' },
];