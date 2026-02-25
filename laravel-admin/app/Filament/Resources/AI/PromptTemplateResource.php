<?php

namespace App\Filament\Resources\AI;

use App\Filament\Resources\AI\PromptTemplateResource\Pages;
use App\Models\PromptTemplate;
use BackedEnum;
use Filament\Resources\Resource;
use Filament\Schemas\Schema;
use Filament\Tables\Actions\DeleteAction;
use Filament\Tables\Actions\EditAction;
use Filament\Tables\Columns\IconColumn;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Filters\TernaryFilter;
use Filament\Tables\Table;
use UnitEnum;

class PromptTemplateResource extends Resource
{
    protected static ?string $model = PromptTemplate::class;

    protected static string|BackedEnum|null $navigationIcon = 'heroicon-o-chat-bubble-left-ellipsis';

    protected static ?string $navigationLabel = 'Prompt Templates';

    protected static UnitEnum|string|null $navigationGroup = 'AI';

    protected static ?int $navigationSort = 2;

    protected static ?string $modelLabel = 'Prompt Template';

    protected static ?string $pluralModelLabel = 'Prompt Templates';

    public static function form(Schema $schema): Schema
    {
        return $schema->components([
            \Filament\Forms\Components\TextInput::make('title')
                ->label('Titel')
                ->required()
                ->maxLength(100),

            \Filament\Forms\Components\TextInput::make('description')
                ->label('Beschreibung')
                ->maxLength(255),

            \Filament\Forms\Components\Textarea::make('prompt_text')
                ->label('Prompt Text')
                ->required()
                ->rows(3)
                ->helperText('Der Text wird als Eingabe in den Chat eingefügt. Kann mit ":" enden für Benutzereingabe.'),

            \Filament\Forms\Components\Select::make('category')
                ->label('Kategorie')
                ->options([
                    'general'     => 'Allgemein',
                    'error_codes' => 'Fehlercodes',
                    'parts'       => 'Ersatzteile',
                    'videos'      => 'Videos',
                    'diagnosis'   => 'Diagnose',
                ])
                ->required()
                ->default('general'),

            \Filament\Forms\Components\TextInput::make('icon')
                ->label('Icon (Heroicon)')
                ->default('heroicon-o-chat-bubble-left')
                ->helperText('z.B. heroicon-o-magnifying-glass'),

            \Filament\Forms\Components\TextInput::make('sort_order')
                ->label('Reihenfolge')
                ->numeric()
                ->default(0),

            \Filament\Forms\Components\Toggle::make('is_active')
                ->label('Aktiv')
                ->default(true),
        ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                TextColumn::make('sort_order')->label('#')->sortable(),
                TextColumn::make('title')->label('Titel')->searchable(),
                TextColumn::make('category')->label('Kategorie')->badge()
                    ->color(fn ($state) => match($state) {
                        'error_codes' => 'danger',
                        'parts'       => 'warning',
                        'videos'      => 'info',
                        'diagnosis'   => 'success',
                        default       => 'gray',
                    }),
                TextColumn::make('prompt_text')->label('Prompt')->limit(60)->wrap(),
                IconColumn::make('is_active')->label('Aktiv')->boolean(),
                TextColumn::make('updated_at')->label('Geändert')->dateTime('d.m.Y H:i')->sortable(),
            ])
            ->defaultSort('sort_order')
            ->filters([
                TernaryFilter::make('is_active')->label('Aktiv'),
            ])
            ->actions([
                EditAction::make(),
                DeleteAction::make(),
            ])
            ->reorderable('sort_order');
    }

    public static function getPages(): array
    {
        return [
            'index'  => Pages\ListPromptTemplates::route('/'),
            'create' => Pages\CreatePromptTemplate::route('/create'),
            'edit'   => Pages\EditPromptTemplate::route('/{record}/edit'),
        ];
    }
}
