<?php

namespace App\Filament\Resources\Manufacturers;

use App\Filament\Resources\Manufacturers\Pages\CreateManufacturer;
use App\Filament\Resources\Manufacturers\Pages\EditManufacturer;
use App\Filament\Resources\Manufacturers\Pages\ListManufacturers;
use App\Filament\Resources\Manufacturers\RelationManagers\DocumentsRelationManager;
use App\Filament\Resources\Manufacturers\RelationManagers\ErrorCodesRelationManager;
use App\Filament\Resources\Manufacturers\RelationManagers\ProductSeriesRelationManager;
use App\Filament\Resources\Manufacturers\RelationManagers\ProductsRelationManager;
use App\Filament\Resources\Manufacturers\RelationManagers\VideosRelationManager;
use App\Models\Manufacturer;
use BackedEnum;
use Filament\Actions\BulkActionGroup;
use Filament\Actions\DeleteAction;
use Filament\Actions\DeleteBulkAction;
use Filament\Actions\EditAction;
use Filament\Forms;
use Filament\Resources\Resource;
use Filament\Schemas\Schema;
use Filament\Tables;
use Filament\Tables\Table;
use UnitEnum;

class ManufacturerResource extends Resource
{
    protected static ?string $model = Manufacturer::class;

    protected static string|BackedEnum|null $navigationIcon = 'heroicon-o-building-office';

    protected static UnitEnum|string|null $navigationGroup = 'Data';

    protected static ?string $navigationLabel = 'Hersteller';

    protected static ?int $navigationSort = 2;

    public static function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                Forms\Components\TextInput::make('name')
                    ->required()
                    ->maxLength(255),

                Forms\Components\TextInput::make('short_name')
                    ->maxLength(50),

                Forms\Components\TextInput::make('website')
                    ->url()
                    ->maxLength(500),

                Forms\Components\TextInput::make('logo_url')
                    ->url()
                    ->maxLength(500)
                    ->label('Logo/Favicon URL'),

                Forms\Components\TextInput::make('support_email')
                    ->email()
                    ->maxLength(255),

                Forms\Components\TextInput::make('support_phone')
                    ->tel()
                    ->maxLength(100),

                Forms\Components\TextInput::make('country')
                    ->maxLength(100),

                Forms\Components\TextInput::make('founded_year')
                    ->numeric(),

                Forms\Components\Textarea::make('headquarters_address')
                    ->columnSpanFull(),

                Forms\Components\TextInput::make('stock_symbol')
                    ->maxLength(20),

                Forms\Components\TextInput::make('primary_business_segment')
                    ->maxLength(255),

                Forms\Components\Toggle::make('is_competitor')
                    ->default(false),

                Forms\Components\TextInput::make('market_share_percent')
                    ->numeric()
                    ->minValue(0)
                    ->maxValue(100)
                    ->label('Market Share (%)'),

                Forms\Components\TextInput::make('annual_revenue_usd')
                    ->numeric()
                    ->label('Annual Revenue (USD)'),

                Forms\Components\TextInput::make('employee_count')
                    ->numeric()
                    ->label('Employee Count'),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('name')
                    ->label('Name')
                    ->searchable()
                    ->sortable(),

                Tables\Columns\TextColumn::make('short_name')
                    ->label('Short Name')
                    ->sortable(),

                Tables\Columns\TextColumn::make('country')
                    ->label('Country')
                    ->sortable(),

                Tables\Columns\BooleanColumn::make('is_competitor')
                    ->label('Competitor'),

                Tables\Columns\TextColumn::make('created_at')
                    ->label('Created')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('is_competitor')
                    ->options([
                        true => 'Competitor',
                        false => 'Non-Competitor',
                    ])
                    ->label('Type'),
            ])
            ->actions([
                EditAction::make(),
                DeleteAction::make(),
            ])
            ->bulkActions([
                BulkActionGroup::make([
                    DeleteBulkAction::make(),
                ]),
            ]);
    }

    public static function getRelations(): array
    {
        return [
            ProductsRelationManager::class,
            ProductSeriesRelationManager::class,
            DocumentsRelationManager::class,
            ErrorCodesRelationManager::class,
            VideosRelationManager::class,
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => ListManufacturers::route('/'),
            'create' => CreateManufacturer::route('/create'),
            'edit' => EditManufacturer::route('/{record}/edit'),
        ];
    }
}
