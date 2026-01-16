<?php

namespace App\Casts;

use Illuminate\Contracts\Database\Eloquent\CastsAttributes;
use Illuminate\Database\Eloquent\Model;

class PostgresArrayCast implements CastsAttributes
{
    /**
     * Cast the given value from PostgreSQL array to PHP array.
     *
     * @param  array<string, mixed>  $attributes
     */
    public function get(Model $model, string $key, mixed $value, array $attributes): ?array
    {
        if ($value === null) {
            return null;
        }

        if (is_array($value)) {
            return $value;
        }

        if (is_string($value)) {
            $trimmed = trim($value, '{}');
            if ($trimmed === '') {
                return [];
            }
            return array_map(fn($item) => trim($item, '"'), explode(',', $trimmed));
        }

        return null;
    }

    /**
     * Prepare the given value for storage as PostgreSQL array literal.
     *
     * @param  array<string, mixed>  $attributes
     */
    public function set(Model $model, string $key, mixed $value, array $attributes): ?string
    {
        if ($value === null) {
            return null;
        }

        if (!is_array($value)) {
            $value = [$value];
        }

        if (empty($value)) {
            return '{}';
        }

        $escaped = array_map(function ($item) {
            $item = str_replace('\\', '\\\\', $item);
            $item = str_replace('"', '\\"', $item);
            return '"' . $item . '"';
        }, $value);

        return '{' . implode(',', $escaped) . '}';
    }
}
