<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Services\AiAgentService;

Route::get('/', function () {
    return view('welcome');
});

Route::middleware(['web', 'auth'])->prefix('kradmin')->group(function () {
    Route::post('/ai-chat/stream', function (Request $request) {
        $validated = $request->validate([
            'session_id' => 'required|string|max:255',
            'message'    => 'required|string|max:2000',
        ]);

        $service = app(AiAgentService::class);
        return $service->chatStream($validated['message'], $validated['session_id']);
    })->name('ai-chat.stream');
});
