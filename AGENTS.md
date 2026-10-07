# Instrucțiuni pentru agentul care preia proiectul

Citește întâi [docs/HANDOVER.md](docs/HANDOVER.md), apoi [README.md](README.md). Aceste instrucțiuni se aplică întregului repository.

## Stare și ordine de lucru

- Aplicația locală există: React/TypeScript/Vite + Python/FastAPI/SQLite. E0/E1a și revizia catalogului/comparațiilor sunt livrate ca flux offline. Nu reface aplicația de la zero.
- Următoarea etapă recomandată este E1b: achiziții confirmate, întâi un flux manual complet, apoi CSV/UBL. Citește criteriile și dependențele din [plan](docs/PLAN_IMPLEMENTARE.md). Cererea curentă a utilizatorului poate schimba prioritatea.
- Loginul, emailurile, OCR-ul, sursele live și producția pentru mai multe firme sunt planificate. Nu le prezenta ca implementate și nu le simula cu date comerciale inventate.
- Pentru comportamentul existent, citește codul, migrațiile, testele și [backend/SMART_CONTRACT.md](backend/SMART_CONTRACT.md). Arhitectura descrie și o destinație viitoare. Consemnează diferențele înainte să schimbi un contract.
- Întrebările anterioare despre meniurile Supabase nu aleg un furnizor pentru proiect. Continuarea locală nu cere conturi Supabase, credențiale sau servicii externe.

## Reguli de corectitudine și date

- Calculează banii și cantitățile în backend cu `Decimal`; în API sunt șiruri zecimale. `null` înseamnă necunoscut, nu zero. Nu calcula separat prețurile în JavaScript.
- Un ID de catalog sau similitudinea numelui nu confirmă identitatea comercială. Păstrează marca, varianta, ambalajul, baza prețului, proveniența și lipsurile; nu combina variante incompatibile.
- Coșul incomplet nu primește un total comparabil. Diferențele dintre estimări nu sunt economii realizate. Data importului nu actualizează data prețului din sursă.
- `probe-data` și `fixtures/snapshot-manifest.json` sunt baseline de integritate. Nu rescrie snapshoturile pentru a face teste să treacă. Datele noi au probe și manifest distincte.
- `scripts/Test-MonitorPrices.ps1 -Offline` rescrie `summary.json`; fără `-Offline` descarcă și înlocuiește probe. Rulează explorările într-o copie temporară. CLI-ul `app.cli check` execută tot importul, deci nu este verificare read-only.
- Păstrează baza existentă și listele utilizatorului. `var`, facturile, tokenurile, `.env`, cache-urile și dependențele instalate rămân în afara Git. Testele folosesc date izolate; documentele sintetice se etichetează.
- Migrațiile SQLite sunt în `backend/app/migrations`. Adaugă o migrație nouă când schimbi schema; nu edita sau redenumi o migrație deja aplicată, verificată prin SHA-256.
- Serverul rămâne pe loopback până la îndeplinirea E4. Nu activa hosting, servicii plătite, trimitere de documente sau emailuri către terți fără autorizarea corespunzătoare.

## Implementare și verificări

- Inspectează Git și sursele înainte de editare; păstrează schimbările altor persoane. Folosește dependențele fixate și evită o restructurare generală pentru o funcție punctuală.
- Comenzile de referință, din rădăcină în PowerShell 7: `scripts/Setup-Local.ps1`, `scripts/Check-Local.ps1`, `scripts/Start-Local.ps1`. Pașii și runtime-urile sunt în handover.
- Pentru cod modificat, rulează verificările relevante; pentru un flux de aplicație, rulează `Check-Local.ps1` și verifică în browser. Pentru documentație, verifică linkurile, comenzile și consistența; nu declara teste rerulate fără execuție.
- Actualizează handover-ul și starea README când livrezi o etapă. Raportează separat implementat, verificat, rămas și blocaje reale.
- Textele interfeței și documentația sunt în română, clare și explicabile. Folosește cratime obișnuite; nu introduce em dash sau en dash. Păstrează utilizabilitatea cu tastatura și pe ecrane de 320/390 px.
- Publicarea respectă [docs/PUBLICARE.md](docs/PUBLICARE.md). Pe checkoutul inițial, cele trei diferențe de metadate documentate nu sunt modificări de prețuri; nu le include din greșeală într-un commit.
