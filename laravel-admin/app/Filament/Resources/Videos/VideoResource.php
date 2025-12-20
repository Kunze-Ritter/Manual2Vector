<?php

namespace App\Filament\Resources\Videos;

use App\Filament\Resources\Videos\Pages\CreateVideo;
use App\Filament\Resources\Videos\Pages\EditVideo;
use App\Filament\Resources\Videos\Pages\ListVideos;
use App\Filament\Resources\Videos\Schemas\VideoForm;
use App\Filament\Resources\Videos\Tables\VideosTable;
use App\Models\Video;
use BackedEnum;
use Filament\Resources\Resource;
use Filament\Schemas\Schema;
use Filament\Support\Icons\Heroicon;
use Filament\Tables\Table;
use UnitEnum;

class VideoResource extends Resource
{
    protected static ?string $model = Video::class;

    protected static UnitEnum|string|null $navigationGroup = 'Content';

    protected static ?string $navigationLabel = 'Videos';

    protected static string|BackedEnum|null $navigationIcon = 'heroicon-o-film';

    protected static ?int $navigationSort = 2;

    protected static bool $shouldRegisterNavigation = true;

    protected static ?string $recordTitleAttribute = 'title';

    public static function form(Schema $schema): Schema
    {
        return VideoForm::configure($schema);
    }

    public static function table(Table $table): Table
    {
        return VideosTable::configure($table);
    }

    public static function getRelations(): array
    {
        return [
            // Relations können später ergänzt werden
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => ListVideos::route('/'),
            'create' => CreateVideo::route('/create'),
            'edit' => EditVideo::route('/{record}/edit'),
        ];
    }
}
