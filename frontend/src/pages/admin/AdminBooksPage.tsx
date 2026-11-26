import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Edit, Plus, Trash2, Upload } from 'lucide-react'
import { toast } from 'sonner'
import { adminApi, catalogApi } from '@/services/booklyApi'
import { extractApiError } from '@/lib/api'
import { formatPEN } from '@/lib/utils'
import type { Book } from '@/types'
import { ConfirmModal } from '@/components/shared/ConfirmModal'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input, Textarea } from '@/components/ui/input'
import { Label } from '@/components/ui/card'

export function AdminBooksPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingBook, setEditingBook] = useState<Book | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Book | null>(null)

  const [form, setForm] = useState({
    title: '',
    isbn: '',
    synopsis: '',
    price: '59.00',
    discount_percent: '0',
    stock: '10',
    pages: '240',
    language: 'Español',
    cover_url: '',
    is_featured: false,
    author_id: '',
    category_id: '',
    publisher_id: '',
  })

  const { data: booksData } = useQuery({
    queryKey: ['admin-books', search, page],
    queryFn: () => adminApi.listBooks({ search: search || undefined, page, page_size: 15 }),
  })
  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => catalogApi.getCategories(),
  })
  const { data: authors } = useQuery({
    queryKey: ['authors-all'],
    queryFn: () => catalogApi.getAuthors({ page_size: 100 }),
  })
  const { data: publishers } = useQuery({
    queryKey: ['publishers'],
    queryFn: () => catalogApi.getPublishers(),
  })

  const openCreate = () => {
    setEditingBook(null)
    setForm({
      title: '',
      isbn: '',
      synopsis: '',
      price: '59.00',
      discount_percent: '0',
      stock: '10',
      pages: '240',
      language: 'Español',
      cover_url: '',
      is_featured: false,
      author_id: authors?.items[0]?.id || '',
      category_id: categories?.items[0]?.id || '',
      publisher_id: publishers?.[0]?.id || '',
    })
    setModalOpen(true)
  }

  const openEdit = (book: Book) => {
    setEditingBook(book)
    setForm({
      title: book.title,
      isbn: book.isbn,
      synopsis: book.synopsis,
      price: String(book.price),
      discount_percent: String(book.discount_percent),
      stock: String(book.stock),
      pages: String(book.pages || 200),
      language: book.language,
      cover_url: book.cover_url || '',
      is_featured: book.is_featured,
      author_id: book.authors[0]?.id || '',
      category_id: book.categories[0]?.id || '',
      publisher_id: book.publisher?.id || '',
    })
    setModalOpen(true)
  }

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        title: form.title,
        isbn: form.isbn,
        synopsis: form.synopsis,
        price: Number(form.price),
        discount_percent: Number(form.discount_percent),
        stock: Number(form.stock),
        pages: Number(form.pages) || undefined,
        language: form.language,
        cover_url: form.cover_url || undefined,
        is_featured: form.is_featured,
        publisher_id: form.publisher_id || undefined,
        author_ids: form.author_id ? [form.author_id] : [],
        category_ids: form.category_id ? [form.category_id] : [],
      }
      if (editingBook) return adminApi.updateBook(editingBook.id, payload)
      return adminApi.createBook(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-books'] })
      setModalOpen(false)
      toast.success(editingBook ? 'Libro actualizado' : 'Libro creado correctamente')
    },
    onError: (err) => toast.error(extractApiError(err)),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminApi.deactivateBook(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-books'] })
      setDeleteTarget(null)
      toast.success('Libro desactivado')
    },
    onError: (err) => toast.error(extractApiError(err)),
  })

  const handleCoverUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const uploaded = await adminApi.uploadImage(file, 'covers')
      setForm((f) => ({ ...f, cover_url: uploaded.url }))
      toast.success('Portada optimizada y subida a Supabase Storage')
    } catch (err) {
      toast.error(extractApiError(err))
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl font-bold">Gestión de libros</h1>
          <p className="text-sm text-muted-foreground">CRUD completo del catálogo BOOKLY.</p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4" />
          Nuevo libro
        </Button>
      </div>

      <Input
        placeholder="Buscar por título, autor o ISBN..."
        value={search}
        onChange={(e) => {
          setSearch(e.target.value)
          setPage(1)
        }}
        className="max-w-sm"
      />

      <div className="overflow-x-auto rounded-xl border">
        <table className="w-full text-left text-sm">
          <thead className="border-b bg-card/60 text-xs uppercase text-muted-foreground">
            <tr>
              <th className="p-3">Título</th>
              <th className="p-3">ISBN</th>
              <th className="p-3">Precio</th>
              <th className="p-3">Stock</th>
              <th className="p-3">Estado</th>
              <th className="p-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {(booksData?.items || []).map((book) => (
              <tr key={book.id} className="hover:bg-muted/30">
                <td className="p-3 font-medium">
                  {book.title}
                  {book.is_featured && (
                    <Badge variant="gold" className="ml-2">
                      Destacado
                    </Badge>
                  )}
                </td>
                <td className="p-3 font-mono text-xs">{book.isbn}</td>
                <td className="p-3">{formatPEN(book.final_price)}</td>
                <td className="p-3">{book.stock}</td>
                <td className="p-3">
                  <Badge variant={book.is_active ? 'secondary' : 'destructive'}>
                    {book.is_active ? 'Activo' : 'Inactivo'}
                  </Badge>
                </td>
                <td className="p-3 text-right space-x-1">
                  <Button variant="ghost" size="icon" onClick={() => openEdit(book)}>
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => setDeleteTarget(book)}>
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingBook ? 'Editar libro' : 'Crear nuevo libro'}</DialogTitle>
          </DialogHeader>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              saveMutation.mutate()
            }}
            className="grid gap-4 sm:grid-cols-2"
          >
            <div className="sm:col-span-2 space-y-1">
              <Label>Título</Label>
              <Input
                required
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>ISBN</Label>
              <Input
                required
                value={form.isbn}
                onChange={(e) => setForm({ ...form, isbn: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Idioma</Label>
              <Input
                value={form.language}
                onChange={(e) => setForm({ ...form, language: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Precio (S/)</Label>
              <Input
                type="number"
                step="0.01"
                required
                value={form.price}
                onChange={(e) => setForm({ ...form, price: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Descuento (%)</Label>
              <Input
                type="number"
                min="0"
                max="100"
                value={form.discount_percent}
                onChange={(e) => setForm({ ...form, discount_percent: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Stock</Label>
              <Input
                type="number"
                min="0"
                required
                value={form.stock}
                onChange={(e) => setForm({ ...form, stock: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Páginas</Label>
              <Input
                type="number"
                min="1"
                value={form.pages}
                onChange={(e) => setForm({ ...form, pages: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <Label>Autor</Label>
              <select
                value={form.author_id}
                onChange={(e) => setForm({ ...form, author_id: e.target.value })}
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                required
              >
                <option value="">Selecciona autor</option>
                {(authors?.items || []).map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <Label>Categoría</Label>
              <select
                value={form.category_id}
                onChange={(e) => setForm({ ...form, category_id: e.target.value })}
                className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                required
              >
                <option value="">Selecciona categoría</option>
                {(categories?.items || []).map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="sm:col-span-2 space-y-1">
              <Label>URL de portada o subir a Supabase Storage</Label>
              <div className="flex gap-2">
                <Input
                  value={form.cover_url}
                  onChange={(e) => setForm({ ...form, cover_url: e.target.value })}
                  placeholder="https://..."
                />
                <label className="inline-flex cursor-pointer items-center gap-1.5 rounded-md border px-3 text-xs font-medium hover:bg-muted">
                  <Upload className="h-3.5 w-3.5" />
                  Subir
                  <input type="file" accept="image/*" className="hidden" onChange={handleCoverUpload} />
                </label>
              </div>
            </div>
            <div className="sm:col-span-2 space-y-1">
              <Label>Sinopsis</Label>
              <Textarea
                required
                minLength={10}
                value={form.synopsis}
                onChange={(e) => setForm({ ...form, synopsis: e.target.value })}
              />
            </div>
            <label className="flex items-center gap-2 text-sm sm:col-span-2">
              <input
                type="checkbox"
                checked={form.is_featured}
                onChange={(e) => setForm({ ...form, is_featured: e.target.checked })}
              />
              Marcar como libro destacado
            </label>
            <div className="flex justify-end gap-2 sm:col-span-2">
              <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={saveMutation.isPending}>
                {saveMutation.isPending ? 'Guardando...' : 'Guardar libro'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmModal
        open={Boolean(deleteTarget)}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="¿Desactivar libro?"
        description={`El libro "${deleteTarget?.title}" dejará de mostrarse en el catálogo público.`}
        confirmLabel="Desactivar"
        destructive
        loading={deleteMutation.isPending}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
      />
    </div>
  )
}
