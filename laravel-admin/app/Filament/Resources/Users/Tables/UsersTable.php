<?php

namespace App\Filament\Resources\Users\Tables;

use App\Enums\UserRole;
use Filament\Actions\BulkActionGroup;
use Filament\Actions\DeleteBulkAction;
use Filament\Actions\EditAction;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Table;

class UsersTable
{
    public static function configure(Table $table): Table
    {
        return $table

            ->columns([
                TextColumn::make('name')
                    ->label('Name')
                    ->searchable()
                    ->sortable(),

                TextColumn::make('email')
                    ->label('E-Mail')
                    ->searchable()
                    ->sortable(),

                TextColumn::make('role')
                    ->label('Rolle')
                    ->formatStateUsing(fn ($state) => UserRole::labelFor($state))
                    ->sortable(),

                TextColumn::make('created_at')
                    ->label('Erstellt am')
                    ->dateTime()
                    ->sortable(),
            ])
            ->filters([
                SelectFilter::make('role')
                    ->label('Rolle')
                    ->options(UserRole::options()),
            ])
            ->recordActions([
                EditAction::make(),
            ])
            ->toolbarActions([
                BulkActionGroup::make([
                    DeleteBulkAction::make(),
                ]),
            ]);
    }
}
