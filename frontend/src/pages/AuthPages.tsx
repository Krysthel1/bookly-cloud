import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { MailCheck } from 'lucide-react'
import { supabase, isSupabaseConfigured } from '@/lib/supabase'
import { useAuthStore } from '@/stores/useAuthStore'
import { useCartStore } from '@/stores/useCartStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/card'

const loginSchema = z.object({
  email: z.string().email('Ingresa un correo electrónico válido'),
  password: z.string().min(6, 'La contraseña debe tener al menos 6 caracteres'),
})

const registerSchema = z
  .object({
    fullName: z.string().min(2, 'Ingresa tu nombre completo'),
    email: z.string().email('Ingresa un correo electrónico válido'),
    password: z.string().min(8, 'Mínimo 8 caracteres'),
    confirmPassword: z.string(),
  })
  .refine((d) => d.password === d.confirmPassword, {
    message: 'Las contraseñas no coinciden',
    path: ['confirmPassword'],
  })

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { setSession, fetchProfile } = useAuthStore()
  const syncGuestCartOnLogin = useCartStore((s) => s.syncGuestCartOnLogin)
  const [submitting, setSubmitting] = useState(false)

  const from = (location.state as { from?: string } | null)?.from

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<z.infer<typeof loginSchema>>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (values: z.infer<typeof loginSchema>) => {
    if (!isSupabaseConfigured) {
      toast.error('Configura VITE_SUPABASE_URL y VITE_SUPABASE_PUBLISHABLE_KEY en .env')
      return
    }
    setSubmitting(true)
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: values.email,
        password: values.password,
      })
      if (error) throw error
      setSession(data.session)
      const profile = await fetchProfile()
      await syncGuestCartOnLogin()
      toast.success('¡Bienvenido de vuelta a BOOKLY!')

      if (from) {
        navigate(from, { replace: true })
      } else if (profile?.roles.includes('admin')) {
        navigate('/admin', { replace: true })
      } else {
        navigate('/', { replace: true })
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'No se pudo iniciar sesión')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="container flex min-h-[75vh] items-center justify-center py-12">
      <div className="w-full max-w-md space-y-6 rounded-2xl border bg-card/50 p-8 shadow-sm">
        <div className="space-y-1 text-center">
          <h1 className="font-serif text-3xl font-bold">Iniciar sesión</h1>
          <p className="text-sm text-muted-foreground">Accede a tu biblioteca y pedidos</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="email">Correo electrónico</Label>
            <Input id="email" type="email" placeholder="lector@bookly.pe" {...register('email')} />
            {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <Label htmlFor="password">Contraseña</Label>
              <Link to="/recuperar-contrasena" className="text-xs text-primary hover:underline">
                ¿Olvidaste tu contraseña?
              </Link>
            </div>
            <Input id="password" type="password" placeholder="••••••" {...register('password')} />
            {errors.password && (
              <p className="text-xs text-destructive">{errors.password.message}</p>
            )}
          </div>

          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? 'Ingresando...' : 'Ingresar'}
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          ¿Aún no tienes cuenta?{' '}
          <Link to="/registro" className="font-medium text-primary hover:underline">
            Regístrate aquí
          </Link>
        </p>
      </div>
    </div>
  )
}

