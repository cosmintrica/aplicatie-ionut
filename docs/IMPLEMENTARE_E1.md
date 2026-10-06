# Implementarea locală E0 + E1a

Acesta este raportul primei livrări, păstrat ca istoric. Revizia ulterioară a interfeței și motorului este descrisă în [REVIZIE_COMPARATII.md](REVIZIE_COMPARATII.md) și [contractul actual](../backend/SMART_CONTRACT.md); ea adaugă corespondențe pe atribute, diferențe între prețuri și estimări pentru coșuri complete.

**5 octombrie 2026.** Planul GPT-6 Astra, efort `ultra`, este în [PLAN_IMPLEMENTARE.md](PLAN_IMPLEMENTARE.md). Această livrare pune în funcțiune fundația și primul flux local; celelalte etape rămân definite în plan.

## Comportament disponibil

- Catalog căutabil și paginat: 104.794 înregistrări Monitor și 2.444 rânduri Lidl, păstrate separat. Cele 12 denumiri goale Monitor rămân în baza importată, dar sunt excluse din căutare.
- Taxonomie extensibilă: 54 categorii și mapare provizorie pentru toate cele 34 categorii explicite Lidl. Categoria OTC rămâne de verificat. Catalogul Monitor fără dovezi de clasificare rămâne căutabil la „De clasificat”.
- Profil local, liste multiple, articole din catalog și cerințe introduse ca text, cantități, eliminare/restaurare și salvare în SQLite.
- Scenariile probate Slatina - 5 km și București - 1 km, cu cotații pe magazin, lipsuri și proveniență. Lista Lidl la nivel de rețea este prezentată separat.
- Comparație pe cotațiile sursei: acoperirea cotațiilor, identitatea confirmată și cantitățile calculabile sunt câmpuri distincte. Costul plătibil și economiile sunt necunoscute în această etapă.
- Dovezi care păstrează fișierul, hashul, locatorul, ID-urile, numele contextual al catalogului și numele comercial. Varianta Jacobs Intense contrazice declarația Alintaroma din observația sursei; codul comun nu anulează conflictul.

Pentru cantități diferite de un articol, aplicația nu multiplică prețurile cu bază neconfirmată. Suma neajustată rămâne identificată separat. Nici o cotație zero sau lipsă nu devine gratuitate, nici un coș parțial nu devine achiziție completă.

## Pornire și date

Comenzile sunt în [README](../README.md). Interfața React/TypeScript este servită de API-ul FastAPI pe `127.0.0.1:8000`; datele private sunt în `var/app.sqlite3`. Dependențele sunt locale și fixate prin lockuri.

Importul verifică manifestul celor 11 fișiere originale, rulează atomic și poate fi repetat fără duplicarea datelor sau ștergerea listelor. Clasificarea provizorie Lidl are versiune derivată din taxonomie, pentru actualizarea sigură a mapărilor în baza deja creată. Startup-ul nu colectează date de la furnizori.

Accesul este limitat la loopback, cu validarea Host/Origin, sesiune locală și CSRF pentru modificări. Modul acesta nu reprezintă autentificare pentru găzduire publică sau mai multe firme. Fișierele originale și baza de date nu sunt montate ca resurse web.

## Verificări

- 54 teste Python pentru domeniu, API și probe reale: cantități zecimale, coșuri incomplete, incompatibilități, revizii, import idempotent, persistență după restart, sesiune și CSRF. Include asocierea unei cerințe libere la un produs pe aceeași linie, fără pierderea descrierii originale.
- 32 verificări ale parserului Monitor, offline.
- Hashurile celor 11 probe originale și linkurile locale din documentația livrată verificate.
- `pip check`: fără dependențe incompatibile.
- TypeScript și buildul Vite trecute prin `scripts/Check-Local.ps1`; bundle JS 289,41 kB / 87,74 kB gzip.
- Flux real în browser: crearea listei exemplu, comparația 15 magazine cu toate cotațiile / 3 parțiale, dovada contextuală Jacobs, modificarea cantității și abținerea calculului, persistență după repornirea serverului, asociere pe aceeași linie și reload, filtre de categorie/subcategorie și stări fără oferte.
- Desktop și viewporturi de 390 px / 320 px verificate. La 320 px, clientWidth și scrollWidth sunt ambele 305 px (restul este scrollbarul vertical), deci nu există overflow lateral; la 390 px sunt ambele 375 px. Problemele observate au fost corectate și reverificate. Consola browserului nu a raportat erori sau avertismente în verificarea finală.

[Captură desktop](images/initial-desktop.jpg). Browserul a fost readus la dimensiunea implicită după testarea mobilă.

TestClient emite un avertisment de depreciere Starlette/httpx; verificările trec. Rezultatele testelor nu demonstrează precizia unui motor general de asociere sau acoperirea națională a ofertelor. [Evidența datelor](EVIDENTA_DATE_E1.md) detaliază aceste limite.

## Etape următoare

E1b adaugă achizițiile confirmate și importurile manual/CSV/UBL. Citirea PDF, OCR-ul fotografiilor și recomandările de furnizori au propriile etape și criterii de validare. Interfața indică indisponibilitatea lor; nu simulează scanări sau economii. Extinderea la electronice necesită surse și identificatori precum EAN/MPN, configurație și compatibilitate, conform [cercetării Compari](CERCETARE_COMPARI.md) și [motorului de corectitudine](MOTOR_CORECTITUDINE.md).
