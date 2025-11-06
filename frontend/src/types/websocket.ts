export interface WebSocketMessage<T = any> {
  event: string;
  data: T;
  timestamp: string;
}

export interface WebSocketError {
  code: number;
  message: string;
  details?: unknown;
}

export interface WebSocketOptions {
  enabled?: boolean;
  onMessage: (message: WebSocketMessage) => void;
  onError?: (error: WebSocketError) => void;
  onReconnect?: (attempt: number) => void;
  onClose?: (event: CloseEvent) => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export interface UseWebSocketResult {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  error: WebSocketError | null;
  reconnect: () => void;
  sendMessage: <T>(message: WebSocketMessage<T>) => void;
}
