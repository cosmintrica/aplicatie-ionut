# Plan de implementare - Preturi achizitii

**Plan inițial din 5 octombrie 2026, completat la 6 octombrie pentru conturi și emailuri și la 7 octombrie pentru handover.** Starea implementării și publicarea surselor sunt descrise în [README](../README.md). Pentru preluare începe cu [HANDOVER.md](HANDOVER.md) și [AGENTS.md](../AGENTS.md).

Construim o aplicație web pentru firme mici care transformă o listă de cumpărături sau o achiziție confirmată într-o comparație explicabilă a ofertelor accesibile. Avantajul principal este corectitudinea identității produsului și a costului pentru cantitatea necesară. Prima livrare folosește exclusiv probele salvate; extinderea la surse active, OCR și producție are etape verificabile, fără a bloca începutul local.

Planul inițial a fost elaborat înaintea implementării aplicației locale. Sursele sunt publicate ulterior; etapele viitoare nu devin funcții implementate prin includerea lor în plan. Starea actuală este documentată în [raportul implementării](IMPLEMENTARE_COMPARATII.md).

## 1. Ordinea de lectură și autoritatea documentelor

| Document | Rol |
|---|---|
| [SPECIFICATIE_PRODUS.md](SPECIFICATIE_PRODUS.md) | Funcții, navigație, ecrane, stări, design și criterii UX. |
| [MOTOR_CORECTITUDINE.md](MOTOR_CORECTITUDINE.md) | Taxonomie/atribute, matching, coșuri, economii, furnizori, OCR și exemple matematice. Autoritatea pentru reguli de calcul. |
| [DECIZII_ARHITECTURA.md](DECIZII_ARHITECTURA.md) | Stivă decisă, model de date, API, ingestie, privacy, performanță și operare. |
| [ACCES_SI_EMAIL.md](ACCES_SI_EMAIL.md) | Completare din 6 octombrie 2026: conturi, verificare și recuperare, onboarding, roluri/invitații, sesiuni și emailuri E4/E5, cu gates explicite. |
| Acest document | Ordinea implementării, scope pe etape, dependențe, backlog și criterii de trecere. |
| [CERINTE_EXTINSE.md](CERINTE_EXTINSE.md), [cererea inițială](../CERERE_INITIALA.md) | Cerințele și mandatul utilizatorului. |
| [raportul probelor](../RAPORT_TESTARE.md), [VALIDARE_IDENTITATE_DATE.md](VALIDARE_IDENTITATE_DATE.md) | Evidență reală și limite. Validarea semantică nu trebuie confundată cu testele parserului. |
| [CERCETARE_COMPARI.md](CERCETARE_COMPARI.md) | Cercetarea publică și sursele primare Compari.ro; referință, fără integrare de date autorizată. |

Într-un conflict, cerințele curente ale utilizatorului și datele observate au prioritate. Pentru comportamentul implementat, schema și API se verifică sursele, migrațiile, testele și [contractul actual](../backend/SMART_CONTRACT.md); arhitectura descrie și o destinație viitoare. Pentru etape și livrare se urmează planul, iar pentru formule și invarianti se urmează motorul. O neconcordanță se rezolvă documentat înaintea schimbării regulii relevante, fără a suspenda lucrul independent.

## 2. Promisiunea produsului și delimitarea

Promisiune: **„Compară costurile pentru produsele de care ai nevoie, în sursele și condițiile verificate.”** Fiecare rezultat explică produsul, cantitatea, sursa, data, condițiile și ce nu se știe. „Cel mai mic preț găsit” este legat de sursele, zona, momentul și categoria de potrivire analizate. Nu înseamnă minimul absolut al pieței românești.

Rezultatele urmărite:

1. Utilizatorul alcătuiește sau repetă o listă în câteva minute, fără cunoștințe tehnice.
2. Distinge același produs, alt ambalaj, echivalent acceptat și simplu candidat.
3. Importă o achiziție și confirmă datele înainte ca ele să fundamenteze economii.
4. Vede diferența de cost pe aceeași bază, cu costuri lipsă explicite.
5. Primește motive verificabile pentru renegociere, comandă de probă sau schimbare de furnizor.

Nu intră în MVP local: checkout/plăți, comenzi ori emailuri către furnizori, marketing și alerte comerciale automate, integrare bancară, gestiune contabilă oficială, depunere în RO e-Factura, toate sursele din România, inventar în timp real, scraping național, scoring de „calitate” a comercianților fără probe, aplicație mobilă nativă sau predicții garantate ale prețurilor. Emailurile tranzacționale necesare verificării adresei, recuperării contului și invitațiilor intră în E4 conform [specificației de acces și email](ACCES_SI_EMAIL.md); nu există în versiunea locală actuală. Un catalog larg se poate naviga de la început; acoperirea reală de oferte rămâne explicit limitată.

## 3. Ce există și ce dovedește

La redactarea inițială existau numai probele. Acum repository-ul public conține aplicația locală E0/E1a, revizia UI/comparații, scripturi, lockuri, teste și documentație. Următoarea etapă recomandată este E1b. [Handover-ul](HANDOVER.md) separă capabilitățile implementate de criteriile viitoare. Nu mutăm și nu suprascriem probele pentru a face teste să treacă. Manifestul public reflectă normalizarea metadatelor descrisă în [PUBLICARE.md](PUBLICARE.md), cu SHA-256, scope, timestamps disponibile și limitările fiecărui fișier.

