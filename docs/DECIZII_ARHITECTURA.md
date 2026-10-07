# Decizii de arhitectură - Preturi achizitii

Proiectare inițială din 5 octombrie 2026, completată la 6 octombrie pentru conturi și emailuri. Deciziile acoperă și etape viitoare; [README](../README.md) descrie implementarea disponibilă. Documentele normative complementare sunt [planul](PLAN_IMPLEMENTARE.md), [specificația](SPECIFICATIE_PRODUS.md) și [regulile de corectitudine](MOTOR_CORECTITUDINE.md). Deciziile de mai jos sunt ale proiectului, nu descrieri ale arhitecturii Compari.ro.

**Preluare la 7 octombrie 2026:** aplicația locală și dependențele fixate există deja. Arborele propus, uneltele de test și setările de mai jos includ destinații viitoare. Pentru configurația actuală, rutele și comenzile existente, urmează [HANDOVER.md](HANDOVER.md), sursele și [contractul motorului](../backend/SMART_CONTRACT.md). De exemplu, modul actual este `APP_MODE=local`, sănătatea este la `/api/v1/health`, iar Vitest/Playwright nu sunt încă instalate; nu copia setările istorice ca bootstrap nou.

## 1. Decizia de bază și granițele sistemului

Construim un monolit modular, cu **React + TypeScript + Vite** pentru interfață și **Python 3.12 + FastAPI/Pydantic + SQLite** pentru API, date și calcule. Python execută parsarea, potrivirea și aritmetica cu `Decimal`; browserul afișează rezultate și trimite intențiile utilizatorului. Nici prețurile, nici verdictul unei potriviri nu sunt calculate independent în JavaScript. Fișierele originale rămân separat de baza de date. Nu sunt necesare conturi cloud, Docker, Redis, servicii vectoriale, un model generativ sau credențiale pentru prima etapă.

| Componentă | Alegere inițială | Motiv și limită |
|---|---|---|
| Web | React, TypeScript strict, Vite, React Router, CSS cu variabile | Interfață mobilă interactivă; fără nevoie inițială de SEO/SSR. Nu impunem Next.js sau o platformă de hosting. |
| Formulare/API client | Formulare controlate pe fluxuri; client `fetch` tipat din schema API | Mai puține dependențe; o singură politică de erori, anulare și sesiune. State management global numai pentru firmă, sesiune și lista curentă. |
| API | FastAPI, Pydantic, Uvicorn | Contracte validate și OpenAPI. Logica de domeniu nu importă FastAPI. |
| Persistență | `sqlite3` din Python; SQL parametrizat, migrații SQL numerotate | Funcționează într-un fișier local; fără ORM și fără server DB separat. Repository-uri pe domenii, fără framework generic de persistence. |
| Parsare | XML protejat (`defusedxml`), CSV stdlib, JSON cu zecimale exacte | Adaptoare mici, teste cu probele existente. Parserul XLSB existent rămâne instrument de probă; în E1 importăm JSON-ul său salvat. |
| Căutare | Tabel de căutare normalizată + SQLite FTS5, filtre indexate | Suficient pentru catalogul de 104.794 rânduri; căutarea nu confirmă identitatea. Dacă buildul SQLite nu are FTS5, se verifică la setup și se folosește un index de prefix până la remediere. |
| Lucrări lente | CLI sincron la început; tabel `job` și un worker Python în E2/E3 | Importuri/OCR reluabile fără a ține requestul HTTP deschis. Redis/Celery nu sunt necesare pentru pilot. |
| Fișiere | Director privat `var/files`, metadate în DB | Niciun original în `web/public`, URL static sau Git. |
| Teste | pytest + Hypothesis pentru domeniu; Vitest/Testing Library; Playwright pentru fluxuri | Teste aritmetice și de izolare, apoi parcursuri reale de utilizator. |
| Producție E4 | Același API/web, PostgreSQL, stocare obiecte privată, OIDC configurat | Decizie de destinație, fără selectarea sau contractarea acum a unui furnizor. Migrarea și autentificarea sunt condiții ale lansării multi-firmă. |

