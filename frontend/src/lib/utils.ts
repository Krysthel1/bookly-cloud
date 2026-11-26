import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatPEN(amount: number | string | null | undefined): string {
  const num = Number(amount ?? 0)
  return `S/ ${num.toLocaleString('es-PE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

export function formatDatePE(value: string | Date | null | undefined): string {
  if (!value) return '—'
  const d = typeof value === 'string' ? new Date(value) : value
  return d.toLocaleDateString('es-PE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export const ORDER_STATUS_LABELS: Record<string, string> = {
  pendiente: 'Pendiente',
  confirmado: 'Confirmado',
  en_preparacion: 'En preparación',
  enviado: 'Enviado',
  entregado: 'Entregado',
  cancelado: 'Cancelado',
}

export const PAYMENT_METHOD_LABELS: Record<string, string> = {
  tarjeta: 'Tarjeta de crédito / débito',
  yape: 'Yape',
  plin: 'Plin',
  contra_entrega: 'Pago contra entrega',
}
