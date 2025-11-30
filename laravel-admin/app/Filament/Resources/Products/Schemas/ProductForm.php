<?php

namespace App\Filament\Resources\Products\Schemas;

use Filament\Forms\Components\Select;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Schemas\Schema;

class ProductForm
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                Select::make('manufacturer_id')
                    ->label('Hersteller')
                    ->relationship('manufacturer', 'name')
                    ->searchable()
                    ->preload()
                    ->required(),

                Select::make('series_id')
                    ->label('Serie')
                    ->relationship('series', 'series_name')
                    ->searchable()
                    ->preload(),

                TextInput::make('model_number')
                    ->label('Modellnummer')
                    ->required()
                    ->maxLength(100),

                Select::make('product_type')
                    ->label('Produkttyp')
                    ->options([
                        'Printers' => [
                            'laser_printer' => 'Laser Printer',
                            'inkjet_printer' => 'Inkjet Printer',
                            'laser_production_printer' => 'Laser Production Printer',
                            'inkjet_production_printer' => 'Inkjet Production Printer',
                            'solid_ink_printer' => 'Solid Ink Printer',
                            'dot_matrix_printer' => 'Dot Matrix Printer',
                            'thermal_printer' => 'Thermal Printer',
                            'dye_sublimation_printer' => 'Dye Sublimation Printer',
                        ],
                        'Multifunction (MFP)' => [
                            'laser_multifunction' => 'Laser MFP',
                            'inkjet_multifunction' => 'Inkjet MFP',
                            'laser_production_multifunction' => 'Laser Production MFP',
                            'inkjet_production_multifunction' => 'Inkjet Production MFP',
                            'solid_ink_multifunction' => 'Solid Ink MFP',
                        ],
                        'Plotters' => [
                            'inkjet_plotter' => 'Inkjet Plotter',
                            'latex_plotter' => 'Latex Plotter',
                            'pen_plotter' => 'Pen Plotter',
                        ],
                        'Scanners' => [
                            'scanner' => 'Scanner',
                            'document_scanner' => 'Document Scanner',
                            'photo_scanner' => 'Photo Scanner',
                            'large_format_scanner' => 'Large Format Scanner',
                        ],
                        'Copiers' => [
                            'copier' => 'Copier',
                        ],
                        'Finishers' => [
                            'finisher' => 'Finisher',
                            'stapler_finisher' => 'Stapler Finisher',
                            'booklet_finisher' => 'Booklet Finisher',
                            'punch_finisher' => 'Punch Finisher',
                            'folder' => 'Folder',
                            'trimmer' => 'Trimmer',
                            'stacker' => 'Stacker',
                        ],
                        'Feeders' => [
                            'feeder' => 'Feeder',
                            'paper_feeder' => 'Paper Feeder',
                            'envelope_feeder' => 'Envelope Feeder',
                            'large_capacity_feeder' => 'Large Capacity Feeder',
                            'document_feeder' => 'Document Feeder',
                        ],
                        'Accessories' => [
                            'accessory' => 'Accessory',
                            'cabinet' => 'Cabinet',
                            'work_table' => 'Work Table',
                            'caster_base' => 'Caster Base',
                            'bridge_unit' => 'Bridge Unit',
                            'interface_kit' => 'Interface Kit',
                            'media_sensor' => 'Media Sensor',
                            'memory_upgrade' => 'Memory Upgrade',
                            'hard_drive' => 'Hard Drive',
                            'controller' => 'Controller',
                            'fax_kit' => 'Fax Kit',
                            'wireless_kit' => 'Wireless Kit',
                            'keyboard' => 'Keyboard',
                            'card_reader' => 'Card Reader',
                            'coin_kit' => 'Coin Kit',
                        ],
                        'Options' => [
                            'option' => 'Option',
                            'duplex_unit' => 'Duplex Unit',
                            'output_tray' => 'Output Tray',
                            'mailbox' => 'Mailbox',
                            'mount_kit' => 'Mount Kit',
                            'job_separator' => 'Job Separator',
                        ],
                        'Consumables' => [
                            'consumable' => 'Consumable',
                            'toner_cartridge' => 'Toner Cartridge',
                            'ink_cartridge' => 'Ink Cartridge',
                            'drum_unit' => 'Drum Unit',
                            'developer_unit' => 'Developer Unit',
                            'fuser_unit' => 'Fuser Unit',
                            'transfer_belt' => 'Transfer Belt',
                            'waste_toner_box' => 'Waste Toner Box',
                            'maintenance_kit' => 'Maintenance Kit',
                            'staple_cartridge' => 'Staple Cartridge',
                            'punch_kit' => 'Punch Kit',
                            'print_head' => 'Print Head',
                            'ink_tank' => 'Ink Tank',
                            'paper' => 'Paper',
                        ],
                        'Software & Licenses' => [
                            'software' => 'Software',
                            'license' => 'License',
                            'firmware' => 'Firmware',
                        ],
                    ])
                    ->searchable()
                    ->preload(),

                TextInput::make('oem_manufacturer')
                    ->label('OEM Hersteller')
                    ->maxLength(100),

                TextInput::make('oem_relationship_type')
                    ->label('OEM Beziehungstyp')
                    ->maxLength(50),

                TextInput::make('product_code')
                    ->label('Produkt-Code')
                    ->maxLength(10),

                TextInput::make('article_code')
                    ->label('Artikel-Code')
                    ->maxLength(50),

                Textarea::make('specifications')
                    ->label('Spezifikationen (JSON)')
                    ->rows(3),

                Textarea::make('pricing')
                    ->label('Preise (JSON)')
                    ->rows(2),

                Textarea::make('lifecycle')
                    ->label('Lifecycle (JSON)')
                    ->rows(2),

                Textarea::make('urls')
                    ->label('URLs (JSON)')
                    ->rows(2),

                Textarea::make('metadata')
                    ->label('Metadata (JSON)')
                    ->rows(2),
            ]);
    }
}
