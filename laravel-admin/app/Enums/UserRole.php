<?php

namespace App\Enums;

enum UserRole: string
{
    case Admin = 'admin';
    case Editor = 'editor';
    case Viewer = 'viewer';

    public function label(): string
    {
        return match ($this) {
            self::Admin => 'Admin',
            self::Editor => 'Editor',
            self::Viewer => 'Viewer',
        };
    }

    public static function labelFor(self|string|null $role): string
    {
        if ($role instanceof self) {
            return $role->label();
        }

        if (is_string($role)) {
            return self::tryFrom($role)?->label() ?? $role;
        }

        return '';
    }

    public static function options(): array
    {
        return array_column(
            array_map(
                fn (self $role) => ['value' => $role->value, 'label' => $role->label()],
                self::cases()
            ),
            'label',
            'value'
        );
    }
}
