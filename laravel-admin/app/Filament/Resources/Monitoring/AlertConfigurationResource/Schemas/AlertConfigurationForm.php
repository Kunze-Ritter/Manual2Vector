<?php

namespace App\Filament\Resources\Monitoring\AlertConfigurationResource\Schemas;

use Filament\Forms\Components\Fieldset;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\TagsInput;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\Toggle;
use Filament\Schemas\Schema;

class AlertConfigurationForm
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                TextInput::make('rule_name')
                    ->label('Regelname')
                    ->required()
                    ->maxLength(100)
                    ->unique(ignoreRecord: true),

                Textarea::make('description')
                    ->label('Beschreibung')
                    ->rows(3),

                Toggle::make('is_enabled')
                    ->label('Aktiviert')
                    ->default(true),

                TagsInput::make('error_types')
                    ->label('Fehlertypen')
                    ->placeholder('Fehlertyp hinzufügen')
                    ->suggestions([
                        'TimeoutError',
                        'ConnectionError',
                        'RateLimitError',
                        'ValidationError',
                        'APIError',
                    ]),

                TagsInput::make('stages')
                    ->label('Pipeline-Stages')
                    ->placeholder('Stage hinzufügen')
                    ->suggestions([
                        'classification',
                        'chunking',
                        'embedding',
                        'link_enrichment',
                        'image_extraction',
                        'error_code_extraction',
                    ]),

                Select::make('severity_threshold')
                    ->label('Schwellenwert Schweregrad')
                    ->options([
                        'low' => 'Low',
                        'medium' => 'Medium',
                        'high' => 'High',
                        'critical' => 'Critical',
                    ])
                    ->default('medium')
                    ->required(),

                Fieldset::make('Schwellenwerte')
                    ->schema([
                        TextInput::make('error_count_threshold')
                            ->label('Fehleranzahl')
                            ->numeric()
                            ->default(5)
                            ->required()
                            ->minValue(1),

                        TextInput::make('time_window_minutes')
                            ->label('Zeitfenster (Minuten)')
                            ->numeric()
                            ->default(15)
                            ->required()
                            ->minValue(1),

                        TextInput::make('aggregation_window_minutes')
                            ->label('Aggregationsfenster (Minuten)')
                            ->numeric()
                            ->default(5)
                            ->required()
                            ->minValue(1),
                    ]),

                TagsInput::make('email_recipients')
                    ->label('E-Mail-Empfänger')
                    ->placeholder('E-Mail hinzufügen')
                    ->nestedRecursiveRules([
                        'email',
                    ]),

                TagsInput::make('slack_webhooks')
                    ->label('Slack Webhooks')
                    ->placeholder('Webhook-URL hinzufügen')
                    ->nestedRecursiveRules([
                        'url',
                    ]),
            ]);
    }
}
