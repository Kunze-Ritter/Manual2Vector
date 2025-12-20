<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Services\AiAgentService;

Route::get('/', function () {
    return view('welcome');
});

Route::middleware(['web', 'auth'])->prefix('kradmin')->group(function () {
    Route::post('/ai-chat/stream', function (Request $request) {
        $sessionId = $request->input('session_id');
        $message = $request->input('message');

        if (!$sessionId || !$message) {
            abort(400, 'Missing session_id or message');
        }

        $service = app(AiAgentService::class);
        return $service->chatStream($message, $sessionId);
    })->name('ai-chat.stream');
});
