<?php

namespace App\Models;

use App\Enums\ChatMessageRole;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class ChatMessage extends Model
{
    protected $table = 'krai_users.chat_messages';

    public $timestamps = false;

    protected $fillable = [
        'session_id',
        'role',
        'content',
    ];

    protected $casts = [
        'created_at' => 'datetime',
        'role' => ChatMessageRole::class,
    ];

    public function session(): BelongsTo
    {
        return $this->belongsTo(ChatSession::class, 'session_id');
    }
}
