import { useCallback } from 'react'
import type { ReactNode } from 'react'
import { toast, type ExternalToast } from 'sonner'

interface ToastAction {
  label: string
  onClick: () => void
}

export type ToastPayload = ReactNode

export interface ToastOptions extends Omit<ExternalToast, 'description' | 'action'> {
  description?: ReactNode
  action?: ToastAction
}

export interface ToastPromiseHandlers<T = unknown> {
  loading: ToastPayload
  success?: ToastPayload | ((data: T) => ToastPayload)
  error?: ToastPayload | ((error: unknown) => ToastPayload)
}

const mapAction = (action?: ToastAction): ExternalToast['action'] =>
  action
    ? {
        label: action.label,
        onClick: action.onClick,
      }
    : undefined

const show = (payload: ToastPayload, options?: ToastOptions) =>
  toast(payload, {
    ...options,
    action: mapAction(options?.action),
    description: options?.description,
  })

const showWithVariant = (
  variant: 'success' | 'error' | 'info' | 'warning' | 'loading',
  payload: ToastPayload,
  options?: ToastOptions,
) => {
  const config = {
    ...options,
    action: mapAction(options?.action),
    description: options?.description,
  }

  switch (variant) {
    case 'success':
      return toast.success(payload, config)
    case 'error':
      return toast.error(payload, config)
    case 'info':
      return toast.info(payload, config)
    case 'warning':
      return toast.warning(payload, config)
    case 'loading':
      return toast.loading(payload, config)
    default:
      return toast(payload, config)
  }
}

export function useToast() {
  const notify = useCallback((payload: ToastPayload, options?: ToastOptions) => {
    return show(payload, options)
  }, [])

  const success = useCallback(
    (payload: ToastPayload, options?: ToastOptions) => showWithVariant('success', payload, options),
    [],
  )

  const error = useCallback(
    (payload: ToastPayload, options?: ToastOptions) => showWithVariant('error', payload, options),
    [],
  )

  const info = useCallback(
    (payload: ToastPayload, options?: ToastOptions) => showWithVariant('info', payload, options),
    [],
  )

  const warning = useCallback(
    (payload: ToastPayload, options?: ToastOptions) => showWithVariant('warning', payload, options),
    [],
  )

  const loading = useCallback(
    (payload: ToastPayload, options?: ToastOptions) => showWithVariant('loading', payload, options),
    [],
  )

  const dismiss = useCallback((id?: number | string) => {
    toast.dismiss(id)
  }, [])

  const promise = useCallback(<T>(promise: Promise<T> | (() => Promise<T>), handlers: ToastPromiseHandlers<T>) => {
    return toast.promise(promise, handlers)
  }, [])

  return {
    notify,
    success,
    error,
    info,
    warning,
    loading,
    dismiss,
    promise,
  }
}
