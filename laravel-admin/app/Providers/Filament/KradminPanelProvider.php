<?php

namespace App\Providers\Filament;

use Filament\Http\Middleware\Authenticate;
use Filament\Http\Middleware\AuthenticateSession;
use Filament\Http\Middleware\DisableBladeIconComponents;
use Filament\Http\Middleware\DispatchServingFilamentEvent;
use Filament\Pages\Dashboard;
use Filament\Panel;
use Filament\PanelProvider;
use Filament\Navigation\NavigationGroup;
use Filament\Support\Colors\Color;
use Filament\Widgets\AccountWidget;
use Filament\Widgets\FilamentInfoWidget;
use App\Filament\Widgets\DashboardStatsWidget;
use App\Filament\Widgets\APIStatusWidget;
use App\Filament\Widgets\DashboardOverviewWidget;
use App\Filament\Widgets\PipelineStatusWidget;
use App\Filament\Widgets\QueueStatusWidget;
use App\Filament\Widgets\DataQualityWidget;
use App\Filament\Widgets\SystemMetricsWidget;
use Illuminate\Cookie\Middleware\AddQueuedCookiesToResponse;
use Illuminate\Cookie\Middleware\EncryptCookies;
use Illuminate\Foundation\Http\Middleware\VerifyCsrfToken;
use Illuminate\Routing\Middleware\SubstituteBindings;
use Illuminate\Session\Middleware\StartSession;
use Illuminate\View\Middleware\ShareErrorsFromSession;

class KradminPanelProvider extends PanelProvider
{
    public function panel(Panel $panel): Panel
    {
        return $panel
            ->default()
            ->id('kradmin')
            ->path('kradmin')
            ->login()
            ->homeUrl(fn () => route('filament.kradmin.resources.manufacturers.index'))
            ->colors([
                'primary' => Color::Amber,
            ])
            ->discoverResources(in: app_path('Filament/Resources'), for: 'App\Filament\Resources')
            ->discoverPages(in: app_path('Filament/Pages'), for: 'App\Filament\Pages')
            ->pages([
                Dashboard::class,
            ])
            ->discoverWidgets(in: app_path('Filament/Widgets'), for: 'App\Filament\Widgets')
            ->widgets([
                AccountWidget::class,
                DashboardOverviewWidget::class,
                APIStatusWidget::class,
                SystemMetricsWidget::class,
                PipelineStatusWidget::class,
                QueueStatusWidget::class,
                DataQualityWidget::class,
                FilamentInfoWidget::class,
            ])
            ->navigationGroups([
                NavigationGroup::make('Content')
                    ->label('Inhalte')
                    ->icon('heroicon-o-folder')
                    ->collapsible(),
                NavigationGroup::make('Data')
                    ->label('Daten')
                    ->icon('heroicon-o-table-cells')
                    ->collapsible(),
                NavigationGroup::make('Monitoring')
                    ->label('Überwachung')
                    ->icon('heroicon-o-chart-bar')
                    ->collapsible(),
                NavigationGroup::make('Services')
                    ->label('Dienste')
                    ->icon('heroicon-o-server')
                    ->collapsible(),
                NavigationGroup::make('System')
                    ->label('System')
                    ->collapsible(),
            ])
            ->middleware([
                EncryptCookies::class,
                AddQueuedCookiesToResponse::class,
                StartSession::class,
                AuthenticateSession::class,
                ShareErrorsFromSession::class,
                VerifyCsrfToken::class,
                SubstituteBindings::class,
                DisableBladeIconComponents::class,
                DispatchServingFilamentEvent::class,
            ])
            ->authMiddleware([
                Authenticate::class,
            ]);
    }
}
