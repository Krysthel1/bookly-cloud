import { create } from 'zustand'
import { toast } from 'sonner'
import type { Book, CartItem } from '@/types'
import { cartApi } from '@/services/booklyApi'
import { extractApiError } from '@/lib/api'
import { useAuthStore } from '@/stores/useAuthStore'

const GUEST_CART_KEY = 'bookly-guest-cart'

interface CartState {
  items: CartItem[]
  itemsCount: number
  subtotal: number
  isLoading: boolean
  fetchCart: () => Promise<void>
  addBook: (book: Book, quantity?: number) => Promise<void>
  updateQuantity: (itemId: string, quantity: number) => Promise<void>
  removeItem: (itemId: string) => Promise<void>
  clearCart: () => Promise<void>
  syncGuestCartOnLogin: () => Promise<void>
}

function loadGuestItems(): CartItem[] {
  try {
    const raw = localStorage.getItem(GUEST_CART_KEY)
    return raw ? (JSON.parse(raw) as CartItem[]) : []
  } catch {
    return []
  }
}

function saveGuestItems(items: CartItem[]) {
  localStorage.setItem(GUEST_CART_KEY, JSON.stringify(items))
}

function computeTotals(items: CartItem[]) {
  const itemsCount = items.reduce((acc, i) => acc + i.quantity, 0)
  const subtotal = items.reduce((acc, i) => acc + Number(i.book.final_price) * i.quantity, 0)
  return { itemsCount, subtotal: Number(subtotal.toFixed(2)) }
}

export const useCartStore = create<CartState>((set, get) => ({
  items: loadGuestItems(),
  ...computeTotals(loadGuestItems()),
  isLoading: false,

  fetchCart: async () => {
    const session = useAuthStore.getState().session
    if (!session) {
      const guest = loadGuestItems()
      set({ items: guest, ...computeTotals(guest) })
      return
    }
    set({ isLoading: true })
    try {
      const cart = await cartApi.getCart()
      set({
        items: cart.items,
        itemsCount: cart.items_count,
        subtotal: Number(cart.subtotal),
      })
    } finally {
      set({ isLoading: false })
    }
  },

  addBook: async (book, quantity = 1) => {
    const session = useAuthStore.getState().session
    if (!session) {
      const current = [...get().items]
      const existing = current.find((i) => i.book_id === book.id)
      const targetQty = (existing?.quantity || 0) + quantity
      if (targetQty > book.stock) {
        toast.error(`Stock insuficiente. Disponible: ${book.stock}`)
        return
      }
      if (existing) {
        existing.quantity = targetQty
        existing.line_subtotal = Number(book.final_price) * targetQty
      } else {
        current.push({
          id: `guest-${book.id}`,
          book_id: book.id,
          quantity,
          line_subtotal: Number(book.final_price) * quantity,
          book: {
            id: book.id,
            title: book.title,
            slug: book.slug,
            isbn: book.isbn,
            cover_url: book.cover_url,
            price: book.price,
            discount_percent: book.discount_percent,
            final_price: book.final_price,
            stock: book.stock,
            authors: book.authors.map((a) => a.name),
          },
        })
      }
      saveGuestItems(current)
      set({ items: current, ...computeTotals(current) })
      toast.success(`"${book.title}" agregado al carrito`)
      return
    }

    try {
      const cart = await cartApi.addItem(book.id, quantity)
      set({
        items: cart.items,
        itemsCount: cart.items_count,
        subtotal: Number(cart.subtotal),
      })
      toast.success(`"${book.title}" agregado al carrito`)
    } catch (error) {
      toast.error(extractApiError(error))
    }
  },

  updateQuantity: async (itemId, quantity) => {
    const session = useAuthStore.getState().session
    if (!session) {
      const current = get().items.map((item) => {
        if (item.id !== itemId) return item
        if (quantity > item.book.stock) {
          toast.error(`Stock máximo disponible: ${item.book.stock}`)
          return item
        }
        return {
          ...item,
          quantity,
          line_subtotal: Number(item.book.final_price) * quantity,
        }
      })
      saveGuestItems(current)
      set({ items: current, ...computeTotals(current) })
      return
    }

    try {
      const cart = await cartApi.updateItem(itemId, quantity)
      set({
        items: cart.items,
        itemsCount: cart.items_count,
        subtotal: Number(cart.subtotal),
      })
    } catch (error) {
      toast.error(extractApiError(error))
    }
  },

  removeItem: async (itemId) => {
    const session = useAuthStore.getState().session
    if (!session) {
      const current = get().items.filter((i) => i.id !== itemId)
      saveGuestItems(current)
      set({ items: current, ...computeTotals(current) })
      toast.success('Libro eliminado del carrito')
      return
    }

    try {
      const cart = await cartApi.removeItem(itemId)
      set({
        items: cart.items,
        itemsCount: cart.items_count,
        subtotal: Number(cart.subtotal),
      })
      toast.success('Libro eliminado del carrito')
    } catch (error) {
      toast.error(extractApiError(error))
    }
  },

  clearCart: async () => {
    const session = useAuthStore.getState().session
    if (!session) {
      localStorage.removeItem(GUEST_CART_KEY)
      set({ items: [], itemsCount: 0, subtotal: 0 })
      return
    }
    const cart = await cartApi.clearCart()
    set({ items: cart.items, itemsCount: cart.items_count, subtotal: Number(cart.subtotal) })
  },

  syncGuestCartOnLogin: async () => {
    const guest = loadGuestItems()
    if (guest.length > 0) {
      for (const item of guest) {
        try {
          await cartApi.addItem(item.book_id, item.quantity)
        } catch {
          // Ignorar si excede stock actual al sincronizar
        }
      }
      localStorage.removeItem(GUEST_CART_KEY)
    }
    await get().fetchCart()
  },
}))
