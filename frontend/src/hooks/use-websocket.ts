import { useState, useEffect, useRef, useCallback } from 'react';
import { getAccessToken } from '@/lib/api-client';

declare const process: { env: { NODE_ENV: string } };
import type { WebSocketMessage } from '@/types/api';
import { WebSocketEvent } from '@/types/api';

// Extend Window interface to include WebSocket types
declare global {
  interface Window {
    WebSocket: typeof WebSocket;
    __wsConnected?: boolean;
    __wsStatus?: 'connecting' | 'connected' | 'disconnected' | 'error';
    __wsReconnectAttempts?: number;
    testWebSocket?: WebSocket | null;
  }
}

const websocketEventValues = new Set<string>(Object.values(WebSocketEvent));

const legacyEventMap: Record<string, WebSocketEvent> = {
  'pipeline:update': WebSocketEvent.PIPELINE_UPDATE,
  'queue:update': WebSocketEvent.QUEUE_UPDATE,
  'metrics:update': WebSocketEvent.HARDWARE_UPDATE,
  'alert:new': WebSocketEvent.ALERT_TRIGGERED,
  'hardware:update': WebSocketEvent.HARDWARE_UPDATE,
};

function normalizeEventType(value?: string): WebSocketEvent | null {
  if (!value) {
    return null;
  }

  if (websocketEventValues.has(value)) {
    return value as WebSocketEvent;
  }

  const mapped = legacyEventMap[value];
  if (mapped) {
    return mapped;
  }

  const transformed = value.replace(/[:\-]/g, '_');
  if (websocketEventValues.has(transformed)) {
    return transformed as WebSocketEvent;
  }

  return null;
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
  sendMessage: <T>(message: WebSocketMessage<T>) => boolean;
}

export function useWebSocket({
  enabled = true,
  onMessage,
  onError,
  onReconnect,
  onClose,
  reconnectAttempts: initialReconnectAttempts = 0,
  reconnectInterval = 1000,
  maxReconnectAttempts = 5,
}: WebSocketOptions): UseWebSocketResult {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<WebSocketError | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(initialReconnectAttempts);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  const connect = useCallback(() => {
    if (!enabled) return;

    // Close any existing connection
    if (ws.current) {
      ws.current.close();
    }

    const token = getAccessToken();
    if (!token) {
      setError({
        code: 401,
        message: 'No authentication token available',
      });
      return;
    }

    try {
      const wsUrl = new URL('/ws/monitoring', window.location.origin);
      wsUrl.protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsUrl.searchParams.set('token', token);

      ws.current = new WebSocket(wsUrl.toString());
      // Expose the WebSocket instance for E2E test reconnection when in test environment
      if (process.env.NODE_ENV === 'test') {
        window.testWebSocket = ws.current;
      }
      
      // Also expose initial status
      window.__wsConnected = false;
      window.__wsStatus = 'connecting';

      ws.current.onopen = () => {
        setIsConnected(true);
        setReconnectAttempts(0);
        setError(null);

        // Expose status to window for tests
        window.__wsConnected = true;
        window.__wsStatus = 'connected';

        // Start heartbeat
        heartbeatInterval.current = setInterval(() => {
          if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send('ping');
          }
        }, 30000);
      };

      ws.current.onmessage = (event) => {
        try {
          const raw = JSON.parse(event.data) as Record<string, unknown>;
          const resolvedType = normalizeEventType(
            (raw.type as string | undefined) ?? (raw.event as string | undefined)
          );

          if (!resolvedType) {
            console.warn('Received WebSocket message with unknown type', raw);
            return;
          }

          const normalizedMessage: WebSocketMessage = {
            type: resolvedType,
            data: raw.data as WebSocketMessage['data'],
            timestamp:
              typeof raw.timestamp === 'string' && raw.timestamp.length > 0
                ? raw.timestamp
                : new Date().toISOString(),
          };

          setLastMessage(normalizedMessage);
          onMessage(normalizedMessage);
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.current.onerror = (event) => {
        const error: WebSocketError = {
          code: 0,
          message: 'WebSocket error',
          details: event,
        };
        setError(error);
        
        // Expose status to window for tests
        window.__wsConnected = false;
        window.__wsStatus = 'error';
        
        onError?.(error);
      };

      ws.current.onclose = (event) => {
        setIsConnected(false);
        if (heartbeatInterval.current) {
          clearInterval(heartbeatInterval.current);
        }
        
        // Expose status to window for tests
        window.__wsConnected = false;
        window.__wsStatus = 'disconnected';
        
        onClose?.(event);

        // Attempt to reconnect if this wasn't an intentional close
        if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
          const attempts = reconnectAttempts + 1;
          setReconnectAttempts(attempts);
          onReconnect?.(attempts);

          // Exponential backoff
          const delay = Math.min(
            reconnectInterval * Math.pow(2, attempts - 1),
            30000 // Max 30 seconds
          );

      // Expose test-only globals
          if (process.env.NODE_ENV === 'test') {
            window.__wsReconnectAttempts = attempts;
            // @ts-ignore
            window.__wsReconnectDelayMs = delay;
          }

          // Also expose in development for debugging
          if (process.env.NODE_ENV !== 'production') {
            window.__wsReconnectAttempts = attempts;
          }

          reconnectTimer.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };
    } catch (err) {
      const error: WebSocketError = {
        code: 0,
        message: err instanceof Error ? err.message : 'Failed to connect to WebSocket',
        details: err,
      };
      setError(error);
      onError?.(error);
    }
  }, [enabled, onMessage, onError, onReconnect, onClose, reconnectAttempts, maxReconnectAttempts, reconnectInterval]);

  const sendMessage = useCallback(<T>(message: WebSocketMessage<T>) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  const reconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
    }
    setReconnectAttempts(0);
    connect();
  }, [connect]);

  // Connect on mount and when dependencies change
  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      if (ws.current) {
        ws.current.close();
        ws.current = null;
      }
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
      }
      if (heartbeatInterval.current) {
        clearInterval(heartbeatInterval.current);
        heartbeatInterval.current = null;
      }
    };
  }, [enabled, connect]);

  return {
    isConnected,
    lastMessage,
    error,
    reconnect,
    sendMessage,
  };
}
