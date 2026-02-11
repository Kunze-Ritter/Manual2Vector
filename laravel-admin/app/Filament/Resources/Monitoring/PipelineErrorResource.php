<?php

namespace App\Filament\Resources\Monitoring;

use App\Filament\Resources\Monitoring\PipelineErrorResource\Pages;
use App\Filament\Resources\Monitoring\PipelineErrorResource\Tables\PipelineErrorsTable;
use App\Models\PipelineError;
use App\Services\BackendApiService;
use BackedEnum;
use Filament\Resources\Resource;
use Illuminate\Database\Eloquent\Builder;
use UnitEnum;

class PipelineErrorResource extends Resource
{
    protected static ?string $model = PipelineError::class;

    protected static BackendApiService $backendApiService;

    public function __construct()
    {
        static::$backendApiService = app(BackendApiService::class);
    }

    public static function getBackendApiService(): BackendApiService
    {
        if (!isset(static::$backendApiService)) {
            static::$backendApiService = app(BackendApiService::class);
        }
        return static::$backendApiService;
    }

    protected static UnitEnum|string|null $navigationGroup = 'Monitoring';

    protected static ?string $navigationLabel = 'Pipeline-Fehler';

    protected static string|BackedEnum|null $navigationIcon = 'heroicon-o-exclamation-triangle';

    protected static ?int $navigationSort = 3;

    protected static ?string $recordTitleAttribute = 'error_id';

    public static function getEloquentQuery(): Builder
    {
        return parent::getEloquentQuery()
            ->with(['document:id,filename', 'resolvedBy:id,name'])
            ->latest('created_at');
    }

    public static function table(\Filament\Tables\Table $table): \Filament\Tables\Table
    {
        return PipelineErrorsTable::make($table);
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListPipelineErrors::route('/'),
            'view' => Pages\ViewPipelineError::route('/{record}'),
        ];
    }

    public static function getNavigationBadge(): ?string
    {
        return static::getModel()::active()->count();
    }

    public static function getNavigationBadgeColor(): ?string
    {
        $count = static::getModel()::active()->count();
        return $count > 0 ? 'danger' : 'success';
    }

    public static function getStatusBadgeColor(string $status): string
    {
        return match($status) {
            'pending' => 'danger',
            'retrying' => 'warning',
            'resolved' => 'success',
            default => 'gray',
        };
    }

    public static function getStatusIcon(string $status): string
    {
        return match($status) {
            'pending' => '❌',
            'retrying' => '🔄',
            'resolved' => '✅',
            default => '⚠️',
        };
    }
}
