<?php

namespace App\Filament\Resources\Videos\Schemas;

use Filament\Forms\Components\DateTimePicker;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Schemas\Schema;

class VideoForm
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                TextInput::make('title')
                    ->label('Titel')
                    ->required()
                    ->maxLength(500),

                TextInput::make('video_url')
                    ->label('Video URL')
                    ->url(),

                TextInput::make('youtube_id')
                    ->label('YouTube ID')
                    ->maxLength(20),

                TextInput::make('platform')
                    ->label('Plattform')
                    ->maxLength(20),

                Textarea::make('description')
                    ->label('Beschreibung')
                    ->rows(3),

                TextInput::make('thumbnail_url')
                    ->label('Thumbnail URL')
                    ->url(),

                TextInput::make('duration')
                    ->label('Dauer (Sekunden)')
                    ->numeric(),

                TextInput::make('channel_title')
                    ->label('Kanal')
                    ->maxLength(200),

                DateTimePicker::make('published_at')
                    ->label('Veröffentlicht am'),

                Select::make('manufacturer_id')
                    ->label('Hersteller')
                    ->relationship('manufacturer', 'name')
                    ->searchable()
                    ->preload(),

                Select::make('series_id')
                    ->label('Serie')
                    ->relationship('series', 'series_name')
                    ->searchable()
                    ->preload(),

                Textarea::make('context_description')
                    ->label('Kontext')
                    ->rows(3),

                Textarea::make('metadata')
                    ->label('Metadata (JSON)')
                    ->rows(3),
            ]);
    }
}
