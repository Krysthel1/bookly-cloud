import { useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { ShieldAlert, BookX } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input, Textarea } from '@/components/ui/input'

export function AboutPage() {
  return (
    <div className="container max-w-4xl py-14 space-y-8">
      <h1 className="font-serif text-4xl font-bold">Sobre BOOKLY</h1>
      <p className="text-lg text-muted-foreground leading-relaxed">
        BOOKLY nace como una librería digital curada orientada a conectar lectores peruanos con
        literatura contemporánea, clásicos universales y literatura técnica de vanguardia.
      </p>
      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-xl border bg-card/50 p-6 space-y-2">
          <h2 className="font-serif text-xl font-semibold">Nuestra curaduría</h2>
          <p className="text-sm text-muted-foreground">
            Cada obra es seleccionada por su calidad editorial, traducción y aporte cultural o
            profesional.
          </p>
        </div>
        <div className="rounded-xl border bg-card/50 p-6 space-y-2">
          <h2 className="font-serif text-xl font-semibold">Arquitectura en la nube</h2>
          <p className="text-sm text-muted-foreground">
            BOOKLY combina React, FastAPI, Supabase PostgreSQL y servicios AWS para brindar alta
            disponibilidad y seguridad.
          </p>
        </div>
      </div>
    </div>
  )
}

export function ContactPage() {
  const [sent, setSent] = useState(false)
  return (
    <div className="container max-w-2xl py-14 space-y-6">
      <h1 className="font-serif text-4xl font-bold">Contacto</h1>
      <p className="text-sm text-muted-foreground">
        ¿Tienes dudas sobre pedidos, disponibilidad de títulos o envíos corporativos? Escríbenos.
      </p>
      {sent ? (
        <div className="rounded-xl border bg-card p-6 space-y-3">
          <h2 className="font-serif text-xl font-semibold">Mensaje recibido</h2>
          <p className="text-sm text-muted-foreground">
            Nuestro equipo editorial te responderá dentro de las próximas 24 horas hábiles.
          </p>
          <Button onClick={() => setSent(false)} variant="outline">
            Enviar otra consulta
          </Button>
        </div>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault()
            setSent(true)
            toast.success('Consulta enviada correctamente')
          }}
          className="space-y-4 rounded-xl border bg-card/40 p-6"
        >
          <Input required placeholder="Nombre completo" />
          <Input required type="email" placeholder="Correo electrónico" />
          <Input required placeholder="Asunto" />
          <Textarea required placeholder="Escribe tu mensaje..." />
          <Button type="submit">Enviar mensaje</Button>
        </form>
      )}
    </div>
  )
}

export function FaqPage() {
  const faqs = [
    {
      q: '¿Los precios incluyen IGV y están en soles?',
      a: 'Sí, todos los precios publicados en BOOKLY se muestran en soles peruanos (S/).',
    },
    {
      q: '¿Cómo funcionan los pagos en la plataforma?',
      a: 'BOOKLY soporta pagos simulados con Tarjeta, Yape, Plin y Pago contra entrega con fines académicos. No se realizan cobros reales.',
    },
    {
      q: '¿Puedo cancelar un pedido después de confirmarlo?',
      a: 'Sí, mientras el pedido esté en estado Pendiente o Confirmado puedes cancelarlo desde Mi Cuenta y el stock se restaurará automáticamente.',
    },
    {
      q: '¿Cuánto cuesta el envío?',
      a: 'El recojo en tienda es gratuito. El envío estándar cuesta S/ 12.00 (gratis desde S/ 120.00) y el envío express S/ 22.00.',
    },
  ]
  return (
    <div className="container max-w-3xl py-14 space-y-6">
      <h1 className="font-serif text-4xl font-bold">Preguntas frecuentes</h1>
      <div className="space-y-4">
        {faqs.map((item) => (
          <div key={item.q} className="rounded-xl border bg-card/40 p-5 space-y-2">
            <h2 className="font-serif text-lg font-semibold">{item.q}</h2>
            <p className="text-sm text-muted-foreground">{item.a}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export function PrivacyPage() {
  return (
    <div className="container max-w-3xl py-14 space-y-5">
      <h1 className="font-serif text-4xl font-bold">Políticas de privacidad</h1>
      <p className="text-sm text-muted-foreground leading-relaxed">
        BOOKLY protege la confidencialidad de los datos personales de sus lectores conforme a las
        buenas prácticas de seguridad en la nube. Las credenciales de acceso son gestionadas
        mediante Supabase Auth y nunca se almacenan contraseñas en texto plano ni datos financieros
        sensibles de tarjetas.
      </p>
    </div>
  )
}

export function TermsPage() {
  return (
    <div className="container max-w-3xl py-14 space-y-5">
      <h1 className="font-serif text-4xl font-bold">Términos y condiciones</h1>
      <p className="text-sm text-muted-foreground leading-relaxed">
        Todas las transacciones efectuadas en BOOKLY utilizan precios validados en el servidor,
        control transaccional de inventario y métodos de pago simulados. Los cupones están sujetos
        a vigencia, monto mínimo y límite de usos configurado por la administración.
      </p>
    </div>
  )
}

export function NotFoundPage() {
  return (
    <div className="container flex min-h-[60vh] flex-col items-center justify-center py-16 text-center">
      <BookX className="h-12 w-12 text-primary" />
      <h1 className="mt-4 font-serif text-4xl font-bold">Página no encontrada (404)</h1>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        El capítulo que buscas no existe o fue movido. Vuelve al catálogo principal para seguir
        explorando.
      </p>
      <Button className="mt-6" asChild>
        <Link to="/">Volver al inicio</Link>
      </Button>
    </div>
  )
}

export function UnauthorizedPage() {
  return (
    <div className="container flex min-h-[60vh] flex-col items-center justify-center py-16 text-center">
      <ShieldAlert className="h-12 w-12 text-destructive" />
      <h1 className="mt-4 font-serif text-4xl font-bold">Acceso no autorizado (403)</h1>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        No cuentas con los permisos necesarios para ingresar a esta sección administrativa.
      </p>
      <Button className="mt-6" asChild>
        <Link to="/">Regresar a la tienda</Link>
      </Button>
    </div>
  )
}
