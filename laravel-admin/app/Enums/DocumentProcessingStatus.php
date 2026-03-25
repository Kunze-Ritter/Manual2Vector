<?php

namespace App\Enums;

enum DocumentProcessingStatus: string
{
    case Pending = 'pending';
    case Uploaded = 'uploaded';
    case Processing = 'processing';
    case Completed = 'completed';
    case Failed = 'failed';

    public function label(): string
    {
        return match ($this) {
            self::Pending => 'Pending',
            self::Uploaded => 'Uploaded',
            self::Processing => 'Processing',
            self::Completed => 'Completed',
            self::Failed => 'Failed',
        };
    }

    public static function labelFor(self|string|null $status): string
    {
        if ($status instanceof self) {
            return $status->label();
        }

        if (is_string($status)) {
            return self::tryFrom($status)?->label() ?? $status;
        }

        return '';
    }

    public static function options(): array
    {
        return array_column(
            array_map(
                fn (self $status) => ['value' => $status->value, 'label' => $status->label()],
                self::cases()
            ),
            'label',
            'value'
        );
    }
}