| Evidență existentă | Utilizare în implementare | Ce nu demonstrează |
|---|---|---|
| Catalog Monitor: 104.794 rânduri, 12 nume goale | Căutare locală, excluderea numelor goale din rezultate normale, contorizare în calitatea datelor | Oferte actuale pentru toate produsele sau identitate exactă. |
| Slatina 5 km: 18 magazine; București 1 km: 19 magazine, șapte ID-uri | Scenarii fixe de demo și regresie | Căutare în alte zone sau toate magazinele orașelor. Nu însumăm 18+19 drept acoperire națională. |
| 65/73 cotații pozitive datate în cele două probe | Test de parsare și afișare a sursei/datei | Stoc, TVA/SGR/transport cunoscut sau checkout. |
| FoodBasket: 48 cotații, 15 magazine cu cele trei ID-uri | Reproducere a sumelor de cotații: Supeco 33,86; Kaufland 41,07; Carrefour Market Aleea Muncii 42,87 lei | Coșuri identice semantic sau costuri finale. |
| Intense/Alintaroma sub `1013048`; `K`, `Kg`, `BUC`, `L` diferite | Cazuri obligatorii de abținere/conflict | Dreptul de a normaliza prețul doar din gramajul titlului. |
| Ariel etichetat `LAPTE` în XML; alte categorii comerciale imprecise | Taxonomie internă independentă, carantină la conflict | Corectitudinea categoriei sursei. |
| Lidl: 2.444 rânduri, 34 categorii, opt duplicate suplimentare nume+gramaj | Import JSON și audit XLSB, potrivire conservatoare | GTIN, stoc, valabilitate individuală sau SKU comun Monitorului. |
| 32 teste parser raportate ca trecute | Baseline de regresie, de rulat la implementare | Precizie de matching, OCR, securitate sau utilizabilitate. |

Data `05.10.2026 04:00` este declarată de sursă. Reimportarea fișierelor astăzi sau ulterior nu o înlocuiește. Datele sintetice pentru calcule/teste se etichetează separat și nu se amestecă în rezultatele comerciale.

