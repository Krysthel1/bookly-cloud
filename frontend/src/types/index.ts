export interface PaginationMeta {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface PaginatedResponse<T> {
  items: T[]
  meta: PaginationMeta
}

export interface UserProfile {
  id: string
  email: string
  full_name: string
  phone?: string | null
  avatar_url?: string | null
  is_active: boolean
  roles: string[]
  created_at: string
}

export interface Author {
  id: string
  name: string
  slug: string
  biography?: string | null
  nationality?: string | null
  photo_url?: string | null
  is_featured: boolean
  is_active: boolean
  books_count: number
}

export interface Category {
  id: string
  name: string
  slug: string
  description?: string | null
  icon?: string | null
  is_active: boolean
  books_count: number
}

export interface Publisher {
  id: string
  name: string
  slug: string
  country?: string | null
  website?: string | null
}

export interface BookImage {
  id: string
  image_url: string
  alt_text?: string | null
  display_order: number
  is_primary: boolean
}

export interface Book {
  id: string
  title: string
  slug: string
  isbn: string
  synopsis: string
  price: number | string
  discount_percent: number | string
  final_price: number | string
  stock: number
  low_stock_threshold: number
  pages?: number | null
  language: string
  publication_date?: string | null
  cover_url?: string | null
  is_featured: boolean
  is_active: boolean
  sales_count: number
  average_rating: number | string
  reviews_count: number
  publisher?: Publisher | null
  authors: Author[]
  categories: Category[]
  images: BookImage[]
  created_at: string
}

export interface Review {
  id: string
  book_id: string
  user_id: string
  user_name: string
  rating: number
  title?: string | null
  comment: string
  created_at: string
}

export interface CartBookSummary {
  id: string
  title: string
  slug: string
  isbn: string
  cover_url?: string | null
  price: number | string
  discount_percent: number | string
  final_price: number | string
  stock: number
  authors: string[]
}

export interface CartItem {
  id: string
  book_id: string
  quantity: number
  line_subtotal: number | string
  book: CartBookSummary
}

export interface Cart {
  id: string
  items: CartItem[]
  items_count: number
  subtotal: number | string
}

export interface Address {
  id: string
  label: string
  recipient_name: string
  phone: string
  street_address: string
  district: string
  city: string
  region: string
  postal_code?: string | null
  reference?: string | null
  is_default: boolean
  created_at: string
}

export interface OrderItem {
  id: string
  book_id: string
  book_title_snapshot: string
  book_isbn_snapshot: string
  unit_price: number | string
  discount_percent_snapshot: number | string
  final_unit_price: number | string
  quantity: number
  line_total: number | string
}

export interface Payment {
  id: string
  method: string
  status: string
  amount: number | string
  transaction_reference: string
  is_simulated: boolean
  paid_at?: string | null
}

export interface Order {
  id: string
  order_code: string
  user_id: string
  customer_name?: string | null
  customer_email?: string | null
  shipping_address_snapshot: Record<string, string | null | undefined>
  shipping_method: string
  status: string
  subtotal: number | string
  discount_amount: number | string
  shipping_cost: number | string
  total: number | string
  notes?: string | null
  stock_restored: boolean
  cancelled_at?: string | null
  created_at: string
  items: OrderItem[]
  payment?: Payment | null
}

export interface Notification {
  id: string
  title: string
  message: string
  type: string
  is_read: boolean
  link?: string | null
  created_at: string
}

export interface Coupon {
  id: string
  code: string
  description?: string | null
  discount_type: 'percentage' | 'fixed'
  discount_value: number | string
  min_order_amount: number | string
  max_uses?: number | null
  current_uses: number
  starts_at: string
  expires_at: string
  is_active: boolean
}

export interface CouponValidation {
  valid: boolean
  code: string
  discount_type: string
  discount_value: number | string
  discount_amount: number | string
  message: string
}

export interface DashboardSeriesPoint {
  label: string
  value: number
  count: number
}

export interface DashboardData {
  kpis: {
    total_revenue: number | string
    today_sales: number | string
    month_sales: number | string
    orders_count: number
    customers_count: number
    books_count: number
    low_stock_count: number
    average_ticket: number | string
    sales_variation_percent: number
  }
  sales_evolution: DashboardSeriesPoint[]
  monthly_revenue: DashboardSeriesPoint[]
  sales_by_category: DashboardSeriesPoint[]
  top_selling_books: DashboardSeriesPoint[]
  orders_by_status: DashboardSeriesPoint[]
  new_customers: DashboardSeriesPoint[]
}

export interface InventoryBook {
  id: string
  title: string
  isbn: string
  stock: number
  low_stock_threshold: number
  price: number | string
  is_active: boolean
  status_label: string
}

export interface InventoryMovement {
  id: string
  book_id: string
  book_title?: string | null
  movement_type: string
  quantity_delta: number
  previous_stock: number
  new_stock: number
  reason: string
  performer_name?: string | null
  created_at: string
}

export interface AuditLog {
  id: string
  actor_id?: string | null
  actor_email?: string | null
  action: string
  entity_type: string
  entity_id: string
  old_values?: Record<string, unknown> | null
  new_values?: Record<string, unknown> | null
  created_at: string
}

export interface AdminUser {
  id: string
  email: string
  full_name: string
  phone?: string | null
  is_active: boolean
  roles: string[]
  created_at: string
  orders_count: number
  total_spent: number
}
