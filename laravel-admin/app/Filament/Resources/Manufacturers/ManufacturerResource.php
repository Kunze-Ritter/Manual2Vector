<?php

namespace App\Filament\Resources\Manufacturers;

use App\Filament\Resources\Manufacturers\Pages\CreateManufacturer;
use App\Filament\Resources\Manufacturers\Pages\EditManufacturer;
use App\Filament\Resources\Manufacturers\Pages\ListManufacturers;
use App\Models\Manufacturer;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class ManufacturerResource extends Resource
{
    protected static ?string $model = Manufacturer::class;

    protected static ?string $navigationIcon = 'heroicon-o-building-office';

    protected static ?string $navigationGroup = 'Product Management';

    protected static ?int $navigationSort = 1;

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
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
                    ->step(0.01),
                
                Forms\Components\TextInput::make('annual_revenue_usd')
                    ->numeric(),
                
                Forms\Components\TextInput::make('employee_count')
                    ->numeric(),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('name')
                    ->searchable()
                    ->sortable(),
                
                Tables\Columns\TextColumn::make('short_name')
                    ->searchable()
                    ->sortable(),
                
                Tables\Columns\TextColumn::make('country')
                    ->sortable()
                    ->searchable(),
                
                Tables\Columns\TextColumn::make('website')
                    ->url()
                    ->limit(30),
                
                Tables\Columns\ImageColumn::make('logo_url')
                    ->label('Logo')
                    ->defaultImageUrl(url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjMyIiBoZWlnaHQ9IjMyIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0xNiA4QzEyLjY4NjMgOCAxMCAxMC42ODYzIDEwIDE0QzEwIDE3LjMxMzcgMTIuNjg2MyAyMCAxNiAyMEMxOS4zMTM3IDIwIDIyIDE3LjMxMzcgMjIgMTRDMjIgMTAuNjg2MyAxOS4zMTM3IDggMTYgOFoiIGZpbGw9IiM5Q0EzQUYiLz4KPC9zdmc+'))
                    ->circular()
                    ->size(40),
                
                Tables\Columns\TextColumn::make('founded_year')
                    ->numeric()
                    ->sortable(),
                
                Tables\Columns\IconColumn::make('is_competitor')
                    ->boolean()
                    ->sortable(),
                
                Tables\Columns\TextColumn::make('stock_symbol')
                    ->badge()
                    ->color('success'),
                
                Tables\Columns\TextColumn::make('created_at')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
                
                Tables\Columns\TextColumn::make('updated_at')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('country')
                    ->options([
                        'Japan' => 'Japan',
                        'USA' => 'United States',
                        'Germany' => 'Germany',
                        'Netherlands' => 'Netherlands',
                    ]),
                
                Tables\Filters\TernaryFilter::make('is_competitor')
                    ->label('Competitor')
                    ->placeholder('All')
                    ->trueLabel('Competitor')
                    ->falseLabel('Not Competitor'),
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
                Tables\Actions\DeleteAction::make(),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
            ]);
    }

    public static function getRelations(): array
    {
        return [
            //
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