FastAPI documentează servirea prin Uvicorn; [documentație oficială](https://fastapi.tiangolo.com/deployment/manually/). Modulul Python `sqlite3` oferă stocare fără server separat; [documentație](https://docs.python.org/3/library/sqlite3.html). SQLite admite un singur writer simultan; importurile folosesc tranzacții scurte și un singur worker, iar accesul concurent de producție trece pe PostgreSQL, [limita documentată](https://www.sqlite.org/whentouse.html).

Mediu verificat în acest chat: Node **22.18.0**, npm **10.9.3**, PowerShell **7.6.6**; Python **3.12.14**, SQLite **3.53.1** în runtime-ul desktop disponibil. Vite cere actualmente Node 20.19+ sau 22.12+; versiunea găsită satisface această condiție, [ghid oficial](https://vite.dev/guide/). Nu rezultă că toate dependențele sunt instalate: FastAPI, Uvicorn și pytest nu sunt disponibile în runtime-ul verificat. Implementarea creează un `venv` al proiectului și manifestele/lockfile-urile, fără a modifica runtime-ul Codex. Descărcarea pachetelor poate necesita rețea; funcționarea E1 după instalare nu necesită rețea. Nu fixăm numere de versiune neverificate în acest plan: la bootstrap se aleg versiuni stabile compatibile, se fixează în lockfile și se înregistrează rezultatul instalării.

## 2. Organizare implementabilă

Arbore propus; numele de mai jos nu desemnează fișiere deja implementate:

```text
backend/
  pyproject.toml, requirements.lock
  app/
    main.py, settings.py, cli.py
    api/                 # catalog, comparisons, purchases, imports, sources
    domain/              # money, units, matching, baskets, savings, evidence
    services/            # cazuri de utilizare și tranzacții
    repositories/        # SQL, întotdeauna cu scope explicit
    adapters/            # monitor_snapshot, lidl_snapshot, csv, ubl, apoi OCR/live
    schemas/             # contracte API și scheme de categorii
  migrations/
  tests/
web/
  package.json, package-lock.json
  src/
    app/                 # rute, layout, sesiune
    features/            # list, catalog, compare, invoices, savings, suppliers
    components/          # primitive vizuale și componente de domeniu
    api/, styles/
  tests/
config/                  # taxonomie și reguli versionate, fără secrete
fixtures/                # manifeste probe, adjudecări, exemple sintetice etichetate
var/                     # DB, fișiere private, cache, loguri; exclus din Git
docs/                    # aceste documente și evidența verificărilor
probe-data/, scripts/, tests/  # probele originale, păstrate
```

Manageri: `npm` în `web`; `venv` + `pip` în `backend`. Un `requirements.lock` cu dependențe tranzitive fixate și, ideal, hashuri este generat la bootstrap; `npm ci` folosește `package-lock.json`. Nu refolosim implicit librării din cache-ul aplicației desktop ca dependențe ale produsului. Configurația minimă: `APP_MODE=offline`, `DATA_DIR`, bind la `127.0.0.1`, `OCR_PROVIDER=none`; `LIVE_SOURCES_ENABLED=false`. Nu se adaugă setări fără consumator concret.

În dezvoltare Vite face proxy la API; buildul web este servit de FastAPI pentru o singură origine. Interfața nu face requesturi la magazine. Ruta `/api/health` afișează versiunea aplicației și modul, fără căi private sau secrete. Buildul E1 nu activează service worker; evităm cache-ul persistent de facturi și confuzia între prețuri salvate și prețuri actuale.

## 3. Model de date și identitate

### Convenții comune

- ID-uri interne UUID, ID-uri externe stocate ca text, fără conversie la număr. GTIN păstrează zerourile inițiale.
- Timp: UTC ISO 8601 și redare `Europe/Bucharest`; `source_time_raw`, fus orar și calitatea interpretării se păstrează. Pentru data Monitorului fără offset, fusul București este o ipoteză de adaptor etichetată. Data unei facturi este `date`, nu miezul nopții convertit arbitrar.
- Bani: sume de document finale în bani întregi (RON), prețuri unitare/cantități în șiruri zecimale canonice, calculate cu `Decimal`. Fără `REAL`, `float`, `parseFloat` sau sumare SQL pe text. Schema API folosește șiruri pentru bani; `null` înseamnă necunoscut, niciodată zero implicit. [Decimal și rotunjire](https://docs.python.org/3/library/decimal.html).
- `currency` obligatoriu; E1 calculează numai RON. Alte monede se păstrează, dar comparația este blocată până la un curs datat și o politică explicită.
- `visibility_scope=public|tenant`; toate înregistrările private au `tenant_id`. Relațiile dintre două entități private verifică și firma, nu numai UUID-ul.
- Orice câmp decisiv are `value`, `state=observed|derived|user_confirmed|unknown|conflicting`, `evidence_ref`, versiune și autor. Nu construim o platformă generică de ontologii: coloane pentru câmpuri comune, JSON tipat și versionat pentru atribute de categorie/condiții.

### Catalog, comercianți și dovezi

| Entitate | Câmpuri esențiale și relații | Reguli |
|---|---|---|
| `category` | `id`, `parent_id`, `code`, nume, `schema_version`, `attributes_schema`, `active_for_comparison` | Cod stabil; schimbarea schemei nu rescrie deciziile istorice. Categoriile neacoperite pot primi achiziții fără oferte. |
| `brand` / `brand_alias` | marcă canonică; alias, limbă, sursă, stare, evidență | Aliasul aprobat nu echivalează mărci private diferite. Aliasurile ambigue nu sunt unice global și nu se aplică automat. |
| `canonical_product` | `id`, categorie, marcă, familie/nume canonic | Grupare de navigare, nu nivel suficient pentru comparație. |
| `product_variant` | produs, `attributes_json`, schemă, fingerprint, statut | Varianta conține concentrație/formă/model/configurație. Orice conflict decisiv blochează potrivirea. |
| `trade_item` | variantă, `pack_count`, `content_per_unit`, unitate, conținut total, `pack_type`, stare | Ambalajul comercial: 1×250 g și 1×500 g sunt articole comerciale diferite. Lipsa gramajului nu devine 1 bucată. |
| `identifier` | `trade_item_id` sau variantă, `scheme=GTIN|MPN`, valoare, issuer, evidență | MPN este în scope de producător; GTIN în conflict merge în revizie, nu în constrângere care ascunde conflictul. |
| `supplier` / `store` | rețea/furnizor; punct de vânzare, ID extern, adresă, coordonate | Magazinul este separat de rețea. Numele similare nu unesc automat entitățile. Furnizorii din facturi pot fi privați firmei. |
| `source` | tip, pagină, parser, mod, drepturi/condiții cunoscute, acoperire, politică de prospețime, enabled | Stare acces/republicare `unverified|approved|restricted`; nu confundăm accesul HTTP cu permisiunea de lansare. |
| `source_snapshot` | sursă, SHA-256, cale, URL/parametri, request/time/status dacă există, captură, `mode`, versiune parser | Conținut imuabil. Datele lipsă în `requests.json` rămân lipsă; nu reconstruim un timestamp precis din numele fișierului. |
| `source_record` | snapshot, locator rând/XML, payload original, hash, rezultat parsare și motive | Permite refacerea și auditul unei observații; recordurile respinse nu dispar. |
| `source_product` | sursă, retailer, magazin/scope, SKU extern dacă există, ID catalog sursă separat, text/unitate brute | Monitor: `Catprod.Id` pentru căutare; `Product.Id` pentru produs retailer, păstrat în scope de magazin până se demonstrează stabilitatea/unicitatea mai largă. Nu considerăm `Catprod.Id` identitate canonică verificată. |
| `match_decision` | record/produs sursă, țintă, relație, status, features/scor, reguli, evidence, autor, `supersedes_id`, scope | Confirmările utilizatorului sunt private implicit. O decizie respinsă nu este ștearsă la o rerulare. |

Un produs din sursă poate avea versiuni de descriere și observații diferite. Maparea validată se leagă de semnătura atributelor; schimbarea lor invalidează reutilizarea confirmării. Pentru Lidl, care nu furnizează SKU, cheia unui rând este `(snapshot, sheet, row)`, iar fingerprintul nume+gramaj+categorie este doar candidat pentru continuitate. Cele opt duplicate nu se deduplică prin alegerea automată a minimului.

### Oferte și calcul

| Entitate | Câmpuri esențiale și relații | Reguli |
|---|---|---|
| `offer` | produs sursă, furnizor/magazin sau rețea, scope geografic, canal, `tenant_id?`, monedă | Oferta nu presupune un `trade_item` confirmat. O ofertă negociată nu intră în catalogul public. |
| `offer_observation` | ofertă, record, preț raw/decimal, bază preț, TVA/bază fiscală, SGR/aplicabilitate/includere, stoc, `source_priced_at`, `retrieved_at`, interval valabil, condiții versionate | Append-only. Zero sau dată invalidă în Monitor înregistrează observație neutilizabilă, nu preț gratuit. `retrieved_at` nu întinerește prețul. |
| `offer_terms` | JSON tipat: min/step/max cantitate, trepte de preț, card/cupon/eligibilitate, livrare, comandă minimă, facturare B2B, condiție produs, garanție | Inițial JSON pe observație; tabel separat numai când reguli comune sunt reutilizate. Condițiile necunoscute sunt câmpuri explicite. |
| `shopping_list` / `shopping_line` | firmă, revizie, zonă, mod fiscal; variantă/articol sau text liber, cantitate/unitate, constrângeri, alternative acceptate | Cererea se păstrează separat de articolul ales. Acceptarea unui echivalent este per linie/listă, revocabilă. |
| `comparison_run` | firmă, revizie listă, context de referință, mod snapshot/current, `as_of`, versiuni, input/output JSON imuabil, observation IDs | Rezultat reproductibil; conține toate lipsurile și exact domeniul căutat. Nu păstrează doar un total. |
| `recommendation` (E2+) | run, bază de referință, motive și costuri, expirare, stare, feedback | Derivată din calcule, nu din textul unui LLM. Revizuirea datelor invalidează recomandarea. |

Fiecare rezultat are separat: `quote_coverage`, `semantic_coverage`, `quantity_coverage`, `cost_completeness`, `freshness`, `eligibility`, `availability_status`. Un `is_complete` global ascunde prea multe și nu este suficient. Pentru produsele cu condiție/garanție diferită, identitatea hardware poate coincide, dar comparația comercială rămâne separată și avertizată.

**Selecția observației curente:** se ia cea mai nouă observație a aceleiași oferte și aceluiași scope, apoi se validează. Nu se caută „cea mai nouă valoare pozitivă” ignorând un răspuns ulterior cu lipsă de cotație. Lipsa într-un feed complet publicat poate retrage oferta; lipsa dintr-un răspuns geografic/parțial nu demonstrează indisponibilitatea globală. În ambele situații păstrăm istoricul fără a-l afișa drept actual.

### Firmă, facturi și control

| Entitate | Câmpuri esențiale și relații | Reguli |
|---|---|---|
| `tenant` | firmă, preferințe, fus, bază de comparație, retenție | E1 are firmă locală de lucru; modelul este pregătit pentru mai multe firme. Nu cerem CUI dacă nu este necesar funcției. |
| `user` / `membership` (E4) | identitate OIDC, tenant, rol `owner|editor|viewer` | Rolul din DB, nu din payload. Viewer nu confirmă/importă/exportă documente sensibile implicit. |
| `document` | tenant, SHA-256, MIME, bytes, cale privată, stare scanare, sursă, retenție | Hash și detector de duplicat per firmă; nu dezvăluim existența documentului altui client. |
| `extraction_run` / `extracted_field` | document, parser/OCR/version, text, pagină/bbox sau XPath/rând, valoare propusă, confidence raw și tip | Textul și confidence furnizorului nu sunt date confirmate. Nu inventăm bounding boxes pentru extractoare care nu le oferă. |
| `invoice` / `invoice_line` | tenant, document, furnizor, număr, dată, tip, monedă, totaluri, revizie/stare; linii cu descriere, cantitate, unitate, preț, reduceri, TVA, depozit, tip linie | Sumele din factură și sumele recalculate rămân distincte. Retur/credit/serviciu/depozit nu devin produse noi. |
| `field_confirmation` | câmp extras, valoare confirmată, autor, moment, motiv, versiune | Corectură append-only; înregistrarea istorică confirmată are revizie, nu este rescrisă de rerularea OCR. |
| `purchase_baseline` | linii confirmate, cantități/bază cost, perioadă, alocare costuri | Reprezintă comparația efectuată. Factura confirmă achiziția raportată, nu dovada plății bancare. |
| `audit_event` / `job` | tenant/actor/acțiune/ID/version; job tip/stare/retry/lease/error | Logul de audit nu include text integral de factură ori secrete. Joburile sunt autorizate cu scope de firmă și la execuție. |

Nu construim fiecare tabel anticipativ: `user/membership`, `recommendation`, workerul și administrarea surselor se adaugă în etapele care le folosesc. În E1 sunt suficiente schema catalogului, ofertele, firmele locale, listele, comparațiile și achizițiile confirmate; extragerile necesare importului structurat folosesc aceeași trasabilitate ca viitorul OCR.

### Constrângeri și indici

- `PRAGMA foreign_keys=ON` pe fiecare conexiune; WAL și `busy_timeout` limitat; tranzacții explicite și rollback la import eșuat. Verificare integritate/migrare înainte de pornire.
- Unique `(source_id, sha256, query_scope)` pentru conținutul importat idempotent; `(snapshot_id, locator)` pentru record. În E2 fiecare cerere reală are un `fetch_id` distinct în jurnalul jobului, cu propriul status și `retrieved_at`, chiar dacă răspunsul are același hash. Observația se leagă de acest eveniment; reexecutarea parsării pentru același eveniment și aceeași versiune nu o multiplică. O nouă colectare poate confirma aceeași valoare, dar nu rescrie data comercială a prețului. Coliziunea cu conținut diferit este conflict, nu overwrite.
- Indici: produse pe categorie/marcă; identificatori pe `(scheme, issuer, value)`; observations pe `(offer_id, source_priced_at, retrieved_at)`; facturi pe `(tenant_id, date)`; linii și fișiere pe `(tenant_id, id)`.
- Relațiile private folosesc FK compus `(tenant_id, parent_id)` cu index unic corespunzător. Interdicție a referințelor cross-tenant în repository și teste negative în API.
- Versiunile schemei/rulelor și evenimentele care invalidează cache se actualizează în aceeași tranzacție. Editările UI au `expected_revision`; conflictul returnează 409 cu reîncărcare/îmbinare explicită.
- Un total pozitiv nu este constrângere universală pentru facturi: note de credit, linii negative și retururi au tip explicit și reguli proprii.

## 4. Contracte API esențiale

Prefix `/api/v1`; validare strictă la intrare; paginare cursor, maximum 50 rezultate implicit și 100 maxim. Erori în formă `{code, message, field_errors, request_id, retryable}` fără stack trace. Firma este rezolvată din sesiune și membership; un `tenant_id` trimis de client nu conferă acces.

| Operație | Rezultat/condiție |
|---|---|
| `GET /capabilities` | `mode`, surse încărcate, scenarii geografice disponibile, import formats, OCR configurat, date reale/sintetice. UI nu ghicește funcțiile. |
| `GET /catalog?q=&category=&cursor=` | Rezultate distincte `canonical|source_only`, număr cotații în context, variante și atribute lipsă. |
| `GET /offers?item=&scenario=` | Valori brute, relație/status, sursă/datǎ, bază preț și condiții; fără deducția `in_stock=true` din existența prețului. |
| `POST/PATCH /lists` și `/lists/{id}/lines` | Revizie și validări; formate cantitate separate de descriere. |
| `POST /comparisons` | Referință listă/revizie/context; rezultat sau 202 job. `known_subtotal`, `payable_total=null` dacă lipsesc componente, motive, alternative, coverage. |
| `POST /imports` | Fișier sau payload manual; cheie de idempotency; draft + duplicat detectat. Scanarea neconfigurată răspunde `OCR_NOT_CONFIGURED`, fără rezultate simulate. |
| `GET /imports/{id}` | Stare, câmpuri extrase, localizare în document, erori aritmetice, candidates; documentul original numai prin endpoint autorizat. |
| `PATCH /invoices/{id}/draft`, `POST /invoices/{id}/confirm` | Corecție versionată; serverul revalidează aritmetica și scope. Neconcordanțe pot rămâne în draft; nu intră automat în economii. |
| `POST /matches/{id}/decision` | Relație acceptată/respinsă și evidență; nu schimbă catalogul global dintr-o corecție privată. |
| `GET /savings`, `/supplier-recommendations` | Baza istorică/curentă explicită, acoperire în linii și valoare, date, incertitudini, fără total cumulativ dublat. |
| `POST /exports`, `DELETE /documents/{id}` | Export numai din firma curentă; ștergere controlată cu dependențe și politica de retenție explicată. |

`comparison_run` include cel puțin: `data_mode`, `as_of`, `source_snapshot_ids`, `algorithm_version`, `currency`, `tax_basis`, `scope`, `evaluated_candidates`, `missing_lines`, `excluded_reasons`, `assumptions`, `cost_breakdown`, `rank_basis`, `optimality`. `network_mode=offline` descrie lipsa colectării automate, separat de `data_mode=offline_snapshot|manual_quote|live_observation|mixed`. Fiecare observație are propriul mod și propriile date. O ofertă privată introdusă manual poate avea valabilitate declarată pentru data cererii; este etichetată „declarată de firmă, neverificată automat”, nu „colectată live”. Într-un rezultat mixt, cotațiile snapshot rămân datate 05.10.2026 și nu fundamentează un verdict integral curent. Nicio observație `offline_snapshot` nu poate primi eticheta `current_offer`, indiferent de momentul importului. UI afișează modul local global și datele/proveniența separat pentru fiecare sursă.

## 5. Importul surselor și mentenanța

Flux comun: fetch/import → fișier imuabil și hash → parsare în staging → verificări structurale/semantice → reconciliere și carantină → publicare atomică a setului acceptat → invalidare cache. Starea importului este `received|parsing|needs_review|published|failed`. Eșecul lasă ultimul set valid disponibil, etichetat cu vechimea sa; nu publică jumătate de catalog.

Contractul unui adaptor: `describe_capabilities`, `parse(snapshot)->records`, `validate(records)->findings`, `normalize(records)->observations`. Fetch-ul este separat și absent în testele offline. Fiecare câmp are locator în sursă și motiv pentru transformare. Nu se folosește un scraper universal și nu se trimite HTML-ul unui LLM care poate produce prețuri fără dovezi.

| Sursă | E1 | Etapa de activare și condiții |
|---|---|---|
| Monitor | XML-urile salvate, localitățile/razele exacte din probe | E2 adaptor GET limitat, timeout/backoff, verificare stabilitate/condiții. API/SLA contractual nu a fost demonstrat. |
| Lidl | JSON-ul salvat + XLSB original pentru audit | E2 parser XLSB dedicat cu teste de schemă și fallback la ultimul set bun. Nu importator Excel arbitrar. |
| Ofertă furnizor introdusă de firmă | Formular/CSV cu dată, monedă, cantitate, valabilitate și termeni | Privată; incompletă dacă termenii lipsesc. Nu se promovează global. |
| 2Performant/direct | Numai contractul de adaptor planificat | După acceptarea programului și verificarea feedului/drepturilor; [documentație feed](https://support.2performant.com/how-to-add-product-feeds-to-your-website). |
| Compari.ro | Referință de produs și documentare | Nu importăm catalog; nicio dependență de API public presupus. [Cercetarea](CERCETARE_COMPARI.md). |
| API marketplace de seller | Neactiv | Un API pentru seller nu dovedește acces la prețurile întregii piețe. |

Politică inițială propusă pentru E2, de validat cu sursa: un fetch simultan/sursă, timeout 30 s, maximum două reîncercări cu backoff/jitter, respectarea `Retry-After`; la 403/429 repetat suspendăm adaptorul. Catalog Monitor maximum o descărcare/zi, interogări de zonă la cererea utilizatorului cu cache și coalescing; Lidl maximum o descărcare/zi lucrătoare. Acestea sunt limite proprii prudente, nu cote contractuale verificate. Nicio căutare exhaustivă națională prin mii de coordonate și nicio ocolire a protecțiilor.

Validări de publicare: rădăcină XML/coloane așteptate, număr rânduri, câmpuri obligatorii, distribuție preț/unitate, duplicate, timestamp viitor, caracteristici schimbate, scădere a acoperirii. Variație de peste 30% a numărului de oferte față de ultimul import comparabil declanșează revizie, nu respingere permanentă; modificări de preț peste 50% sunt anomalii de investigat, nu dovada erorii. Pragurile sunt reguli de pilot și se calibrează pe date; promoțiile reale pot trece după confirmare. Orice schimbare de schemă neacoperită blochează publicarea.

Mentenanță: responsabil pentru fiecare adaptor, fixture real anonim pentru fiecare incident, test înaintea schimbării parserului, versiune și posibilitate de rerulare pe snapshoturi. Săptămânal în pilot: acoperire, fals pozitive, staleness, coada de revizie și erorile sursei. Fiecare sursă nouă livrează fișa de acces, taxonomie, semantica prețului, drepturi, frecvență, limite și test de retragere.

## 6. Prospețime, performanță și cache

Prospețimea este o stare calculată, nu simpla existență a unui răspuns HTTP. Păstrăm distinct data prețului, data colectării, metadata fișierului și intervalul de valabilitate. `source_priced_at` lipsă nu devine `retrieved_at`. Snapshoturile rămân permanent marcate ca snapshot, inclusiv dacă sunt importate în aceeași zi.

Politică E2 inițială: cotații Monitor cu dată mai veche de 24 h sunt `stale`; peste 72 h sunt numai istorice și excluse din recomandările curente. Intervalul explicit expirat are prioritate. Data viitoare cu peste 5 minute față de ceasul de referință merge în revizie. Lidl poate fi „fișier colectat recent; valabilitate individuală necunoscută”; vineri→luni nu inventăm o actualizare de weekend. Existența unei date recente nu confirmă stocul sau prețul la casă. Pragurile pot fi schimbate versionat pe sursă în urma măsurătorilor.

Cache-ul memorie/DB folosește cheia: scope public/tenant, firmă când este privat, localitate+rază/scenariu, ID-uri și cantități, eligibilitate card, bază fiscală, versiune listă, snapshot, versiune catalog și algoritm. Nu se partajează între firme rezultatele dependente de facturi, contracte sau carduri. TTL de răspuns 15 minute pentru căutări E2, dar statusul de vechime se recalculează la citire; cache-ul nu prelungește valabilitatea. Editarea unui produs, cost sau match invalidează comparațiile dependente și marchează istoricul ca revizie veche.

Ținte de acceptare propuse, măsurate pe mașina de dezvoltare cu configurația și datasetul consemnate: căutare p95 sub 300 ms pentru 104.794 rânduri, comparație simplă 20 linii×20 magazine p95 sub 1 s, UI interactiv sub 2,5 s la profilul mobil documentat, maximum 50 rezultate pe pagină. Import complet inițial sub 60 s și memorie proces sub 500 MB sunt bugete de verificat, nu rezultate obținute. Nu încărcăm catalogul de 20 MB în browser. XML se parsează incremental; importul scrie în loturi și publică atomic. Optimizarea coșului este limitată explicit în [motor](MOTOR_CORECTITUDINE.md), nu blocantă pentru comparația pe magazin.

## 7. OCR, confidențialitate și izolare

Completarea [ACCES_SI_EMAIL.md](ACCES_SI_EMAIL.md), din 6 octombrie 2026, este contractul pentru conturi, emailuri și administrarea firmelor în E4/E5. Descrie funcții viitoare; sesiunea și profilul local actuale nu sunt autentificare multiutilizator și nu trimit email.

**Decizia OCR:** E1 import manual/CSV/UBL; E2 extragere reală de text PDF cu `pypdf`; E3 adaptor local Tesseract pentru imagini, cu pachete de limbă și renderer PDF verificate la setup. Tesseract este candidat de implementare, nu promisiune de acuratețe a tabelelor de factură. Dacă benchmarkul nu trece, rămâne asistat de utilizator sau se configurează un furnizor extern după alegerea explicită a serviciului, datelor trimise și costului. [Instalare Tesseract](https://tesseract-ocr.github.io/tessdoc/Installation.html), [limitele extragerii textului PDF](https://pypdf.readthedocs.io/en/stable/user/extract-text.html). O pagină scanată fără text nu este un import PDF reușit; primește `needs_ocr`.

Contractul OCR: intrare fișier privat și pagini autorizate; ieșire blocuri text/câmpuri propuse cu localizare, confidence brut dacă motorul îl oferă, versiune și avertismente. Parserul aritmetic și confirmarea utilizatorului sunt etape separate. Un LLM eventual propune structură/candidați din text, fără acces la rețea, secrete sau instrumente și fără drept de confirmare. Instrucțiunile din factură sunt tratate ca date neîncredere. Nu se trimit documente la un serviciu extern implicit și nu se folosesc facturi private pentru antrenare sau catalog global.

E1 este **mod local de dezvoltare, pe un singur calculator de încredere**, nu autentificare pentru utilizatori multipli. Bind obligatoriu loopback, Host/Origin allowlist, CSRF la mutații, cookie de sesiune locală cu SameSite și token aleator, fără wildcard CORS. Sesiunea locală este limitată la firma de lucru; testele pot crea două firme, dar nu pretind protecție față de administratorul calculatorului. Interfața adaptată telefonului se verifică în viewport; accesul real de pe alt telefon necesită ulterior rețea/HTTPS/autentificare configurate. Nu expunem serverul local în LAN prin simpla schimbare a bindului.

E4: OIDC Authorization Code + PKCE, cookie HttpOnly/Secure, sesiuni revocabile, membership verificat server-side, PostgreSQL RLS ca strat suplimentar și teste cu două organizații. Workerul, fișierele, exportul, căutarea și cache-ul au aceeași limitare de tenant. Cheile providerelor exclusiv în procesul server/secret store, niciodată `VITE_*`, HTML, răspunsuri API sau loguri. Dev auth nu poate porni în `APP_MODE=production`.

E4 adaugă identitate stabilă `issuer + subject`, adresă verificată, invitație cu rol și token hashat, transfer controlat al ultimului Proprietar, politica de expirare/revocare și MFA Proprietar/Administrator. Recuperarea și verificarea adresei folosesc providerul de identitate; aplicația nu stochează parole proprii și nu unește conturi după email neconfirmat. Autorizarea se repetă la execuția workerului și la emiterea linkurilor de download/export.

Emailurile aplicației folosesc adaptor server-side și outbox tranzacțional cu cheie unică per eveniment, lease/retry limitat, termene de expirare și reconcilierea trimiterilor incerte. Webhookurile verifică semnătura pe corpul brut și se persistă înainte de confirmare; procesarea este idempotentă. Providerul neconfigurat, tokenul expirat, invitația revocată, accesul retras și bounce/reclamațiile împiedică trimiterea, fără simulare de succes. Preferințele și suprimarea se verifică din nou la expediere. Expeditor/DNS, secrete, retenție, costuri și probele G4-EMAIL/G4-DATE sunt documentate înainte de activare conform [ACCES_SI_EMAIL.md](ACCES_SI_EMAIL.md).

Upload: allowlist PDF/JPEG/PNG/CSV/XML, verificare MIME și semnătură, maximum 20 MB/document și 30 pagini inițial; 25 megapixeli/imagine, timeout de procesare per pagină, limită de resurse în worker, fără execuție de macro/script/entități externe. PDF criptat/malformat primește mesaj explicit; extensii neacceptate nu sunt redenumite în tăcere. Originalele se descarcă drept attachment și nu sunt randate ca HTML activ. Fără fetch server-side din URL-uri introduse liber; adaptoarele au host allowlist. Export CSV neutralizează formulele; SQL este parametrizat. E4 adaugă scanare malware și izolarea procesării documentelor înainte de pilotul extern.

Retenție propusă de produs: upload eșuat/neconfirmat 7 zile; original confirmat 90 zile, cu opțiunea de ștergere mai rapidă; datele structurate confirmate până la ștergerea de către firmă; log operațional fără conținut 30 zile; audit operațional 180 zile; backupuri rolling maximum 30 zile. Sunt valori de proiectare, **nu termene legale de arhivare**; aplicația nu înlocuiește arhiva contabilă. Înaintea lansării se configurează politica împreună cu responsabilul firmei și se verifică cerințele aplicabile.

Există două acțiuni distincte: **șterge originalul** elimină fișierul, OCR-ul brut, previews și indexul de text, dar păstrează datele structurate pe care utilizatorul a ales să le păstreze; analiza spune „original șters”, iar extragerea nu mai poate fi reluată. **Șterge achiziția și datele derivate** elimină și datele confirmate, corecțiile cu conținut privat, baseline-urile și copiile datelor în `comparison_run.input/output`, recomandări, exporturi temporare, job payloads, cache și indexuri. Agregatele active se recalculează; nu lăsăm un JSON „imuabil” care păstrează factura după ștergere. Imuabilitatea este o regulă de versionare în utilizarea normală, subordonată ștergerii datelor. Workerii primesc invalidare și verifică tombstone-ul înainte de scriere pentru a nu recrea rezultatul șters. Exporturile deja descărcate pe dispozitivul utilizatorului nu pot fi retrase de server, limită explicată în UI.

Ștergerea firmei aplică aceeași curățare tuturor datelor private active, lasă doar un eveniment minimal fără conținut și un tombstone pentru reaplicarea ștergerii la restaurare. Backupurile dispar la expirarea ferestrei; acest interval este explicat la cerere. Testele acoperă ambele moduri de ștergere, procesări în curs și restaurarea unui backup anterior ștergerii.

Exportul firmei livrează JSON/CSV cu valori confirmate, revizii, proveniență și originalele încă păstrate. Nu exportă secrete sau datele altor firme. Fișiere și DB criptate în mediul de producție, TLS, chei separate; în E1 limitele stocării locale sunt declarate și nu pretindem criptare proprie absentă. Backup înainte de migrare și test de restaurare; ținte E4 inițiale RPO 24 h/RTO 4 h, de validat prin exercițiu, nu SLA public.

## 8. Observabilitate și operare

Loguri JSON cu `request_id`, `job_id`, cod sursă, versiune parser, durată, număr rânduri, cod eroare. Redactare de text factură, CUI, adrese, tokenuri, URL-uri de feed cu secrete. Audit pentru confirmare, corectură, export, ștergere, acces extern OCR și schimbare de reguli. Nu înregistrăm fiecare apăsare a utilizatorului.

Metrici: ingestii reușite/eșuate, ultimele cotații per sursă, rânduri respinse și motive, acoperire semantică, match automat/revizuit/respins, false matches auditate, timp în coada de revizie, câmpuri OCR corectate, facturi confirmate fără diferențe, comparații cu cost complet, latențe și rată 5xx. Numitorii sunt vizibili: „99% corect” fără număr/categorie/perioadă este interzis.

Alarme E2/E4: schema sursei schimbată; două fetchuri consecutive eșuate; sursă peste hard-stale; o eroare de izolare; un false match critic (toner, variantă electronică) în producție; corecții OCR crescute față de baseline. Acțiune: suspendarea automatizării afectate, păstrarea datelor brute, afișarea limitelor și incident documentat. O eroare la o sursă nu ascunde restul surselor funcționale. Nu trimitem automat utilizatorilor mesaje comerciale sau furnizorilor cereri.

## 9. Decizii amânate cu declanșator clar

| Decizie | Când se ia | Efect asupra E1 |
|---|---|---|
| Furnizor hosting/OIDC/stocare | La pilotul multi-firmă, după regiune, cost, backup și acces | Niciun blocaj local. |
| OCR extern | Doar dacă localul nu atinge criteriile sau costul de revizie îl justifică | Importurile structurate/manuale funcționează. |
| Model semantic/embeddings | După măsurarea candidaților deterministici și existența setului etichetat | Nu schimbă identitatea; propune candidați revizuibili. |
| Feed electronice | La obținerea accesului/termenilor și a identificatorilor suficienți | Modelul păstrează deja categoria și atributele, fără oferte inventate. |
| Solver de optimizare generală | După cerere reală pentru coșuri mari și reguli complexe | Comparația pe magazin și split limitat sunt suficiente. |
| Notificări, aplicație nativă, contabilitate/ERP | După validarea utilității și retenției | Nu intră în primul MVP. |

Arhitectura se schimbă pe baza unei limite măsurate sau a unei cerințe reale. Separarea modulelor permite înlocuirea adaptorului, stocării și autentificării fără rescrierea regulilor de corectitudine.