Pe pagina oficială, Lidl declară lista sortimentului permanent publicată luni-vineri, prețuri în rețea și SGR exclusă; nu oferă prin acest enunț stoc individual verificat, [sursa primară](https://www.lidl.ro/c/preturile-la-zi/s10019622). Această informație poate fi evidență la nivel de sursă; nu completează automat câmpuri absente per produs.

## 4. Lecțiile Compari.ro aplicate

Documentația Compari descrie feeduri XML/CSV ale comercianților, identificatori stabili, categorii și coduri de producător pentru electronice. Aplicăm un contract similar de calitate a intrării, fără a copia catalogul lor. [Cerințe feed](https://www.compari.ro/static/feed-requirements.html).

Asocierea documentată folosește producătorul, codul oficial și EAN când este disponibil; regulile depind de categorie. Aplicăm identificatori verificați plus atribute critice și revizie la conflict. Nu deducem algoritmul intern, folosirea AI sau o precizie nedeclarată. [Asociere produse](https://www.compari.ro/static/product-pairing.html).

Compari distinge ofertele asociate de produsele individuale sau în curs de procesare. Aplicăm aceeași distincție de stare: sursa poate fi vizibilă fără a intra încă într-o comparație de identitate. Actualizarea periodică nu este timp real. [Stări și actualizări](https://www.compari.ro/static/displayed-products.html).

Diferențiatorul aplicației este contextul firmei: facturi, cantități reale, prețuri negociate private, cost per comandă și oportunități explicabile. Integrarea Compari nu este o dependență a planului; nu este demonstrat un API public de export al întregului catalog. Cercetarea extinsă păstrează sursele, incertitudinile și aspectele comerciale.

## 5. Ordinea livrărilor

### E0 - Fundație și contracte de corectitudine

**Rezultat:** proiectul pornește local, are schemele de bază și un baseline reproductibil. Dependențe: runtime-uri locale și descărcarea pachetelor, fără conturi de servicii.

- Păstrează `probe-data`, `scripts`, `tests`, documentația existentă. Creează `backend`, `web`, `config`, `fixtures`, `var` separat. Inițializarea Git este opțională pentru implementator; nu publică nimic și exclude DB, facturi, cache, `.env` și artefacte mari regenerabile.
- Configurează React/TS/Vite și Python/FastAPI/SQLite, lockfile-uri și comenzi documentate. Nu migra pe o platformă disponibilă doar fiindcă există un plugin.
- Adaugă schemele de categorie, tipuri `Money`, cantitate, evidență, relație de potrivire, observație și stări de rezultat. Scrie primele teste înaintea calculelor UI.
- Creează manifestul probelor fără modificarea originalelor; înregistrează separat dovezile absente, inclusiv timestamps de colectare care nu apar în `requests.json`.
- Rulează cele 32 teste PowerShell. Portarea logicii Monitor în Python se verifică pe aceleași cazuri, apoi adaugă validările semantice; parserul PowerShell nu este șters.

**Gate G0:** pornire loopback, migrație și seed idempotente, probe intacte, teste de bani/unități trecute, API capabilities declară `offline_snapshot`, niciun fetch la furnizori la pornire.

### E1a - Primul flux util, exclusiv snapshot

**Fluxul local este implementat, inclusiv revizia ulterioară a interfeței și motorului.** Cerințele de mai jos păstrează ținta și limitele etapei, fără a declara toate gates viitoare certificate. Ecrane: pornire cu acoperire, catalog/căutare, listă, comparație, detaliu dovadă. La preluare verifică baseline-ul și continuă E1b; nu reface aplicația de la zero.

1. Importă toate cele 104.794 intrări ca produse ale sursei și 2.444 rânduri Lidl. Nu le promovează în masă la produse canonice confirmate. Taxonomia internă există pentru toate domeniile; mappingul se aplică numai când justificat, restul rămâne „de clasificat”.
2. Creează un subset editorial inițial de maximum 30 articole relevante: lapte, cafea, apă, curățenie și hârtie, numai în măsura în care probele le susțin. Categoriile fără ofertă acceptă liste/text liber și explică lipsa acoperirii. Nu inventează produse pentru a atinge 30.
3. Oferă numai scenariile geografice probate, cu raza și data lor. Geolocația este neactivată în E1; alegerea altui oraș produce „nu există date salvate pentru această zonă”, fără a reutiliza tacit Slatina.
4. Permite căutare și adăugare de produs/variantă/cantitate în listă; păstrează cererea la erori. Afișează cotațiile pe magazin, denumirile comerciale și unitățile originale, cu relațiile și lipsurile explicate.
5. Reproduce valorile raportului într-o secțiune „sume ale cotațiilor sursei”, separată de coșul compatibil. Un total cu bază de preț/variantă incertă nu primește badge „coș complet verificat” sau „economie”.
6. Activează calculele pe cantități numai pentru datele a căror identitate și bază sunt confirmate; dacă setul real nu oferă dovezile necesare, afișează motivul abținerii. Fixtures aritmetice sintetice demonstrează funcția în teste, nu prin prețuri fabricate în aplicație.
7. Păstrează lista și preferințele în DB locală, arată data ultimului import și limitele în toate rezultatele/exporturile.

**Demonstrabil acum:** ingestie/căutare, liste, vizualizarea cotelor reale, diferențierea coșului parțial, conflictul de variantă, abținere explicabilă, structură mobilă și reproducerea datelor. **Nedemonstrat acum:** minim plătibil, ofertă live, facturi reale procesate, economie realizată sau recomandare fermă de schimbare furnizor.

**Gate G1a:** scenariul demonstrativ D1 de mai jos funcționează offline; nu există afirmații live și nici substituții ascunse; un reload păstrează lista; browserele afișează corect layoutul mobil.

### E1b - Achiziții confirmate și analize locale

**Rezultat:** date introduse de utilizator devin o bază trasabilă pentru comparație. Depinde de G1a și regulile complete de calcul.

- Formular de achiziție manuală cu furnizor, dată, document opțional, monedă, linii, cantitate, unitate, preț/bază, reduceri, TVA dacă este prezent, taxe/transport și total. Userul vede și confirmă rezumatul.
- Import CSV cu preview, maparea coloanelor, alegerea separatorului/localei și erori pe rând. Nu interpretăm automat `1,234` dacă sensul este ambiguu. Furnizăm un șablon documentat.
- Import UBL 2.1 `Invoice` din fișier local, namespace corect; furnizor, ID/datǎ, monedă, linii/cantități/unități, preț și `BaseQuantity`, reduceri/taxe/totaluri. XML necunoscut rămâne draft neacceptat, cu mesaj. `CreditNote`, avansuri complexe, valute și profile nesuportate sunt detectate și rutate la introducere/revizie explicită până la suport; nu sunt tratate drept facturi obișnuite. Aceasta este extragere structurată, nu validare fiscală completă sau integrare ANAF. [Standard UBL 2.1](https://docs.oasis-open.org/ubl/os-UBL-2.1/UBL-2.1.html).
- Separă originalul/textul extras de câmpurile confirmate și consemnează corecturile. Sumele greșite sau identitatea insuficientă împiedică folosirea liniei în economii, fără a pierde importul.
- Permite mapări private ale produselor recurente ale furnizorului, cu valabilitate pe semnătura atributelor; renunță la mapare când ambalajul/codul se schimbă.
- Istoric și diferențe față de cotațiile snapshot pe linii comparabile; comparațiile necontemporane sunt „scenariu față de date salvate”, nu „oportunitate actuală”. O ofertă proprie, introdusă de firmă cu dată/valabilitate/condiții, poate fundamenta scenariul curent în scope privat.
- Export CSV/JSON și ștergere document/achiziție cu recalcularea analizelor. Prețurile negociate rămân în firmă.

**Gate G1b:** o achiziție introdusă manual și una importată ajung la aceeași valoare confirmată; corecția reface analiza; duplicatul nu dublează achizițiile/economiile; câmpurile necunoscute rămân necunoscute; exemplele sintetice sunt etichetate și separate.

### E2 - Surse active controlate și recomandări demonstrabile

**Rezultat:** pilot local cu prețuri colectate la cerere/periodic, statut de prospețime și recomandări limitate la dovezi. Dezvoltarea adaptorului și testarea pe fișiere pot continua fără acord comercial; lansarea/republicarea depind de drepturile clarificate. Un eșec de acces nu blochează E1.

- Adaptoare live Monitor/Lidl separate de snapshot, staging, versionare, timeout/backoff și limite proprii din arhitectură. Nu rula orchestrat scriptul vechi fără `-Offline` peste probele originale; colectările noi au director și manifest propriu.
- Interfață de stare a surselor: colectat, vechi, parțial, indisponibil, în revizie. Nu există toggle UI care transformă un snapshot în live.
- Contract de ofertă proprie/directă/CSV furnizor; feed 2Performant numai după acceptare/configurare. Înainte de activare, validează termenii, câmpurile, TVA, transportul, stocul, eligibilitatea B2B și semantica SKU.
- Extragere PDF cu text real și lipire text, cu localizare și revizie. PDF scanat detectat și trimis la starea `needs_ocr`; nu prezenta OCR simulat.
- Comparație într-un magazin, minimum per articol ca referință teoretică și split limitat. Utilizatorul vede costurile suplimentare și domeniul explorat, fără promisiune de optim global.
- Recomandări de renegociere/schimbare după pragurile de dovezi din motor; lipsa dovezilor generează „verifică” sau „cere o ofertă”, fără expedierea mesajului. Condițiile B2B necunoscute blochează verdictul ferm.
- Pilot de utilitate propus: 3-5 firme voluntare sau utilizatori reprezentați prin date anonimizate, cel puțin 20 liste reale. În E2 acestea sunt teste moderate pe instanțe locale/date separate pentru fiecare firmă, fără server comun, LAN sau acces multi-firmă la distanță; un pilot găzduit așteaptă E4. Participanții și facturile nu sunt disponibili sau contactați în acest plan.

**Gate G2:** minimum 10 cicluri de import distribuite pe 14 zile pentru fiecare sursă activată; monitorizare a erorilor, probe cu staleness, incidente și reparații reproductibile. Lipsa a 14 zile de observații limitează statutul la experimental; nu este compensată de 14 cereri într-o zi. Recomandarea are bază completă și dovadă de eligibilitate ori rămâne condiționată. Niciun nou acord/cont nu este presupus obținut. Această observație de stabilitate nu înlocuiește gate-ul statistic al asocierilor automate: minimum 600 decizii independente evaluate pe ruta activată, precizie observată ≥99,5%, limita inferioară Wilson95% ≥99% și zero conflicte critice, conform motorului.

### E3 - Scanare OCR reală, evaluată

**Rezultat:** import din fotografii și PDF scanat, cu dovezi la nivel de câmp, revizie și confirmare. Se poate dezvolta în paralel cu observarea surselor E2, după G1b; nu depinde de accesul la feeduri noi.

- Adaptor Tesseract local + pachete de limbă + rasterizare PDF în proces limitat; verificare explicită a binarelor/licențelor/dependențelor. Nu le instala în etapa de planificare. Tratează multipagină, rotație, calitate insuficientă, PDF mixt text/imagine, timeout și reluare idempotentă.
- Preprocesare conservatoare: copie de lucru pentru orientare/redimensionare/contrast, originalul păstrat; nu elimina semne zecimale pentru un aspect mai curat. Vizualizare original și câmpuri alăturat sau în foi mobile.
- Motorul produce text real; parserul propune câmpuri; aritmetica verifică sumele; utilizatorul confirmă. Confidence diferit între motoare nu se mediază ca probabilitate globală.
- Set inițial propus: minimum 60 documente/600 linii, minimum 6 layouturi de furnizor, inclusiv fotografii dificile și 15 documente rezervate pentru evaluare finală. Transcriere verificată de om; layouturile/duplicatele apropiate nu se împart între calibrare și test.
- Dacă localul nu atinge țintele, păstrează extragerea asistată, măsoară timpul de corecție și compară un provider extern numai când configurarea, trimiterea documentelor și costul sunt acoperite de autorizare specifică. Interfața nu activează un serviciu extern pe ascuns.

**Gate G3:** pe setul ținut separat, ≥95% exactitate a câmpurilor numerice esențiale înainte de corectură, 100% din neconcordanțele aritmetice din set semnalate, zero facturi neconfirmate incluse în economii. Raportează documentele ilizibile și abstinențele, nu le scoate din numitor. Dacă pragul nu trece, funcția rămâne „scanare asistată în evaluare”, cu confirmare obligatorie. Pragurile sunt ținte de produs, nu precizie deja demonstrată.

### E4 - Pilot multi-firmă și pregătire pentru producție

**Rezultat:** autentificare reală, izolare, backup/restore și operațiuni testate. Configurarea de servicii și publicarea cer autorizarea aferentă; planul nu o acordă.

- PostgreSQL cu migrare verificată din SQLite, OIDC, roluri și sesiuni, storage privat, TLS, secret management. Testele cross-tenant acoperă API, fișiere, jobs, cache, export, audit și ștergere.
- Signup/login, verificare email, recuperare acces, onboarding de firmă, invitații, roluri și selector multi-firmă conform [ACCES_SI_EMAIL.md](ACCES_SI_EMAIL.md). Emailurile aplicației au outbox, idempotency, retry limitat, webhooks verificate, suprimare la bounce/reclamații și preferințe distincte; providerul de identitate este responsabil explicit pentru mesajele sale.
- Politică de date clară, proces de ștergere/export și furnizori OCR identificați, acorduri de surse, termeni și limite afișate. Analiza obligațiilor aplicabile se face pentru operațiunea reală înainte de lansare; nu este presupusă finalizată prin acest plan tehnic.
- Scanare/izolare documente, rate limiting, monitorizare, backupuri și exercițiu de recuperare, invalidare sesiuni și plan de incident.
- Pilot restrâns cu suport și registru al erorilor de identitate/preț. Gate de matching automat din motor; până atunci confirmare/revizie obligatorie pentru asocierile riscante.

**Gate G4:** teste de izolare fără excepții, restaurare demonstrată, surse permise pentru utilizarea concretă, costuri și limite configurate, indicatori de calitate publicați în raport intern; autorizare distinctă înaintea publicării.

G4 include obligatoriu G4-ACCES, G4-FIRME, G4-EMAIL, G4-DATE și G4-UX din [specificația de acces și email](ACCES_SI_EMAIL.md). Repository public nu înseamnă aplicație găzduită; ecranele de login, cookie-ul local și un HTTP 200 de email nu înlocuiesc probele de autentificare, izolare sau livrare.

### E5 - Electronice și extindere justificată

- Primul lot: consumabile de imprimantă și birotică, apoi laptopuri/monitoare, în funcție de feedul obținut și cererea pilotului. Modelul și taxonomia există deja, dar acoperirea se activează per categorie.
- MPN/GTIN/brand, RAM/stocare/model exact/regiune/condiție, garanție, kit și vânzător marketplace devin filtre obligatorii după categorie. Aceeași platformă nu înseamnă același vânzător.
- Set etichetat distinct și verificare de precizie pe noua categorie; nu moștenim scorurile alimentelor. Automatizările pot fi activate pe alimente și oprite pe tonere/electronice.
- Numai după cerere măsurată: import ERP, alerte opționale, solver coșuri mari, selecție asistată semantic și extensie geografică. Nu adăuga din start un sistem generic pentru orice produs și orice contract.

## 6. Backlog cu dependențe și dovada de finalizare

`P0` = necesar corectitudinii/primului flux; `P1` = necesar MVP extins; `P2` = extensie după pilot. Ordinea este o dependență tehnică, nu un calendar promis.

| ID | Pri. / etapă | Livrabil concret | Depinde de | Dovada de finalizare |
|---|---|---|---|---|
| B01 | P0/E0 | Manifeste, bootstrap, lockfiles, scripturi start/check | - | Pornire din instalare curată; hashurile probelor intacte. |
| B02 | P0/E0 | Money/Quantity/Evidence, migrații, repository scope | B01 | Round-trip decimal, null, timezone, rollback, cross-tenant FK. |
| B03 | P0/E1a | Import Monitor XML și rețele | B02 | Numerele din raport reproduse, toate ID-urile distincte păstrate. |
| B04 | P0/E1a | Import Lidl JSON și provenance XLSB | B02 | 2.444 rânduri/34 categorii, duplicate inspectabile, date neinventate. |
| B05 | P0/E1a | Taxonomie, normalizare, candidat/match/revizie | B03/B04 | Setul real de conflicte nu are uniri automate greșite. |
| B06 | P0/E1a | Design primitives, navigație, capabilities, catalog | B01/B03 | 360 px, tastatură, nume lungi, empty/error/loading. |
| B07 | P0/E1a | Listă persistentă și comparație pe cotații | B05/B06 | Coșurile incomplete nu câștigă; evidență deschisă per ofertă. |
| B08 | P0/E1b | Motor cost: pachete, TVA/SGR, terms, necunoscute | B02/B05 | Exemple și proprietăți aritmetice; `payable_total=null` corect. |
| B09 | P1/E1b | Achiziții manuale, CSV și UBL, draft/confirm | B02/B06 | Aceeași achiziție prin trei intrări produce aceleași date confirmate. |
| B10 | P1/E1b | Istoric, baseline și diferențe/economii | B08/B09 | Nicio economie din draft sau comparație temporală etichetată greșit. |
| B11 | P1/E1b | Export/ștergere/revizii, mapări private | B09/B10 | Duplicat, corectură, revocare mapping, ștergere recalculată. |
| B12 | P1/E2 | Staging/job/adaptoare active și staleness | B03/B04 | Timeout/429/schema schimbată/ultima versiune bună, fără overwrite probe. |
| B13 | P1/E2 | Cost pe furnizor/split limitat și explicații | B08/B12 | Prag transport, comandă minimă, limită domeniu/optimalitate. |
| B14 | P1/E2 | PDF text și lipire text | B09 | PDF text real, scan detectat, draft cu localizare. |
| B15 | P1/E2 | Recomandări furnizor și feedback | B10/B12/B13 | Caz pozitiv, economie anulată de transport, dovadă insuficientă. |
| B16 | P1/E3 | OCR adaptor/worker/UI corectare | B09/B14 | Ieșire reală, erori/timeout, document mixt, rerulare idempotentă. |
| B17 | P1/E3 | Set etichetat și raport OCR/matching | B05/B16 | Metrici pe date separate; pragul măsurat, abțineri incluse. |
| B18 | P1/E4 | PostgreSQL/OIDC/roluri/storage privat | B11 | Migrare, două firme, acces document și jobs, logout/revocare. |
| B18a | P1/E4 | Conturi/onboarding/recuperare/invitații/sesiuni | B18 | G4-ACCES și G4-FIRME; adresă verificată, expirare/reutilizare, roluri și revocare fără acces rezidual. |
| B18b | P1/E4 | Email tranzacțional, outbox și preferințe | B18a | G4-EMAIL/G4-DATE; retry idempotent, restart, bounce/reclamații, link expirat și preferință revocată. |
| B19 | P1/E4 | Operare/backup/retention/producție | B12/B18 | Restore, ștergere după restore, source rights, incident drill. |
| B20 | P2/E5 | Feed nou + categorie nonalimentară | B05/B12/B17 | Contract sursă și set de evaluare per categorie. |
| B21 | P2/E5 | Alerte/ERP/optimizare extinsă | Dovadă de cerere | Criteriu de utilitate și cost înainte de implementare. |

Paralelizare recomandată după B02: un editor pe `backend/adapters`/fixture-uri, unul pe UI, unul pe motorul de domeniu; contractele API și ownershipul fișierelor se stabilesc înainte. Integrarea listă→comparație nu se lasă la final. Curarea datelor și testele de adversitate rulează în paralel cu UI; nu se delegă verificarea fiscală unui algoritm de similaritate.

## 7. Matricea de acceptare

| Arie | Criteriu măsurabil |
|---|---|
| Integritatea probelor | Niciun fișier original modificat; toate importurile au hash/locator și sunt idempotente. |
| Parser Monitor | 32 teste existente + port cu aceleași rezultate; 104.794/12, 18/19, 65/73, 48/15 se reproduc ca metrici de sursă. |
| Semantică reală | Intense/Alintaroma, 250/500 g, unități ambigue, categorii Ariel/Fairy sunt detectate fără identity merge automat. |
| Matching nou | Precision, recall candidați, abstinență și coverage pe categorie; gates din motor. Setul mic de E1 nu susține o afirmație comercială „99%”. |
| Aritmetică | Decimal, bani întregi la total, cantități fracționare/pachete întregi, discount/minim/SGR/transport acoperite; lipsă ≠ zero. |
| Coș | Niciun subtotal incomplet comparat drept total complet; constraints și produse lipsă sunt vizibile. |
| Temporal | Snapshot nu devine live; prețul istoric și curent au date distincte; expirare/ceas viitor/cache testate. |
| Facturi | Draft/extras/confirmat separate; duplicat nu dublează; corecție invalidantă; total corect nu implică match corect. |
| OCR | Motor real sau stare neconfigurat; G3 măsurat separat pe format/dificultate, fără excluderea cazurilor grele. |
| Economii | Fiecare valoare deschide liniile/baza/datele/costurile; negativele se păstrează; estimările nu se însumează ca realizate. |
| Recomandări | Caz cu toate dovezile și caz cu transport care anulează avantajul; necunoscutele împiedică verdictul ferm. |
| Confidențialitate | Zero acces cross-tenant în testele API/fișier/job/cache/export; zero secret în bundle/log; corecții private. |
| Conturi/email - E4 | Gates de acces, firme, email, date și UX din [ACCES_SI_EMAIL.md](ACCES_SI_EMAIL.md); fără cont fictiv sau etichetă de livrare fără dovadă. |
| UX | Viewport 360/390/768/1280 px fără scroll orizontal global, zoom200%, navigare tastatură, focus și labels; contrast AA verificat. |
| Performanță | p95 căutare<300 ms, comparație20×20<1 s, profil și date consemnate; bugete UI/import din arhitectură. |
| Operare | E2 loguri/adaptor suspendabil; E4 restore și retenție testate, nu doar backup „configurat”. |

Set de regresie minim pentru domeniu: minimum 40 cazuri explicite, distincte de cele 32 ale parserului. Include zece cazuri de matching (inclusiv toner și electronice sintetice), zece de cost/coș, zece de facturi/timp și zece de izolare/proveniență. Numărul nu substituie relevanța; cazurile se aleg după invarianti și erori reale. Property tests: reimportarea nu dublează; un cost suplimentar pozitiv nu micșorează totalul când restul termenilor rămân fixați; creșterea acoperirii nu ascunde lipsuri; round-trip-ul zecimal nu alterează suma; o asociere respinsă nu reapare automat fără dovezi noi. Promoțiile cu prag sunt testate separat, deoarece pot modifica monotonicitatea.

### Scenarii de demonstrație

**D1 / E1a:** pornește offline, selectează Slatina 5 km, adaugă Zuzu 1,5% 1 l / Jacobs 250 g / Borsec 2 l, deschide sursa și data, vezi 15 acoperiri de cotații pentru ID-uri și sumele brute, apoi conflictul variantei Jacobs și costurile necunoscute. Schimbă la produs fără cotație: „lipsă cotație”, nu zero și nu „indisponibil în magazin”. Alege alt oraș: stare fără date, fără rezultate din Slatina. Reîncarcă și recuperează lista.

**D2 / E1b:** importă un CSV/UBL sintetic etichetat, corectează o cantitate, verifică diferența de total și confirmă; leagă produsul și baza de preț cu evidență de test. Compară cu o ofertă sintetică separată, vezi pachetele necesare, surplusul și economiile semnate; reimportul este duplicat, corecția invalidează analiza. În modul de date reale, fără factură reală, pagina spune că nu există achiziții confirmate.

**D3 / E2:** ultima ofertă validă este urmată de lipsă de cotație/eroare/retragere. UI păstrează istoricul dar nu îl transformă în ofertă curentă. Transportul necunoscut blochează totalul final; transportul cunoscut poate inversa ordinea magazinelor. Recomandarea își explică motivul sau se abține.

**D4 / E3:** fotografie lizibilă și fotografie înclinată, text OCR real, marcarea unei virgule citite greșit, corectură trasabilă și confirmare; PDF mixt și document duplicat. Fără adaptor, captura nu produce date. O factură cu total corect și toner incompatibil rămâne blocată pentru comparație.

**D5 / E4:** firma A importă o factură și o ofertă negociată; firma B încearcă IDs/URL/export/job/cache și primește acces refuzat fără metadate private. Ștergere, backup și restore respectă tombstone-ul de ștergere.

## 8. Costuri și efort, fără tarife inventate

E1 nu depinde de API-uri facturabile sau hosting, deci poate avea **zero consum de servicii externe plătite** pe calculatorul existent. Acesta nu este cost total zero: timpul de dezvoltare/curare, echipamentul, energia, instalarea și suportul rămân costuri. Nu presupunem free tier-uri sau prețuri contractuale neverificate.

Estimare de planificare, nu ofertă: un dezvoltator familiar cu Python/React, contribuție punctuală pentru revizia datelor, scope-ul de mai sus și fără întârzieri de cont/acord. E0 1-2 zile de lucru, E1a 4-7, E1b 5-8, E2 5-9 plus cele 14 zile calendaristice de observație, E3 6-12 incluzând integrarea/evaluarea dar nu obținerea corpusului, E4 6-10. E0-E1b: aproximativ **10-17 zile de lucru**; E0-E4: **27-48 zile**, cu dependențe externe care pot prelungi calendarul. Aceste intervale sunt estimări de inginerie ale scope-ului, nu măsurători sau promisiuni. Se reestimează după G1a; o echipă/agent mai rapidă nu anulează timpul necesar probelor și feedbackului.

Buget lunar de pilot se calculează după alegerea furnizorilor:

```text
C_lunar = compute + DB + storage_GB × tarif_storage + egress_GB × tarif_egress
        + pagini_OCR × tarif_pagina + consum_model × tarif_model
        + licente/feeduri + ore_mentenanta × tarif_ora
        + linii_revizuite × secunde_medii_pe_linie / 3600 × tarif_revizie
```

Scenariu de volum, explicit ipotetic: 100 firme × 20 facturi/lună × 2 pagini = 4.000 pagini OCR/lună; 10% revizie × 10 linii/document × 2.000 documente = 2.000 linii revizuite. La 30 secunde/linie rezultă 16,7 ore de revizie/lună, înainte de incidente. Nu sunt valori măsurate; formula arată de ce precizia și abstinența au cost operațional. La aproximativ 1 MB/pagină, originalele adaugă circa 4 GB/lună înainte de copii/backup; retenția schimbă direct bugetul.

Înainte de alegerea providerului se verifică pagina tarifară oficială, regiunea, taxele, cursul, minimumurile, limitele și politica de date; valorile se salvează cu dată. Pentru OCR local se măsoară secunde/pagină și memorie, nu se presupune gratuitate operațională. Pentru feeduri se solicită termenii numai în etapa autorizată, fără presupuneri despre acces sau preț.

## 9. Riscuri și răspunsuri

| Risc real | Efect | Răspuns și criteriu de oprire a automatizării |
|---|---|---|
| Identitate greșită sub ID comun | Economii false/cumpărare incompatibilă | Atribute critice, evidență, conflict prioritar, revizie; orice caz critic suspendă regula afectată. |
| Unitate/bază preț ambiguă | Eroare de4×/6× sau mai mare | Separare ambalaj și bază; nicio conversie fără dovadă. |
| Date vechi ori sursă schimbată | Clasament inutil | Timestampuri distincte, hard-stale, schema gate, ultimul set bun etichetat. |
| Acoperire redusă | Produs pare mai complet decât este | Numitori per zonă/categorie/listă, lipsuri vizibile, fără extrapolare națională. |
| Condiții comerciale necunoscute | Avantaj anulat la checkout | Transport/TVA/SGR/card/minim explicite, scenariu condiționat sau abținere. |
| OCR cu cifre aparent plauzibile | Istoric și recomandări corupte | Text original, verificări aritmetice, revizie câmpuri și confirmare obligatorie. |
| Documente private divulgate | Prejudiciu firmei | Scope în toate căile, fișiere private, retenție, niciun provider implicit. |
| Acces tehnic fără drepturi clarificate | Blocaj de lansare/sursă retrasă | E1 offline, adaptoare separate; launch gate per sursă, fallback la oferte private. |
| Prea multă revizie manuală | Produs neeconomic | Măsurare timp/abținere/categorie, subset bine curat și mapări private reutilizabile. |
| Interfață bogată dar greu de folosit | Lipsă adopție | Livrare verticală, teste cu utilizatori și explicarea incertitudinii în limbaj simplu. |
| Extindere prematură | Întârzierea valorii inițiale | E1a/E1b fixe, electronice cu date reale ulterior, fără motor universal anticipat. |

Decizii care pot continua fără clarificări: stiva locală, taxonomia inițială, layout mobil, parsere snapshot, motorul conservator, import manual/CSV/UBL și testele. Dependențe de obținut ulterior: documente reale pentru OCR, validarea atributelor lipsă, acceptări comerciale, provider/auth/producție, regiune/retention finală și pragurile de utilitate economică ale fiecărei firme. Aceste lipsuri nu condiționează livrarea planului sau E1a.

## 10. Checklist de preluare pentru orice agent

### Înainte de cod

- [ ] Citește AGENTS, handover și README, apoi secțiunile de plan și validare relevante; păstrează sursele și probele.
- [ ] Confirmă prin inspecție starea checkoutului; aplicația și repository-ul există deja. Păstrează modificările locale.
- [ ] Verifică E0/E1a ca baseline; ținta recomandată este **E1b**, dacă utilizatorul nu cere altă prioritate. Nu implementa simultan toate etapele.
- [ ] Înregistrează hashurile probelor și comenzile baseline; nu executa downloadul vechi peste `probe-data`.
- [ ] Verifică executabilele reale și folosește setupul și lockurile existente; `.venv` este în rădăcină. Dacă instalarea este indisponibilă, raportează exact blocajul, fără a înlocui aplicația printr-un demo fals.

### În timpul implementării

- [ ] Contracte pentru decimal/null, scope, provenance, timp, relații de matching și completeness înainte de UI de rezultate.
- [ ] Import idempotent cu stări și audit; mapare categorie conservatoare; `source_only` vizibil.
- [ ] Detectează Jacobs Intense/Alintaroma și ambiguitatea Unit înainte de badge-uri de economie.
- [ ] Construiește fluxul D1 complet și verifică-l în browser mobil; înregistrează capturile relevante și rezultatul, fără a expune date private.
- [ ] Adaugă E1b numai după G1a: draft/confirmat, CSV/UBL, duplicate, revizii și scenarii economice.
- [ ] Afișează capabilitățile neconfigurate cinstit; fără prețuri, facturi, OCR sau recomandări fabricate.

### Verificări executabile

Comenzi **existente acum**, din rădăcina proiectului, PowerShell7:

```powershell
.\tests\Test-MonitorPricesParser.ps1
```

`scripts/Test-MonitorPrices.ps1 -Offline` recalculează raportul și **scrie `probe-data/summary.json`**. Pentru verificarea fără modificarea probei originale, importă modulul read-only și folosește funcțiile direct sau rulează orchestratorul într-o copie temporară verificată a probelor. Fără `-Offline`, scriptul suprascrie și XML-uri prin download; nu îl folosi pentru importurile aplicației.

```powershell
Import-Module .\scripts\MonitorPrices.psm1 -Force
$catalogProbe = @(Read-MonitorCatalog -Path .\probe-data\catalog.xml)
$foodProbe = Read-MonitorPrices -Path .\probe-data\slatina-representative.xml -CatalogIds @('1012187','1013048','1361463')
$catalogProbe.Count
$foodProbe.ValidOfferCount
$foodProbe.CompleteBasketCount
```

Rezultate așteptate: 104794, 48, 15; ultima valoare înseamnă acoperire numerică a ID-urilor. Nu o interpreta drept identitate semantică verificată.

Comenzi **existente**, din rădăcină: `scripts/Setup-Local.ps1`, `scripts/Check-Local.ps1`, `scripts/Start-Local.ps1`, conform [README](../README.md). Setupul instalează dependențele fixate, construiește UI și importă probele; Check rulează parserul, regresiile Python și buildul. CLI-ul `app.cli` acceptă numai `seed` și `check`, ambele importând date; `migrate` și `import-snapshots` erau propuneri inițiale și nu există. Frontendul are `dev`, `typecheck`, `build`, `preview`, fără `test`/`test:e2e` în prezent. Nu se raportează instrumentele de test viitoare ca instalate ori executate. Implementatorul verifică exit code și se oprește între comenzi dependente la eroare.

- [ ] Rulează testele afectate, typecheck/build și scenariile browser relevante; nu prezenta „scris” drept „verificat”.
- [ ] Verifică hashurile probelor după lucru și declară orice diferență intenționată separat.
- [ ] Testează replay/idempotency, restart/recovery și corectarea unui rezultat deja salvat.
- [ ] Raportează funcțiile terminate, probele/testele, limitele reale și următoarea etapă precisă.
- [ ] Actualizează starea README și handover-ul. Implementarea locală poate continua în scope-ul cerut; publicarea și serviciile externe urmează autorizarea din sesiunea curentă. Publicarea acestui repository a fost solicitată explicit, fără a autoriza automat găzduire sau conturi de servicii.

## 11. Cum evaluăm dacă produsul merită extins

După E2/E3, pe cohorta reală se măsoară: timp până la prima listă comparabilă, proporția liniilor comparabile, numărul conflictelor corectate, timpul de revizie per factură, comparații cu cost complet și recomandări acceptate după verificare. Ținte inițiale de test, nu rezultate: mediană sub 3 minute pentru o listă recurentă de 10 produse; minimum 80% dintre participanți finalizează fluxul fără ajutor; cel puțin o oportunitate verificabilă relevantă în jumătate dintre firmele pilot. Dacă acoperirea sau efortul de revizie sunt slabe, restrângem categoria/sursele și îmbunătățim datele înainte de extindere.

Valoarea urmărită este o decizie de cumpărare mai bine justificată, nu un număr mare de oferte sau un procent spectaculos de economie fără bază comparabilă.

## 12. Verificarea planului la predare

Cele patru documente au trecut o revizie integrată și o verificare punctuală a remediilor: etape, moduri temporale, reguli Monitor/Lidl, `BaseQuantity`, discounturi globale, costuri comune, ștergere și izolarea pilotului. Cele 32 referințe locale dintre documente și probe se rezolvă; blocurile de cod au delimitări echilibrate, fără marcatori de lucru rămași sau caractere de înlocuire de encoding.

Verificarea read-only cu parserul existent a reprodus: 104.794 intrări de catalog, 12 nume goale, 48 cotații în subcoșul alimentar, 15 seturi complete la nivel de ID și minimul brut raportat de 33,86 lei. Nu s-a rescris `summary.json`. Cele 32 teste ale parserului sunt rezultatul consemnat în raportul inițial, nu o suită nouă executată pentru acest plan. La redactarea inițială nu exista o aplicație. Ulterior, publicarea din 6 octombrie a trecut setupul curat, cele 75 teste Python, 32 verificări ale parserului și buildul pe [GitHub Actions](https://github.com/cosmintrica/aplicatie-ionut/actions/runs/37392153976). OCR-ul și precizia comercială rămân criterii viitoare; acest baseline nu le certifică.
