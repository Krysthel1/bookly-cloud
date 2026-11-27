import { apiClient } from '@/lib/api'
import type {
  Address,
  AdminUser,
  AuditLog,
  Author,
  Book,
  Cart,
  Category,
  Coupon,
  CouponValidation,
  DashboardData,
  InventoryBook,
  InventoryMovement,
  Notification,
  Order,
  PaginatedResponse,
  Publisher,
  Review,
  UserProfile,
} from '@/types'

export const catalogApi = {
  getBooks: async (params?: Record<string, unknown>) => {
    const { data } = await apiClient.get<PaginatedResponse<Book>>('/books', { params })
    return data
  },
  getFeatured: async (limit = 8) => {
    const { data } = await apiClient.get<Book[]>('/books/featured', { params: { limit } })
    return data
  },
  getBestSellers: async (limit = 8) => {
    const { data } = await apiClient.get<Book[]>('/books/best-sellers', { params: { limit } })
    return data
  },
  getNewReleases: async (limit = 8) => {
    const { data } = await apiClient.get<Book[]>('/books/new-releases', { params: { limit } })
    return data
  },
  getBook: async (idOrSlug: string) => {
    const { data } = await apiClient.get<Book>(`/books/${idOrSlug}`)
    return data
  },
  getRelated: async (idOrSlug: string) => {
    const { data } = await apiClient.get<Book[]>(`/books/${idOrSlug}/related`)
    return data
  },
  getReviews: async (idOrSlug: string) => {
    const { data } = await apiClient.get<Review[]>(`/books/${idOrSlug}/reviews`)
    return data
  },
  createReview: async (idOrSlug: string, payload: { rating: number; title?: string; comment: string }) => {
    const { data } = await apiClient.post<Review>(`/books/${idOrSlug}/reviews`, payload)
    return data
  },
  getCategories: async (params?: { search?: string; page?: number; page_size?: number }) => {
    const { data } = await apiClient.get<PaginatedResponse<Category>>('/categories', {
      params: { page_size: 50, ...params },
    })
    return data
  },
  getAuthors: async (params?: { featured?: boolean; search?: string; page?: number; page_size?: number }) => {
    const { data } = await apiClient.get<PaginatedResponse<Author>>('/authors', {
      params: { page_size: 50, ...params },
    })
    return data
  },
  getPublishers: async () => {
    const { data } = await apiClient.get<Publisher[]>('/publishers')
    return data
  },
}

export const cartApi = {
  getCart: async () => {
    const { data } = await apiClient.get<Cart>('/cart')
    return data
  },
  addItem: async (book_id: string, quantity = 1) => {
    const { data } = await apiClient.post<Cart>('/cart/items', { book_id, quantity })
    return data
  },
  updateItem: async (itemId: string, quantity: number) => {
    const { data } = await apiClient.patch<Cart>(`/cart/items/${itemId}`, { quantity })
    return data
  },
  removeItem: async (itemId: string) => {
    const { data } = await apiClient.delete<Cart>(`/cart/items/${itemId}`)
    return data
  },
  clearCart: async () => {
    const { data } = await apiClient.delete<Cart>('/cart')
    return data
  },
}

export const favoritesApi = {
  list: async () => {
    const { data } = await apiClient.get<Book[]>('/favorites')
    return data
  },
  add: async (book_id: string) => {
    const { data } = await apiClient.post<Book[]>('/favorites', { book_id })
    return data
  },
  remove: async (bookId: string) => {
    const { data } = await apiClient.delete<Book[]>(`/favorites/${bookId}`)
    return data
  },
}

export const ordersApi = {
  validateCoupon: async (code: string, subtotal: number) => {
    const { data } = await apiClient.post<CouponValidation>('/coupons/validate', { code, subtotal })
    return data
  },
  checkout: async (payload: {
    address_id?: string
    shipping_address?: Record<string, string>
    shipping_method: 'estandar' | 'express' | 'recojo_tienda'
    payment_method: 'tarjeta' | 'yape' | 'plin' | 'contra_entrega'
    coupon_code?: string
    notes?: string
    idempotency_key: string
  }) => {
    const { data } = await apiClient.post<Order>('/orders/checkout', payload, {
      headers: { 'Idempotency-Key': payload.idempotency_key },
    })
    return data
  },
  listMine: async (page = 1) => {
    const { data } = await apiClient.get<PaginatedResponse<Order>>('/orders', { params: { page } })
    return data
  },
  getDetail: async (orderId: string) => {
    const { data } = await apiClient.get<Order>(`/orders/${orderId}`)
    return data
  },
  cancelOrder: async (orderId: string) => {
    const { data } = await apiClient.post<Order>(`/orders/${orderId}/cancel`)
    return data
  },
}

export const accountApi = {
  updateProfile: async (payload: { full_name?: string; phone?: string; avatar_url?: string }) => {
    const { data } = await apiClient.patch<UserProfile>('/users/me', payload)
    return data
  },
  uploadAvatar: async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const { data } = await apiClient.post<UserProfile>('/users/me/avatar', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },
  listAddresses: async () => {
    const { data } = await apiClient.get<Address[]>('/users/me/addresses')
    return data
  },
  createAddress: async (payload: Omit<Address, 'id' | 'created_at'>) => {
    const { data } = await apiClient.post<Address>('/users/me/addresses', payload)
    return data
  },
  updateAddress: async (id: string, payload: Partial<Omit<Address, 'id' | 'created_at'>>) => {
    const { data } = await apiClient.patch<Address>(`/users/me/addresses/${id}`, payload)
    return data
  },
  deleteAddress: async (id: string) => {
    await apiClient.delete(`/users/me/addresses/${id}`)
  },
  listNotifications: async () => {
    const { data } = await apiClient.get<Notification[]>('/users/me/notifications')
    return data
  },
  markNotificationRead: async (id: string) => {
    const { data } = await apiClient.patch<Notification>(`/users/me/notifications/${id}/read`)
    return data
  },
}

