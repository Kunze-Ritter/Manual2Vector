<div class="text-center py-12">
    <x-filament::icon
        icon="heroicon-o-exclamation-triangle"
        class="w-16 h-16 mx-auto text-red-500 mb-4"
    />
    <h3 class="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">
        Fehler beim Abrufen des Stage-Status
    </h3>
    <div class="max-w-md mx-auto">
        <p class="text-sm text-red-700 dark:text-red-300 mb-4">
            Beim Abrufen der Stage-Informationen ist ein Fehler aufgetreten:
        </p>
        <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <p class="text-sm font-mono text-red-800 dark:text-red-200">
                {{ $error }}
            </p>
        </div>
        <p class="text-xs text-red-600 dark:text-red-400 mt-4">
            Bitte versuchen Sie es später erneut oder kontaktieren Sie den Support, falls das Problem weiterhin besteht.
        </p>
    </div>
</div>
