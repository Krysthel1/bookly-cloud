"""
Script de carga inicial (seed) para BOOKLY.
Registra roles, categorías, editoriales, autores, cupones y 42 libros de demostración.
Ejecutar:
    python scripts/seed.py
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import os
import re
import sys
from uuid import uuid4

from sqlalchemy import select

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import SessionLocal
from app.models.catalog import (
    Author,
    Book,
    BookAuthor,
    BookCategory,
    BookImage,
    Category,
    Publisher,
)
from app.models.commerce import Coupon
from app.models.operations import InventoryMovement
from app.models.user import Role


def slugify(text: str) -> str:
    value = text.lower().strip()
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n"
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value


def cover_placeholder(isbn: str, title: str, bg: str = "243D32") -> str:
    # Open Library Covers API usa ISBN reales para portadas de demostración públicas
    clean_isbn = isbn.replace("-", "")
    return f"https://covers.openlibrary.org/b/isbn/{clean_isbn}-L.jpg?default=false"


CATEGORIES_DATA = [
    ("Literatura Contemporánea", "BookOpen", "Narrativa moderna peruana, latinoamericana y universal."),
    ("Clásicos Universales", "Landmark", "Obras fundamentales que trascienden generaciones."),
    ("Ensayo y Pensamiento", "Feather", "Crítica cultural, filosofía, historia y reflexión."),
    ("Tecnología e Ingeniería", "Cpu", "Arquitectura de software, nube, IA y ciencia de datos."),
    ("Negocios y Liderazgo", "Briefcase", "Estrategia, economía, diseño de producto y gestión."),
    ("Ciencia Ficción y Fantasía", "Sparkles", "Mundos especulativos, distopías y épica literaria."),
    ("Poesía", "ScrollText", "Antologías poéticas de autores consagrados y contemporáneos."),
    ("Desarrollo Personal", "Compass", "Hábitos, psicología práctica y creatividad."),
]

PUBLISHERS_DATA = [
    ("Alfaguara", "España / Perú", "https://www.penguinlibros.com"),
    ("Seix Barral", "España", "https://www.planetadelibros.com"),
    ("Anagrama", "España", "https://www.anagrama-ed.es"),
    ("Debate", "España", "https://www.penguinlibros.com"),
    ("Fondo de Cultura Económica", "México / Perú", "https://www.fondodeculturaeconomica.com"),
    ("Peisa", "Perú", "https://www.peisa.com.pe"),
    ("O'Reilly Media", "Estados Unidos", "https://www.oreilly.com"),
    ("Tusquets Editores", "España", "https://www.tusquetseditores.com"),
]

AUTHORS_DATA = [
    ("Mario Vargas Llosa", "Peruana", True, "Premio Nobel de Literatura 2010 y referente de la narrativa hispanoamericana."),
    ("Julio Ramón Ribeyro", "Peruana", True, "Maestro indiscutible del cuento corto latinoamericano."),
    ("César Vallejo", "Peruana", True, "Poeta universal peruano, autor de Trilce y Los heraldos negros."),
    ("Gabriel García Márquez", "Colombiana", True, "Premio Nobel de Literatura 1982, figura central del realismo mágico."),
    ("Jorge Luis Borges", "Argentina", True, "Ensayista, cuentista y poeta fundamental del siglo XX."),
    ("Isabel Allende", "Chilena", True, "Narradora de éxito internacional y voz clave de la novela contemporánea."),
    ("Samanta Schweblin", "Argentina", False, "Autora multipremiada de cuento y novela breve contemporánea."),
    ("Haruki Murakami", "Japonesa", True, "Autor japonés reconocido por unir lo cotidiano con atmósferas oníricas."),
    ("Yuval Noah Harari", "Israelí", True, "Historiador y autor de ensayos sobre humanidad y tecnología."),
    ("Martin Kleppmann", "Británica", True, "Ingeniero de software y autor de referencia en sistemas distribuidos."),
    ("Eric Evans", "Estadounidense", False, "Pionero de Domain-Driven Design y modelado de software complejo."),
    ("Robert C. Martin", "Estadounidense", False, "Autor e ingeniero reconocido por sus principios de arquitectura limpia."),
    ("James Clear", "Estadounidense", False, "Especialista en formación de hábitos y mejora continua."),
    ("Ursula K. Le Guin", "Estadounidense", True, "Maestra de la ciencia ficción antropológica y la fantasía."),
    ("Frank Herbert", "Estadounidense", False, "Creador de la saga épica de ciencia ficción Dune."),
    ("Blanca Varela", "Peruana", True, "Una de las voces poéticas más influyentes de América Latina."),
    ("José María Arguedas", "Peruana", True, "Escritor y antropólogo peruano que retrató el mundo andino."),
    ("Byung-Chul Han", "Surcoreana", False, "Filósofo contemporáneo crítico de la sociedad digital."),
]

# 42 libros curados con datos completos, ISBN reales, precios en S/ y categorías
BOOKS_DATA = [
    ("La ciudad y los perros", "9788420412146", "Mario Vargas Llosa", "Literatura Contemporánea", "Alfaguara", 69.00, 10, 28, 448, date(2012, 5, 10), True, 185),
    ("Conversación en La Catedral", "9788420412153", "Mario Vargas Llosa", "Literatura Contemporánea", "Alfaguara", 85.00, 0, 16, 728, date(2013, 3, 14), True, 140),
    ("La tía Julia y el escribidor", "9788420471426", "Mario Vargas Llosa", "Literatura Contemporánea", "Alfaguara", 64.00, 15, 22, 464, date(2015, 8, 20), False, 92),
    ("La palabra del mudo", "9789972409332", "Julio Ramón Ribeyro", "Clásicos Universales", "Seix Barral", 79.00, 10, 34, 896, date(2019, 11, 5), True, 210),
    ("Prosas apátridas", "9788432229848", "Julio Ramón Ribeyro", "Ensayo y Pensamiento", "Seix Barral", 54.00, 0, 19, 208, date(2016, 4, 12), False, 88),
    ("Los heraldos negros", "9788437607115", "César Vallejo", "Poesía", "Peisa", 45.00, 0, 40, 160, date(2018, 6, 1), True, 165),
    ("Trilce", "9788437610139", "César Vallejo", "Poesía", "Peisa", 49.00, 10, 25, 224, date(2020, 2, 18), False, 110),
    ("Cien años de soledad", "9788497592208", "Gabriel García Márquez", "Clásicos Universales", "Debate", 72.00, 15, 45, 496, date(2017, 6, 15), True, 320),
    ("El amor en los tiempos del cólera", "9788497592451", "Gabriel García Márquez", "Clásicos Universales", "Debate", 68.00, 0, 30, 464, date(2018, 1, 22), False, 174),
    ("Crónica de una muerte anunciada", "9788497592437", "Gabriel García Márquez", "Clásicos Universales", "Debate", 48.00, 0, 38, 160, date(2019, 4, 3), False, 155),
    ("Ficciones", "9788499089508", "Jorge Luis Borges", "Clásicos Universales", "Debate", 58.00, 10, 29, 224, date(2014, 9, 10), True, 204),
    ("El Aleph", "9788499089515", "Jorge Luis Borges", "Clásicos Universales", "Debate", 59.00, 0, 24, 208, date(2014, 9, 10), False, 162),
    ("La casa de los espíritus", "9788401352898", "Isabel Allende", "Literatura Contemporánea", "Debate", 74.00, 12, 27, 464, date(2016, 11, 8), True, 148),
    ("Violeta", "9788401027550", "Isabel Allende", "Literatura Contemporánea", "Debate", 76.00, 0, 18, 400, date(2022, 1, 25), False, 129),
    ("Distancia de rescate", "9788439729655", "Samanta Schweblin", "Literatura Contemporánea", "Anagrama", 52.00, 0, 14, 128, date(2021, 5, 19), False, 83),
    ("Pájaros en la boca", "9788439732419", "Samanta Schweblin", "Literatura Contemporánea", "Anagrama", 56.00, 10, 12, 208, date(2021, 9, 11), False, 71),
    ("Tokio blues (Norwegian Wood)", "9788483835043", "Haruki Murakami", "Literatura Contemporánea", "Tusquets Editores", 69.00, 15, 33, 384, date(2015, 3, 1), True, 245),
    ("Kafka en la orilla", "9788483835050", "Haruki Murakami", "Literatura Contemporánea", "Tusquets Editores", 79.00, 0, 21, 616, date(2016, 7, 12), False, 167),
    ("1Q84", "9788483836231", "Haruki Murakami", "Ciencia Ficción y Fantasía", "Tusquets Editores", 115.00, 20, 11, 1312, date(2018, 10, 4), False, 118),
    ("Sapiens: De animales a dioses", "9788499926223", "Yuval Noah Harari", "Ensayo y Pensamiento", "Debate", 84.00, 15, 36, 496, date(2020, 2, 10), True, 290),
    ("Homo Deus", "9788499926711", "Yuval Noah Harari", "Ensayo y Pensamiento", "Debate", 86.00, 0, 20, 496, date(2021, 3, 15), False, 178),
    ("Nexus: Breve historia de las redes de información", "9788419642660", "Yuval Noah Harari", "Ensayo y Pensamiento", "Debate", 95.00, 10, 25, 576, date(2025, 9, 10), True, 145),
    ("Designing Data-Intensive Applications", "9781449373320", "Martin Kleppmann", "Tecnología e Ingeniería", "O'Reilly Media", 198.00, 10, 15, 616, date(2017, 4, 2), True, 230),
    ("Domain-Driven Design", "9780321125217", "Eric Evans", "Tecnología e Ingeniería", "O'Reilly Media", 215.00, 0, 9, 560, date(2003, 8, 30), False, 112),
    ("Clean Architecture", "9780134494166", "Robert C. Martin", "Tecnología e Ingeniería", "O'Reilly Media", 165.00, 15, 18, 432, date(2017, 9, 12), True, 198),
    ("Clean Code", "9780132350884", "Robert C. Martin", "Tecnología e Ingeniería", "O'Reilly Media", 172.00, 10, 22, 464, date(2008, 8, 11), False, 260),
    ("Hábitos atómicos", "9786077476719", "James Clear", "Desarrollo Personal", "Debate", 68.00, 20, 50, 328, date(2020, 6, 1), True, 410),
    ("La mano izquierda de la oscuridad", "9788445007334", "Ursula K. Le Guin", "Ciencia Ficción y Fantasía", "Anagrama", 65.00, 0, 17, 336, date(2021, 2, 4), False, 96),
    ("Los desposeídos", "9788445007341", "Ursula K. Le Guin", "Ciencia Ficción y Fantasía", "Anagrama", 67.00, 10, 13, 384, date(2022, 4, 18), False, 84),
    ("Un mago de Terramar", "9788445007358", "Ursula K. Le Guin", "Ciencia Ficción y Fantasía", "Anagrama", 62.00, 0, 24, 256, date(2020, 11, 2), False, 105),
    ("Dune", "9788466353779", "Frank Herbert", "Ciencia Ficción y Fantasía", "Debate", 89.00, 15, 31, 784, date(2021, 10, 14), True, 275),
    ("El mesías de Dune", "9788466355421", "Frank Herbert", "Ciencia Ficción y Fantasía", "Debate", 69.00, 0, 19, 320, date(2022, 1, 20), False, 132),
    ("Canto villano", "9789972404153", "Blanca Varela", "Poesía", "Peisa", 52.00, 0, 22, 144, date(2019, 5, 16), True, 94),
    ("Ejercicios materiales", "9789972404160", "Blanca Varela", "Poesía", "Peisa", 49.00, 10, 16, 128, date(2021, 8, 9), False, 64),
    ("Los ríos profundos", "9788437600727", "José María Arguedas", "Clásicos Universales", "Peisa", 55.00, 0, 30, 320, date(2018, 9, 25), True, 188),
    ("Todas las sangres", "9789972409882", "José María Arguedas", "Clásicos Universales", "Peisa", 72.00, 10, 15, 512, date(2020, 7, 14), False, 97),
    ("El zorro de arriba y el zorro de abajo", "9789972409899", "José María Arguedas", "Clásicos Universales", "Peisa", 61.00, 0, 4, 344, date(2021, 11, 18), False, 58),
    ("La sociedad del cansancio", "9788425428685", "Byung-Chul Han", "Ensayo y Pensamiento", "Fondo de Cultura Económica", 49.00, 15, 29, 120, date(2022, 3, 10), True, 224),
    ("La agonía del Eros", "9788425432545", "Byung-Chul Han", "Ensayo y Pensamiento", "Fondo de Cultura Económica", 46.00, 0, 3, 104, date(2023, 5, 12), False, 115),
    ("Vida contemplativa", "9788430625352", "Byung-Chul Han", "Ensayo y Pensamiento", "Fondo de Cultura Económica", 58.00, 10, 21, 144, date(2025, 10, 1), False, 102),
    ("El ingeniero pragmático (Edición 20 aniversario)", "9780135957059", "Robert C. Martin", "Negocios y Liderazgo", "O'Reilly Media", 159.00, 10, 14, 352, date(2024, 11, 12), False, 121),
    ("Estrategia digital y cultura de datos", "9788419642998", "Martin Kleppmann", "Negocios y Liderazgo", "Debate", 119.00, 15, 2, 310, date(2026, 2, 14), False, 67),
]


def seed_database() -> None:
    with SessionLocal() as db:
        # 1. Roles
        roles_map: dict[str, Role] = {}
        for role_name, desc in [
            ("customer", "Cliente de la librería digital BOOKLY"),
            ("admin", "Administrador de BOOKLY"),
        ]:
            role = db.scalar(select(Role).where(Role.name == role_name))
            if not role:
                role = Role(id=uuid4(), name=role_name, description=desc)
                db.add(role)
                db.flush()
            roles_map[role_name] = role

        # 2. Categorías
        categories_map: dict[str, Category] = {}
        for name, icon, desc in CATEGORIES_DATA:
            slug = slugify(name)
            cat = db.scalar(select(Category).where(Category.slug == slug))
            if not cat:
                cat = Category(
                    id=uuid4(),
                    name=name,
                    slug=slug,
                    description=desc,
                    icon=icon,
                    is_active=True,
                )
                db.add(cat)
                db.flush()
            categories_map[name] = cat

        # 3. Editoriales
        publishers_map: dict[str, Publisher] = {}
        for name, country, website in PUBLISHERS_DATA:
            slug = slugify(name)
            pub = db.scalar(select(Publisher).where(Publisher.slug == slug))
            if not pub:
                pub = Publisher(
                    id=uuid4(),
                    name=name,
                    slug=slug,
                    country=country,
                    website=website,
                    is_active=True,
                )
                db.add(pub)
                db.flush()
            publishers_map[name] = pub

        # 4. Autores
        authors_map: dict[str, Author] = {}
        for name, nationality, featured, bio in AUTHORS_DATA:
            slug = slugify(name)
            author = db.scalar(select(Author).where(Author.slug == slug))
            if not author:
                author = Author(
                    id=uuid4(),
                    name=name,
                    slug=slug,
                    nationality=nationality,
                    biography=bio,
                    is_featured=featured,
                    is_active=True,
                )
                db.add(author)
                db.flush()
            authors_map[name] = author

        # 5. Libros (42 libros)
        created_books = 0
        for (
            title,
            isbn,
            author_name,
            category_name,
            publisher_name,
            price,
            discount,
            stock,
            pages,
            pub_date,
            is_featured,
            sales_count,
        ) in BOOKS_DATA:
            existing = db.scalar(select(Book).where(Book.isbn == isbn))
            if existing:
                continue

            book_id = uuid4()
            cover = cover_placeholder(isbn, title)
            book = Book(
                id=book_id,
                title=title,
                slug=slugify(f"{title}-{isbn[-4:]}"),
                isbn=isbn,
                synopsis=(
                    f"Edición cuidada de '{title}', obra escrita por {author_name} y publicada por "
                    f"{publisher_name}. Disponible en BOOKLY con envío protegido a todo el Perú."
                ),
                publisher_id=publishers_map[publisher_name].id,
                price=Decimal(str(price)).quantize(Decimal("0.01")),
                discount_percent=Decimal(str(discount)).quantize(Decimal("0.01")),
                stock=stock,
                low_stock_threshold=5,
                pages=pages,
                language="Español" if "O'Reilly" not in publisher_name else "Inglés",
                publication_date=pub_date,
                cover_url=cover,
                is_featured=is_featured,
                is_active=True,
                sales_count=sales_count,
                average_rating=Decimal("4.70") if is_featured else Decimal("4.40"),
                reviews_count=0,
            )
            db.add(book)
            db.flush()

            db.add(
                BookAuthor(
                    book_id=book.id,
                    author_id=authors_map[author_name].id,
                    author_order=1,
                )
            )
            db.add(
                BookCategory(
                    book_id=book.id,
                    category_id=categories_map[category_name].id,
                )
            )
            db.add(
                BookImage(
                    id=uuid4(),
                    book_id=book.id,
                    image_url=cover,
                    alt_text=f"Portada de {title}",
                    display_order=0,
                    is_primary=True,
                )
            )
            db.add(
                InventoryMovement(
                    id=uuid4(),
                    book_id=book.id,
                    movement_type="entrada",
                    quantity_delta=stock,
                    previous_stock=0,
                    new_stock=stock,
                    reason="Carga inicial de inventario BOOKLY",
                )
            )
            created_books += 1

        # 6. Cupones promocionales
        now = datetime.now(timezone.utc)
        coupons_data = [
            (
                "BOOKLY10",
                "10% de descuento en toda la librería",
                "percentage",
                Decimal("10.00"),
                Decimal("50.00"),
                500,
            ),
            (
                "BIENVENIDA15",
                "S/ 15.00 de descuento en tu primera compra mayor a S/ 90.00",
                "fixed",
                Decimal("15.00"),
                Decimal("90.00"),
                300,
            ),
            (
                "LECTURA20",
                "20% de descuento especial en pedidos superiores a S/ 180.00",
                "percentage",
                Decimal("20.00"),
                Decimal("180.00"),
                100,
            ),
        ]
        for code, desc, dtype, val, min_amt, max_uses in coupons_data:
            if not db.scalar(select(Coupon).where(Coupon.code == code)):
                db.add(
                    Coupon(
                        id=uuid4(),
                        code=code,
                        description=desc,
                        discount_type=dtype,
                        discount_value=val,
                        min_order_amount=min_amt,
                        max_uses=max_uses,
                        current_uses=0,
                        starts_at=now - timedelta(days=1),
                        expires_at=now + timedelta(days=365),
                        is_active=True,
                    )
                )

        db.commit()
        print(
            f"[OK] Seed completado: {len(categories_map)} categorías, {len(authors_map)} autores, "
            f"{len(publishers_map)} editoriales y {created_books} libros nuevos registrados."
        )


if __name__ == "__main__":
    seed_database()