export const adminApi = {
  getDashboard: async (params?: { start_date?: string; end_date?: string }) => {
    const { data } = await apiClient.get<DashboardData>('/admin/dashboard', { params })
    return data
  },
  listBooks: async (params?: { search?: string; page?: number; page_size?: number }) => {
    const { data } = await apiClient.get<PaginatedResponse<Book>>('/admin/books', { params })
    return data
  },
  createBook: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post<Book>('/admin/books', payload)
    return data
  },
  updateBook: async (id: string, payload: Record<string, unknown>) => {
    const { data } = await apiClient.patch<Book>(`/admin/books/${id}`, payload)
    return data
  },
  deactivateBook: async (id: string) => {
    await apiClient.delete(`/admin/books/${id}`)
  },
  createCategory: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post<Category>('/admin/categories', payload)
    return data
  },
  updateCategory: async (id: string, payload: Record<string, unknown>) => {
    const { data } = await apiClient.patch<Category>(`/admin/categories/${id}`, payload)
    return data
  },
  deleteCategory: async (id: string) => {
    await apiClient.delete(`/admin/categories/${id}`)
  },
  createAuthor: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post<Author>('/admin/authors', payload)
    return data
  },
  updateAuthor: async (id: string, payload: Record<string, unknown>) => {
    const { data } = await apiClient.patch<Author>(`/admin/authors/${id}`, payload)
    return data
  },
  deleteAuthor: async (id: string) => {
    await apiClient.delete(`/admin/authors/${id}`)
  },
  listInventory: async (params?: { search?: string; page?: number }) => {
    const { data } = await apiClient.get<PaginatedResponse<InventoryBook>>('/admin/inventory', { params })
    return data
  },
  listLowStock: async () => {
    const { data } = await apiClient.get<PaginatedResponse<InventoryBook>>('/admin/inventory/low-stock')
    return data
  },
  createMovement: async (payload: {
    book_id: string
    movement_type: 'entrada' | 'salida' | 'ajuste'
    quantity: number
    reason: string
  }) => {
    const { data } = await apiClient.post<InventoryMovement>('/admin/inventory/movements', payload)
    return data
  },
  listMovements: async (page = 1) => {
    const { data } = await apiClient.get<PaginatedResponse<InventoryMovement>>('/admin/inventory/movements', {
      params: { page },
    })
    return data
  },
  listOrders: async (params?: { status?: string; search?: string; page?: number }) => {
    const { data } = await apiClient.get<PaginatedResponse<Order>>('/admin/orders', { params })
    return data
  },
  updateOrderStatus: async (id: string, status: string, reason?: string) => {
    const { data } = await apiClient.patch<Order>(`/admin/orders/${id}/status`, { status, reason })
    return data
  },
  listUsers: async (params?: { search?: string; is_active?: boolean; page?: number }) => {
    const { data } = await apiClient.get<PaginatedResponse<AdminUser>>('/admin/users', { params })
    return data
  },
  getUserOrders: async (userId: string) => {
    const { data } = await apiClient.get<PaginatedResponse<Order>>(`/admin/users/${userId}/orders`)
    return data
  },
  listCoupons: async () => {
    const { data } = await apiClient.get<Coupon[]>('/admin/coupons')
    return data
  },
  createCoupon: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post<Coupon>('/admin/coupons', payload)
    return data
  },
  updateCoupon: async (id: string, payload: Record<string, unknown>) => {
    const { data } = await apiClient.patch<Coupon>(`/admin/coupons/${id}`, payload)
    return data
  },
  listAuditLogs: async (page = 1) => {
    const { data } = await apiClient.get<PaginatedResponse<AuditLog>>('/admin/audit-logs', {
      params: { page },
    })
    return data
  },
  getReport: async (
    reportType: 'sales' | 'inventory' | 'customers' | 'best-sellers',
    params?: { start_date?: string; end_date?: string },
  ) => {
    const { data } = await apiClient.get<{ report: string; count: number; rows: Record<string, unknown>[] }>(
      `/admin/reports/${reportType}`,
      { params },
    )
    return data
  },
  downloadReportCsv: async (
    reportType: 'sales' | 'inventory' | 'customers' | 'best-sellers',
    params?: { start_date?: string; end_date?: string },
  ) => {
    const response = await apiClient.get(`/admin/reports/${reportType}`, {
      params: { format: 'csv', ...params },
      responseType: 'blob',
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = `bookly-${reportType}.csv`
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
  },
  uploadImage: async (file: File, bucketType: 'covers' | 'images' = 'covers') => {
    const form = new FormData()
    form.append('file', file)
    const { data } = await apiClient.post<{ url: string }>('/admin/storage/upload', form, {
      params: { bucket_type: bucketType },
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },
}
