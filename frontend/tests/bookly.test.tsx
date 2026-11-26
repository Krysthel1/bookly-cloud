import { describe, it, expect, beforeEach } from 'vitest'
import { act, render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { BookCard } from '@/components/books/BookCard'
import { EmptyState } from '@/components/shared/EmptyState'
import { CartPage } from '@/pages/CartPage'
import { LoginPage } from '@/pages/AuthPages'
import { ProtectedRoute } from '@/routes/ProtectedRoute'
import { useCartStore } from '@/stores/useCartStore'
import { useAuthStore } from '@/stores/useAuthStore'
import type { Book } from '@/types'

const sampleBook: Book = {
  id: 'book-1',
  title: 'La ciudad y los perros',
  slug: 'la-ciudad-y-los-perros',
  isbn: '9788420412146',
  synopsis: 'Novela clásica de Mario Vargas Llosa.',
  price: 80,
  discount_percent: 10,
  final_price: 72,
  stock: 10,
  low_stock_threshold: 3,
  pages: 448,
  language: 'Español',
  is_featured: true,
  is_active: true,
  sales_count: 100,
  average_rating: 4.8,
  reviews_count: 12,
  authors: [
    {
      id: 'auth-1',
      name: 'Mario Vargas Llosa',
      slug: 'mvll',
      is_featured: true,
      is_active: true,
      books_count: 3,
    },
  ],
  categories: [
    {
      id: 'cat-1',
      name: 'Literatura',
      slug: 'literatura',
      is_active: true,
      books_count: 10,
    },
  ],
  images: [],
  created_at: new Date().toISOString(),
}

describe('BOOKLY Frontend Suite', () => {
  beforeEach(() => {
    localStorage.clear()
    useCartStore.setState({ items: [], itemsCount: 0, subtotal: 0, isLoading: false })
    useAuthStore.setState({ session: null, profile: null, isInitialized: true, isLoading: false })
  })

  it('renderiza BookCard con precio en soles, descuento y agrega al carrito', async () => {
    render(
      <MemoryRouter>
        <BookCard book={sampleBook} />
      </MemoryRouter>,
    )

    expect(screen.getAllByText('La ciudad y los perros').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Mario Vargas Llosa').length).toBeGreaterThan(0)
    expect(screen.getByText('-10%')).toBeInTheDocument()
    expect(screen.getByText('S/ 72.00')).toBeInTheDocument()

    const addBtn = screen.getByRole('button', { name: /Agregar La ciudad y los perros/i })
    fireEvent.click(addBtn)

    expect(useCartStore.getState().itemsCount).toBe(1)
    expect(useCartStore.getState().subtotal).toBe(72)
  })

  it('muestra estado vacío en CartPage y permite gestionar cantidades cuando hay ítems', async () => {
    const { rerender } = render(
      <MemoryRouter>
        <CartPage />
      </MemoryRouter>,
    )
    expect(screen.getByText('Tu carrito está vacío')).toBeInTheDocument()

    await act(async () => {
      await useCartStore.getState().addBook(sampleBook, 2)
    })
    rerender(
      <MemoryRouter>
        <CartPage />
      </MemoryRouter>,
    )
    expect(screen.getAllByText('La ciudad y los perros').length).toBeGreaterThan(0)
    expect(screen.getAllByText('S/ 144.00').length).toBeGreaterThan(0)
  })

  it('valida formulario de LoginPage con Zod antes de enviar', async () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Ingresar' }))
    expect(await screen.findByText('Ingresa un correo electrónico válido')).toBeInTheDocument()
    expect(await screen.findByText('La contraseña debe tener al menos 6 caracteres')).toBeInTheDocument()
  })

  it('protege rutas privadas y bloquea acceso administrativo a no-admins', () => {
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route path="/iniciar-sesion" element={<div>Pantalla Login</div>} />
          <Route path="/no-autorizado" element={<div>Acceso Denegado</div>} />
          <Route element={<ProtectedRoute requireAdmin />}>
            <Route path="/admin" element={<div>Panel Admin</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )
    expect(screen.getByText('Pantalla Login')).toBeInTheDocument()

    useAuthStore.setState({
      session: { access_token: 'tok' } as never,
      profile: {
        id: 'u1',
        email: 'c@bookly.pe',
        full_name: 'Cliente',
        is_active: true,
        roles: ['customer'],
        created_at: new Date().toISOString(),
      },
      isInitialized: true,
    })

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route path="/no-autorizado" element={<div>Acceso Denegado</div>} />
          <Route element={<ProtectedRoute requireAdmin />}>
            <Route path="/admin" element={<div>Panel Admin</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    )
    expect(screen.getByText('Acceso Denegado')).toBeInTheDocument()
  })

  it('renderiza EmptyState con acción personalizada', () => {
    let clicked = false
    render(
      <EmptyState
        title="Sin resultados"
        description="Prueba otra búsqueda"
        actionLabel="Limpiar"
        onAction={() => {
          clicked = true
        }}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Limpiar' }))
    expect(clicked).toBe(true)
  })
})
