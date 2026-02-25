<?php

/**
 * KRAI Helper Functions
 *
 * Global helper functions for stage configuration access.
 * Extracted from config/krai.php because PHP's return statement
 * in config files prevents function definitions from being parsed.
 */

if (!function_exists('krai_stages')) {
    function krai_stages(): array
    {
        return config('krai.stages', []);
    }
}

if (!function_exists('krai_stage_label')) {
    function krai_stage_label(string $stage): string
    {
        return config("krai.stages.{$stage}.label", $stage);
    }
}

if (!function_exists('krai_stage_icon')) {
    function krai_stage_icon(string $stage): string
    {
        return config("krai.stages.{$stage}.icon", 'heroicon-o-cog');
    }
}

if (!function_exists('krai_stage_group')) {
    function krai_stage_group(string $stage): string
    {
        return config("krai.stages.{$stage}.group", 'processing');
    }
}

if (!function_exists('krai_stages_by_group')) {
    function krai_stages_by_group(): array
    {
        $stages = krai_stages();
        $groups = [];

        foreach ($stages as $key => $stage) {
            $group = $stage['group'];
            $groups[$group][$key] = $stage;
        }

        return $groups;
    }
}

if (!function_exists('krai_stage_options')) {
    function krai_stage_options(): array
    {
        $stages = krai_stages();
        $options = [];

        foreach ($stages as $key => $stage) {
            $options[$key] = $stage['label'];
        }

        return $options;
    }
}
