# Handover - Aplicație Ionuț

Stare consemnată la 7 octombrie 2026. Repository: [cosmintrica/aplicatie-ionut](https://github.com/cosmintrica/aplicatie-ionut). Un agent nou nu primește istoricul chatului automat; informațiile necesare continuării sunt în repository. Citește [AGENTS.md](../AGENTS.md) la preluare și verifică sursele, în special dacă au apărut commituri noi.

Ultima livrare de aplicație documentată este [4ad818b](https://github.com/cosmintrica/aplicatie-ionut/commit/4ad818b49059bf8a914e56f9442c4bec0c25bf93), publicată pe `main`: interfață, corelare și alternative de ambalaj. [Verificarea GitHub pe clonă curată](https://github.com/cosmintrica/aplicatie-ionut/actions/runs/37555766904) este încheiată cu succes. Actualizarea prezentului handover completează dovezile livrării; nu schimbă funcțiile aplicației.

## 1. Obiectivul produsului

Firmele mici introduc ce trebuie să cumpere sau o achiziție confirmată. Aplicația compară ofertele disponibile pentru produse compatibile, cantități și condiții explicite; arată costurile, diferențele, sursa și data. Destinația include import de facturi/OCR, istoric, oportunități explicabile și recomandări de furnizori. Taxonomia cuprinde de la început alimente, curățenie, consumabile și electronice. Acoperirea tuturor prețurilor din România nu este o promisiune demonstrată.

Cerințele sunt în [CERERE_INITIALA.md](../CERERE_INITIALA.md) și [CERINTE_EXTINSE.md](CERINTE_EXTINSE.md). Corectitudinea asocierii, o interfață ușor de înțeles și dovezile pentru recomandări sunt cerințe de bază.

## 2. Ce există efectiv

| Arie | Stare în cod |
|---|---|
| Runtime | React/TypeScript/Vite, API FastAPI, SQLite; acces local pe loopback |
| Date | Import offline Monitor/Lidl din probele salvate la 5 octombrie 2026, manifest cu 11 fișiere și SHA-256 |
| Catalog | Căutare, categorii, prețuri raportate și filtre înainte de paginare; 107.226 înregistrări cu nume, dintre care 2.448 cu preț la baseline |
| Liste | Liste persistente, cantități, text liber, schimbarea produsului cu păstrarea cerinței inițiale, filtru pentru poziții fără produs/preț, scenariu și redenumire |
| Comparații | Atribute și motive, variante separate, alternative de ambalaj cu preț/kg/l, matrice produs-magazin, coșuri complete detaliate și export CSV; incomplet separat |
| Zone | Slatina 5 km și București 1 km, plus lista națională Lidl distinctă; fără extindere geografică implicită |
| Protecție locală | Host/origin loopback, sesiune și CSRF; aceasta nu este autentificare pentru mai multe firme |
| Livrare | Cod public, lockuri, scripturi Windows, teste, documente și capturi; GitHub Actions fără deploy |

E0/E1a sunt livrate ca versiune locală utilă, cu [revizia UI/corelare din 7 octombrie](REVIZIE_UX_CORELARE.md). Aceasta adaugă alternative pe kg/l, schimbarea produsului ales, detalierea coșului, export CSV și gardele pentru utilizare/variantă/formă. Motorul curent are `algorithm_version=attributes-and-unit-prices-3`. Aceasta nu certifică toate țintele viitoare de matching, performanță, accesibilitate sau producție. Codul și [SMART_CONTRACT.md](../backend/SMART_CONTRACT.md) descriu capabilitățile existente: „Aceleași caracteristici” este candidat pe atribute, nu identitate GTIN confirmată. `payable_total`, `savings` și `estimated_savings` nu se completează din estimările actuale.

Nu sunt implementate: achiziții confirmate, import manual/CSV/UBL/PDF, OCR, economie realizată, recomandări ferme pe istoric, colectare continuă, login/OIDC, membership pentru mai multe firme, emailuri și producție. Nicio integrare Supabase sau Compari.ro nu este configurată prin publicarea codului. Investigația Compari documentează feeduri și identificatori, nu oferă acces la catalogul lor.

### Puncte de intrare pentru continuare

| Ce modifici | Fișiere de pornire |
|---|---|
| Extracție, verdict, ambalaje și preț pe unitate | [smart.py](../backend/app/smart.py), [regresii de corelare](../backend/tests/test_matching_improvements.py) |
| Catalog, oferte, comparații și proveniență | [repository.py](../backend/app/repository.py), [contractul API](../backend/SMART_CONTRACT.md) |
| Lista, cantitățile și schimbarea produsului | [App.tsx](../web/src/App.tsx), [Shopping.tsx](../web/src/Shopping.tsx) |
| Explorarea produsului și alternativele sale | [Catalog.tsx](../web/src/Catalog.tsx), [Details.tsx](../web/src/Details.tsx), [ProductFacts.tsx](../web/src/ProductFacts.tsx) |
| Matrice, conținutul coșului și CSV | [Comparison.tsx](../web/src/Comparison.tsx), [tipurile frontend](../web/src/api.ts) |
| Aspect desktop/mobil | [styles.css](../web/src/styles.css), [workspace.css](../web/src/workspace.css), [comparison.css](../web/src/comparison.css) |

La următoarele schimbări păstrează distincția dintre `description` (cerința inițială), `source_product_name` și `reference_profile` (produsul evaluat). `pack_alternatives` nu se introduc automat în coș; `unit_price.label` se calculează în backend. Matricea folosește `comparable_options` pentru eligibilitate, inclusiv la cantități fracționare, iar ofertele naționale Lidl fără magazin rămân separate de magazinele geografice. Anularea cererilor depășite și blocarea comparației pentru cantități nesalvate sunt comportamente verificate, nu detalii de eliminat la refactorizare.

## 3. Lectură și autoritate

1. [AGENTS.md](../AGENTS.md), acest handover și [README.md](../README.md): stare, convenții, pornire și următorul pas.
2. [PLAN_IMPLEMENTARE.md](PLAN_IMPLEMENTARE.md): etape, dependențe, backlog și criterii. E1b este următoarea etapă recomandată.
3. Pentru comportamentul existent: `backend/app`, migrațiile SQL, `web/src`, teste și [SMART_CONTRACT.md](../backend/SMART_CONTRACT.md). API-ul folosește `/api/v1`; sănătatea este la `/api/v1/health`.
4. Pentru funcția care urmează: secțiunile relevante din [SPECIFICATIE_PRODUS.md](SPECIFICATIE_PRODUS.md), [MOTOR_CORECTITUDINE.md](MOTOR_CORECTITUDINE.md) și [DECIZII_ARHITECTURA.md](DECIZII_ARHITECTURA.md). Sunt documente de proiectare, inclusiv structură și comenzi propuse istoric.
5. Pentru conturi/emailuri E4/E5: [ACCES_SI_EMAIL.md](ACCES_SI_EMAIL.md). Pentru dovezi/limite: [REVIZIE_COMPARATII.md](REVIZIE_COMPARATII.md), [VALIDARE_IDENTITATE_DATE.md](VALIDARE_IDENTITATE_DATE.md) și [RAPORT_TESTARE.md](../RAPORT_TESTARE.md).

Instrucțiunile curente ale utilizatorului și dovezile reale au prioritate. O diferență între designul viitor și cod nu justifică ștergerea funcției existente. Înregistrează și rezolvă neconcordanța în etapa relevantă.

## 4. Pornire dintr-o clonă nouă

Mediul verificat: Windows, PowerShell 7, Python 3.12+ și Node.js 22.12+ (22.18 verificat). Folosește `pwsh`, nu presupune că terminalul implicit are PowerShell 7. Instalarea inițială descarcă dependențe; funcționarea cu snapshoturile după setup este offline. Nu sunt necesare chei AI, conturi cloud sau fișiere locale de la autor.

```powershell
$ErrorActionPreference = 'Stop'
git clone https://github.com/cosmintrica/aplicatie-ionut.git
if ($LASTEXITCODE -ne 0) { throw 'Clone failed.' }
Set-Location aplicatie-ionut
.\scripts\Setup-Local.ps1
.\scripts\Check-Local.ps1
.\scripts\Start-Local.ps1
```

Scripturile opresc operațiile dependente la eroare. Dacă executabilele nu sunt în PATH, `Setup-Local.ps1` acceptă `-PythonPath` și `-NodePath`. Deschide `http://127.0.0.1:8000`. Dacă portul este ocupat, identifică instanța existentă; nu opri un proces fără să verifici cui aparține.

Pentru un checkout existent, inspectează întâi `git status`; cu arbore curat, `git pull --ff-only` aduce actualizările. Nu reseta sau suprascrie modificările locale pentru un pull. După schimbări de dependențe, migrații sau frontend, repetă setupul și verificările necesare.

`.venv` este în rădăcină. CLI-ul actual acceptă numai `seed` și `check`, iar ambele execută importul. `migrate` și `import-snapshots` nu există. `web/package.json` are `dev`, `typecheck`, `build`, `preview`; nu are în prezent `test` sau `test:e2e`. Nu declara Vitest/Playwright instalate sau executate doar fiindcă apar în proiectare.

Configurația actuală folosește `APP_MODE=local`, implicit, și opțional `APP_DB_PATH`; alte moduri sunt refuzate. Baza implicită este `var/app.sqlite3`. `APP_MODE=offline`, `OCR_PROVIDER` și `LIVE_SOURCES_ENABLED`, descrise istoric în arhitectură, nu sunt configurații funcționale ale acestei versiuni.

## 5. Verificări și baseline

Baseline curent, pentru commitul `4ad818b`: 112 teste Python (37 regresii noi de corelare), 32 verificări PowerShell și build TypeScript/Vite trecute local. [GitHub Actions](https://github.com/cosmintrica/aplicatie-ionut/actions/runs/37555766904) a confirmat și instalarea dependențelor fixate, importul probelor și verificările pe un checkout nou. Există un avertisment Starlette/TestClient privind httpx, fără eșecuri. Baseline-ul anterior de 75 teste Python, din 6 octombrie, rămâne [istoric](https://github.com/cosmintrica/aplicatie-ionut/actions/runs/37392153976).

Testarea browser a folosit Chromium/Playwright din runtime-ul agentului, cu bază izolată: layout la 320/390 px, persistență, cantități nesalvate și fracționare, substituție 250 g cu 500 g, răspunsuri întârziate, dovezi, focus și CSV. Nu există încă o suită browser instalată în repository; pentru reproducere urmează scenariile din [REVIZIE_UX_CORELARE.md](REVIZIE_UX_CORELARE.md). Raportul consemnează și problema locală de permisiuni pytest, rezolvată prin directoare temporare noi, fără schimbarea codului.

`scripts/Check-Local.ps1` rulează parserul, testele backend/regresii și buildul. Setupul trebuie să existe, iar Node/npm să fie în PATH. Pentru documentație, verifică linkurile, comenzile și consistența; baseline-ul de mai sus este o execuție istorică, nu o afirmație că fiecare checkout a fost testat deja.

Parcurs browser pentru o schimbare de aplicație: găsește un produs cu preț, adaugă-l într-o listă, schimbă cantitatea, compară și deschide dovada; verifică persistarea după reload, variantele incompatibile, coșul incomplet și zona selectată. Verifică 320/390 px și tastatura. Folosește o listă de test separată; nu șterge datele existente. [Raportul UI](IMPLEMENTARE_COMPARATII.md) păstrează verificările și capturile anterioare.

## 6. Date și publicare

- Clona publică funcționează cu probele și manifestul incluse; nu cere snapshoturile originale ale autorului sau baza sa locală.
- La prima publicare au fost normalizate exclusiv șase căi locale din două JSON-uri derivate. Prețurile au rămas aceleași; XML/XLSB sunt intacte. Manifestul public conține hashurile reale și hashurile originale ale fișierelor normalizate. Vezi [PUBLICARE.md](PUBLICARE.md).
- Numai checkoutul inițial al autorului păstrează originalele și are trei diferențe față de commit: `probe-data/lidl-parsed-2026-10-05.json`, `probe-data/summary.json`, `fixtures/snapshot-manifest.json`. Nu sunt modificări de prețuri; nu le curăța prin reset și nu le publica prin `git add -A` din acel arbore. Pe o clonă normală aceste diferențe nu există.
- `scripts/prepare-publication.py` pregătește o copie nouă în `tmp`; nu publică și nu modifică originalele. Datele de lucru, facturile reale, listele firmei și secretele rămân locale. Repository public nu înseamnă aplicație găzduită online.
- `scripts/Test-MonitorPrices.ps1`, inclusiv cu `-Offline`, nu este verificare fără efecte. Păstrează baseline-ul; colectările noi folosesc locație și manifest proprii.

La încheierea reviziei din 7 octombrie, aplicația a fost repornită pe baza implicită `var/app.sqlite3`. Amprenta conținutului tabelelor `company`, `shopping_list` și `list_line` a fost identică înainte și după repornire. Bazele și listele de test au rămas în `tmp`, excluse din publicare. Un coleg care clonează primește sursele și probele publice, nu listele firmei autorului.

## 7. Următorul livrabil: E1b, achiziție manuală confirmată

Aceasta este prioritatea recomandată dacă utilizatorul nu cere altceva. Scope inițial: achiziție în RON, introducere manuală, draft, validare, revizie și confirmare cu proveniență. Completează fluxul vertical înaintea tuturor importurilor.

1. Verifică baseline-ul și modelul existent. Definește contractele E1b pentru furnizor, document/data, cantități/unități, preț/bază, reduceri, TVA, taxe/transport și total. Necunoscutele rămân explicite. Extinde costul conform B08; nu transforma raportarea existentă în cost final.
2. Adaugă migrații și API-uri compatibile, păstrând listele și snapshoturile. Separă extras/introdus, confirmat și revizie; o corecție invalidează analiza veche. Nu introduce un ORM sau o platformă nouă pentru această etapă.
3. Construiește formularul și revizia cu sumar clar, erori pe câmp, salvare și confirmare. Facturi reale nu sunt în repository; exemplele de test sunt sintetice și etichetate.
4. Demonstrează round-trip-ul sumelor, draft/confirmat, lipsa identității/bazei, corectarea și prevenirea duplicării. Nu atribui economii unei linii draft ori unei potriviri neverificate.
5. După fluxul manual, adaugă CSV cu preview/mapare/erori, apoi UBL 2.1, urmând B09-B11. Toate intrările ajung la același model confirmat. E1b se acceptă prin G1b și D2 din plan, nu doar printr-un formular.
6. Actualizează contractele, testele, README și acest handover. Raportează precis ce parte E1b este gata și ce lipsește; nu marca G1b trecut înaintea tuturor probelor cerute.

Mai departe: E2 pentru adaptoare controlate/PDF text și recomandări demonstrabile; E3 pentru OCR real și corpus evaluat; E4 pentru PostgreSQL/OIDC, roluri, izolare, emailuri și operare; E5 pentru surse/categorii și alerte extinse. Planul descrie dependențele și gates. Providerii de identitate/email/OCR, regiunea de hosting și acordurile de feed nu sunt alese sau obținute implicit.

## 8. Prompt de început pentru alt agent

Poți copia textul în noua sesiune și adapta obiectivul:

> Preia acest checkout al aplicației Ionuț. Citește AGENTS.md, docs/HANDOVER.md și README.md, apoi secțiunile E1b relevante ale planului și contractele actuale. Verifică sursele și baseline-ul; păstrează datele și modificările locale. Continuă E1b cu un flux complet de achiziție manuală draft/revizie/confirmare în RON, cu validări și proveniență, înaintea CSV/UBL. Respectă regulile pentru identitate, bani, necunoscute și snapshoturi. Folosește stiva existentă; actualizează documentația și execută verificările relevante. Raportează implementat, verificat, rămas și orice decizie care necesită informații de la mine.