export function RegisterPage() {
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<z.infer<typeof registerSchema>>({
    resolver: zodResolver(registerSchema),
  })

  const onSubmit = async (values: z.infer<typeof registerSchema>) => {
    if (!isSupabaseConfigured) {
      toast.error('Configura Supabase Auth en frontend/.env para registrar cuentas reales.')
      return
    }
    setSubmitting(true)
    try {
      const { error } = await supabase.auth.signUp({
        email: values.email,
        password: values.password,
        options: {
          data: { full_name: values.fullName },
          emailRedirectTo: `${window.location.origin}/confirmacion-correo`,
        },
      })
      if (error) throw error
      setRegisteredEmail(values.email)
      toast.success('Cuenta creada. Revisa tu bandeja para confirmar tu correo.')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Error al registrar usuario')
    } finally {
      setSubmitting(false)
    }
  }

  if (registeredEmail) {
    return (
      <div className="container flex min-h-[70vh] items-center justify-center py-12">
        <div className="max-w-md space-y-4 rounded-2xl border bg-card/50 p-8 text-center">
          <MailCheck className="mx-auto h-12 w-12 text-primary" />
          <h1 className="font-serif text-2xl font-bold">Confirma tu correo</h1>
          <p className="text-sm text-muted-foreground">
            Enviamos un enlace de verificación a <strong>{registeredEmail}</strong>. Haz clic en él
            para activar tu cuenta de cliente en BOOKLY.
          </p>
          <Button asChild className="w-full">
            <Link to="/iniciar-sesion">Ir a iniciar sesión</Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="container flex min-h-[75vh] items-center justify-center py-12">
      <div className="w-full max-w-md space-y-6 rounded-2xl border bg-card/50 p-8 shadow-sm">
        <div className="space-y-1 text-center">
          <h1 className="font-serif text-3xl font-bold">Crear cuenta</h1>
          <p className="text-sm text-muted-foreground">Únete a la comunidad lectora de BOOKLY</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="fullName">Nombre completo</Label>
            <Input id="fullName" placeholder="María Quispe" {...register('fullName')} />
            {errors.fullName && (
              <p className="text-xs text-destructive">{errors.fullName.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="reg-email">Correo electrónico</Label>
            <Input id="reg-email" type="email" placeholder="maria@correo.com" {...register('email')} />
            {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="reg-pass">Contraseña</Label>
            <Input id="reg-pass" type="password" placeholder="Mínimo 8 caracteres" {...register('password')} />
            {errors.password && (
              <p className="text-xs text-destructive">{errors.password.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="reg-confirm">Confirmar contraseña</Label>
            <Input id="reg-confirm" type="password" {...register('confirmPassword')} />
            {errors.confirmPassword && (
              <p className="text-xs text-destructive">{errors.confirmPassword.message}</p>
            )}
          </div>

          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? 'Registrando...' : 'Crear cuenta de cliente'}
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          ¿Ya tienes una cuenta?{' '}
          <Link to="/iniciar-sesion" className="font-medium text-primary hover:underline">
            Inicia sesión
          </Link>
        </p>
      </div>
    </div>
  )
}

export function EmailConfirmationPage() {
  return (
    <div className="container flex min-h-[65vh] items-center justify-center py-12">
      <div className="max-w-md space-y-4 rounded-2xl border bg-card/50 p-8 text-center">
        <MailCheck className="mx-auto h-12 w-12 text-primary" />
        <h1 className="font-serif text-2xl font-bold">Correo verificado</h1>
        <p className="text-sm text-muted-foreground">
          Tu cuenta ha sido confirmada exitosamente. Ya puedes iniciar sesión y realizar compras.
        </p>
        <Button asChild className="w-full">
          <Link to="/iniciar-sesion">Iniciar sesión</Link>
        </Button>
      </div>
    </div>
  )
}

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/restablecer-contrasena`,
    })
    if (error) {
      toast.error(error.message)
      return
    }
    setSent(true)
    toast.success('Enlace de recuperación enviado')
  }

  return (
    <div className="container flex min-h-[70vh] items-center justify-center py-12">
      <div className="w-full max-w-md space-y-5 rounded-2xl border bg-card/50 p-8">
        <h1 className="font-serif text-2xl font-bold">Recuperar contraseña</h1>
        {sent ? (
          <p className="text-sm text-muted-foreground">
            Revisa tu correo <strong>{email}</strong> para restablecer tu contraseña.
          </p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Tu correo registrado"
            />
            <Button type="submit" className="w-full">
              Enviar enlace de recuperación
            </Button>
          </form>
        )}
      </div>
    </div>
  )
}

export function ResetPasswordPage() {
  const [password, setPassword] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const { error } = await supabase.auth.updateUser({ password })
    if (error) {
      toast.error(error.message)
      return
    }
    toast.success('Contraseña actualizada correctamente')
    navigate('/iniciar-sesion')
  }

  return (
    <div className="container flex min-h-[70vh] items-center justify-center py-12">
      <div className="w-full max-w-md space-y-5 rounded-2xl border bg-card/50 p-8">
        <h1 className="font-serif text-2xl font-bold">Restablecer contraseña</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Nueva contraseña (mín. 8 caracteres)"
          />
          <Button type="submit" className="w-full">
            Guardar nueva contraseña
          </Button>
        </form>
      </div>
    </div>
  )
}
