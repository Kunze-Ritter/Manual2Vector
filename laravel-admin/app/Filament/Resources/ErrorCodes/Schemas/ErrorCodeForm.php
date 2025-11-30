<?php

namespace App\Filament\Resources\ErrorCodes\Schemas;

use Filament\Forms\Components\Select;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\Toggle;
use Filament\Schemas\Schema;

class ErrorCodeForm
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                TextInput::make('error_code')
                    ->label('Error Code')
                    ->required()
                    ->maxLength(20),

                Textarea::make('error_description')
                    ->label('Beschreibung')
                    ->rows(3),

                Textarea::make('solution_text')
                    ->label('Lösung')
                    ->rows(4),

                Select::make('manufacturer_id')
                    ->label('Hersteller')
                    ->relationship('manufacturer', 'name')
                    ->searchable()
                    ->preload(),

                Select::make('product_id')
                    ->label('Produkt')
                    ->relationship('product', 'model_number')
                    ->searchable()
                    ->preload(),

                Select::make('video_id')
                    ->label('Video')
                    ->relationship('video', 'title')
                    ->searchable()
                    ->preload(),

                TextInput::make('page_number')
                    ->label('Seite')
                    ->numeric(),

                TextInput::make('confidence_score')
                    ->label('Confidence')
                    ->numeric(),

                TextInput::make('estimated_fix_time_minutes')
                    ->label('Geschätzte Fixzeit (Minuten)')
                    ->numeric(),

                TextInput::make('severity_level')
                    ->label('Schweregrad')
                    ->maxLength(20),

                Toggle::make('requires_technician')
                    ->label('Techniker erforderlich'),

                Toggle::make('requires_parts')
                    ->label('Ersatzteile erforderlich'),

                Textarea::make('context_text')
                    ->label('Kontext')
                    ->rows(3),

                Textarea::make('metadata')
                    ->label('Metadata (JSON)')
                    ->rows(3),
            ]);
    }
}
