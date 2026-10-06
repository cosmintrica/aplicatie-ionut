# Motorul de corectitudine: produse, costuri, facturi și recomandări

Stare: specificație pentru implementare, redactată la 5 octombrie 2026. Pragurile de mai jos sunt decizii inițiale de produs care trebuie validate, nu rezultate deja obținute. Acest document nu afirmă că există deja un motor de potrivire, OCR ori optimizare.

Se citește împreună cu [specificația produsului](SPECIFICATIE_PRODUS.md), [arhitectura](DECIZII_ARHITECTURA.md) și [planul de implementare](PLAN_IMPLEMENTARE.md). Dovezile locale sunt [cererea inițială](../CERERE_INITIALA.md), [cerințele extinse](CERINTE_EXTINSE.md), [raportul de testare](../RAPORT_TESTARE.md), [validarea identității datelor](VALIDARE_IDENTITATE_DATE.md), [parserul Monitorul](../scripts/MonitorPrices.psm1), [testele parserului](../tests/Test-MonitorPricesParser.ps1) și snapshoturile originale din `probe-data`. [Cercetarea Compari.ro](CERCETARE_COMPARI.md) explică lecțiile din documentația publică; regulile de aici sunt deciziile produsului nostru, nu afirmații despre algoritmul intern Compari. Exemplele sintetice din acest document nu sunt oferte comerciale.

Aliniere cu livrarea: E1a afișează și compară cotațiile din snapshoturi; E1b introduce achiziții manuale/CSV/UBL, revizie și calcule conservatoare; E2 adaugă PDF cu text, ingestie activă delimitată și coș împărțit între maximum două magazine în domeniul limitat definit mai jos; E3 adaugă OCR real și evaluarea sa; E4 deschide funcțiile pentru firme multiple în producție numai după verificările de securitate și surse; E5 extinde electronicele și optimizarea generală a coșurilor, inclusiv scala și mai mult de doi furnizori. Regulile complete de mai jos definesc destinația, fără a încărca E1a cu toate funcțiile. Stiva aleasă folosește Python `Decimal` pentru calculele server; React afișează rezultatele și nu le recalculează cu `Number` drept autoritate monetară.

## 1. Reguli care nu pot fi ocolite de un scor sau de AI

1. O cotație este o observație cu proveniență; nu dovedește un checkout, un stoc sau un preț disponibil oricărei firme.
2. Identitatea produsului, interpretarea prețului și eligibilitatea ofertei sunt verificări distincte. O potrivire corectă nu repară o bază de preț necunoscută.
3. `necunoscut`, `neaplicabil`, `zero confirmat`, `negativ` și `absent` sunt valori diferite. Necunoscutul nu se convertește implicit în zero, fals sau compatibil.
4. Un atribut critic în conflict blochează eticheta „produs identic”, indiferent de GTIN, nume, ID de catalog sau scor AI. Un atribut critic lipsă produce revizie ori abținere.
5. Relația „echivalent pentru această nevoie” este condiționată de cererea utilizatorului. Nu rescrie identitatea globală a produselor.
6. Ofertele condiționate de card, cantitate, contract, adresă sau firmă sunt eligibile numai dacă acele condiții sunt confirmate; altfel se afișează separat.
7. Economiile folosesc aceleași cantități, aceeași monedă, aceeași bază fiscală și același domeniu de cost. Costurile omise se afișează lângă rezultat.
8. Un coș incomplet nu primește total complet. Un coș cu toate prețurile produselor, dar cu transport/SGR necunoscut, nu primește „total de plată verificat”.
9. Textul extras din factură nu este automat dată confirmată. Modelul poate propune, dar nu poate inventa un câmp lipsă, o cotă TVA ori o ofertă.
10. Fiecare decizie și fiecare calcul trebuie reproduse din intrări versionate. Corectarea unui produs sau a unei facturi invalidează rezultatele dependente; nu modifică retroactiv dovezile originale.

## 2. Ce demonstrează probele și ce trebuie restrâns

| Observație verificată local | Consecință pentru implementare |
|---|---|
| 104.794 înregistrări de catalog, 12 fără nume | Catalogul este spațiu de căutare; numărul nu este număr de produse comparabile ori de oferte actuale. Numele gol intră în carantină. |
| Slatina: 18 magazine; București: 19 în probele selectate | Acoperirea rezultatelor se raportează la acele cereri geografice, nu la întreaga țară. |
| Cotațiile pozitive utilizabile din Monitorul au data textuală `05.10.2026 04:00` | Se păstrează data declarată de sursă separat de momentul descărcării. Snapshoturile sunt etichetate „date salvate din 5 octombrie 2026”. |
| `Price=0` și dată absentă apar pentru linii indisponibile | Nu sunt produse gratuite și nu intră în clasamente. Absența cotației nu dovedește absența din magazin. |
| `Basketprice` poate include numai o parte dintre articole | Se recalculează din liniile eligibile. Totalul serverului rămâne câmp de diagnostic. |
| `Catprod.Id` și `Product.Id` au roluri diferite | Primul identifică poziția din catalogul sursei, al doilea produsul comerciantului; niciunul nu devine GTIN ori ID canonic global. |
| Laptele are `L`, `Litru`, `BUC`, `BUCATA`; cafeaua de 250 g are inclusiv `K`, `Kg`, `250g`, `BUC` | Se păstrează separat unitatea sursei, cantitatea ambalajului și baza de tarifare. Nu se împarte prețul la gramaj înainte de validarea bazei. |
| Sub `Catprod.Id=1013048`, catalogul spune „ALINTAROMA”, dar unele denumiri comerciale includ „INTENSE” | Nu se decide din aceste cuvinte nici că sunt sigur identice, nici că sunt sigur diferite. Se marchează contradicție potențială de variantă și se cere evidență/revizie. |
| În XML, Ariel `1449689` apare în categoria `LAPTE`, iar Fairy `1282436` în `DEZINFECTANTI` | Categoria brută nu devine automat categoria canonică; conflictul nume/categorie intră la revizie. Aceste rânduri nu au cotații utilizabile în probe. |
| Câmpul `Promo` este gol în toate cele 148 de rânduri profilate în validarea identității | Starea promoției/condiției rămâne necunoscută; nu se convertește la `false` sau la „fără card”. |
| Parserul dă 15 coșuri complete pentru cele trei ID-uri alimentare | Sunt coșuri complete la nivelul cotațiilor pe ID. Validarea semantică și completitudinea costurilor sunt etape suplimentare. |
| Lidl: 2.444 rânduri, 34 categorii; fără GTIN/SKU, stoc, TVA ori valabilitate pe articol | Rândul are identitate de import și proveniență, nu identitate universală. Data fișierului nu devine dată de valabilitate. |
| Lidl are opt rânduri suplimentare cu aceeași cheie nume + gramaj | Duplicatele se inspectează, nu se înlocuiesc automat cu cel mai mic preț. |
| Cele 32 teste existente validează parserul | Nu sunt măsurarea preciziei potrivirii, a OCR ori a recomandărilor. Se păstrează și se adaugă verificări distincte. |

Exemplele de denumiri contradictorii sunt vizibile în [summary.json](../probe-data/summary.json): Store `778`, „CAFEA INTENSE 250G JACOBS”, și Store `7528`, „JACOBS KRONUNG INTENSE 250G”. Parserul păstrează alternativele comerciale și calculează minimul per ID de catalog, cu un comentariu explicit despre necesitatea verificării unității/ambalajului. Acest comportament rămâne util pentru reproducerea probei, dar nu este algoritmul final de achiziție.

## 3. Catalogul: niveluri și categorii

### 3.1 Nivelurile care trebuie păstrate separat

- **Marcă**: identitate canonică și aliasuri aprobate, cu limbă/sursă. `Kronung`/`Krönung`/`Kroenung` pot fi aliasuri de căutare; acest lucru nu echivalează toate subgamele.
- **Familie de produs**: o linie comercială ori un model; ajută navigarea, fără să fie unitate cumpărabilă.
- **Variantă**: combinația atributelor care schimbă produsul efectiv: formulă, procent, model, RAM, capacitate etc.
- **Ambalaj vândut**: cantitate netă, unitate, număr componente și nivel logistic; de exemplu `6 × 1 l`, nu doar `6 l`.
- **Articol al sursei**: identificator și denumire nemodificate, cu observații versionate. Un SKU este unic numai în domeniul comerciantului/feedului documentat.
- **Ofertă**: articol + furnizor/magazin + preț/bază + condiții + timp + proveniență. Condiția bunului, garanția și accesoriile incluse se verifică și aici.
- **Cerință de cumpărare**: ce cere firma, ce atribute sunt obligatorii, cantitatea și substituțiile acceptate. Se separă de catalog și de istoricul achizițiilor.

Un pachet cu 250 g și unul cu 500 g pot aparține aceleiași variante, dar au ambalaje și de regulă articole comerciale diferite. Două laptopuri cu același nume de familie și RAM diferit sunt variante diferite. „Nou” și „recondiționat” sunt oferte cu condiții distincte chiar dacă modelul hardware este identic; motorul nu le amestecă în compararea standard.

### 3.2 Taxonomie inițială și atribute decisive

Taxonomia se declară de la început pentru toate domeniile de mai jos. Disponibilitatea în UI se bazează pe produse și surse verificate; crearea categoriilor nu pretinde că există deja oferte. Primele reguli activate sunt lapte, cafea și apă; consumabilele existente în Lidl pot fi căutate și revizuite, fără substituție automată cu alte mărci.

| Categorie | Atribute critice pentru identitate/comparabilitate | Atribute utile suplimentare |
|---|---|---|
| Alimente → lactate → lapte | marcă, linie, specie/bază, procent grăsime, lactoză/fără lactoză, tratament când e declarat și relevant, aromă, volum, număr recipiente | bio declarat, cerință de păstrare, termen dacă există |
| Alimente → cafea | marcă, gamă, boabe/măcinată/instant/capsule, decofeinizată, amestec declarat, gramaj, număr unități; sistemul capsulelor când se aplică | măcinare, intensitate declarată, origine; nu deducem gustul ori calitatea |
| Băuturi → apă | marcă, gamă/tip declarat, plată/carbogazoasă, aromă, volum pe recipient, număr recipiente, tip ambalaj când cererea îl constrânge | SGR verificat la nivel de ambalaj/ofertă, eligibilitate retur |
| Curățenie → detergenți | utilizare, marcă, gamă, formulă/concentrație, formă, cantitate; compatibilități/sensibilități cerute | număr de spălări numai când e declarat și cu aceeași metodă de dozare |
| Igienă → hârtie | utilizare, număr straturi, material declarat, role/pachete, foi pe rolă ori lungime | dimensiune foaie; comparația pe foaie cere dimensiuni comparabile |
| Birotică → hârtie imprimantă | format, gramaj g/m², tip/culoare, număr coli, compatibilități declarate | certificări numai cu dovadă |
| Consumabile imprimare → toner/cerneală | cod producător, original/compatibil/remanufacturat, tehnologie, culoare, imprimante compatibile explicit, capacitate/randament și standardul declarat | cip/firmware/regiune, garanție ofertă, retur |
| Electronice → laptop/desktop | producător, model și cod complet de configurație, CPU, RAM, stocare/tip, GPU unde există, ecran relevant, OS inclus, configurație/regiune | tastatură, accesorii, alimentare; condiție bun și garanție obligatorii pentru comparare ofertă |
| Electronice → telefon/tabletă | producător/model exact, RAM dacă există variante, stocare, conectivitate, regiune/rețea, configurație SIM relevantă | culoare conform preferinței; condiție/garanție/accesorii |
| Alte domenii | categorie separată și schemă proprie înainte de activarea echivalențelor | produsele neclasificate rămân căutabile, dar fără comparație automată pe unitate |

Regula pentru atribute opționale: „necunoscut” nu blochează orice afișare. Blochează acea concluzie pentru care atributul este necesar. De exemplu, lipsa culorii unui laptop poate fi acceptată de cererea firmei, dar lipsa RAM nu permite eticheta „aceeași configurație”. Lista atributelor critice se versionează per categorie și relație de potrivire.

Nu implementăm o ontologie universală. Se folosesc coduri stabile de categorie, atribute tipizate, vocabular restrâns pentru câmpurile decisive și câmpuri originale pentru dovadă. Categoria sursei se mapează la categoria noastră fără a o pierde. Numele, codurile și atributele pot semnala un conflict de categorie; categoria internă nu se alege doar fiindcă sursa o declară sau un model o propune. Exemplul Ariel/LAPTE trebuie trimis la revizie înainte de orice regulă specifică laptelui.

## 4. Relațiile dintre două produse

| Cod de relație | Condiție | Etichetă în UI | Intră în coș automat? |
|---|---|---|---|
| `IDENTICAL_PACK` | aceeași variantă și același ambalaj; atributele decisive sunt verificate, fără conflict | Același produs și ambalaj | Da, dacă oferta este eligibilă și baza prețului verificată |
| `SAME_VARIANT_OTHER_PACK` | aceeași variantă, ambalaj diferit, conversie fizică validă | Același produs, alt ambalaj | Numai dacă cererea permite alt ambalaj; se afișează surplusul |
| `FUNCTIONAL_EQUIVALENT` | produs diferit, dar satisface toate cerințele acceptate de utilizator | Alternativă compatibilă cu cerințele tale | Numai după acceptare explicită pentru cererea respectivă |
| `SUGGESTION` | asemănare ori utilizare posibilă, cu informații insuficiente | Sugestie de verificat | Nu |
| `INCOMPATIBLE` | contradicție cu cel puțin un atribut obligatoriu | Nu corespunde: motiv concret | Nu |
| `UNRESOLVED` | dovezi insuficiente ori contradictorii | Asociere neconfirmată | Nu |

Nu există tranzitivitate automată între echivalențe funcționale: A potrivit pentru cererea X și B potrivit pentru cererea Y nu implică A = B. Relația de alt ambalaj nu ignoră restricțiile de utilizare: 12 sticle de 500 ml și trei sticle de 2 l au același volum, dar pot fi incompatibile cu servirea individuală cerută de firmă.

## 5. Pipeline de potrivire implementabil

### 5.1 Pașii și dovezile

1. **Păstrare original**: salvează numele, ID-urile, câmpurile, locația din fișier/răspuns și hashul observației. Normalizarea creează câmpuri noi.
2. **Normalizare lexicală**: Unicode, spații, majuscule, diacritice pentru căutare; punctuația relevantă pentru modele, zecimale, procente și `6x1L` se păstrează în tokeni structurați. Nu elimina `Pro`, `Plus`, `XL`, `Intense`, `1,5%`, `II`, `Gen 2`, sufixe de model sau `fără`.
3. **Extragere deterministă**: parser pentru cantități/procente/multipack, dicționar de branduri/aliasuri aprobate, patternuri per categorie, GTIN și coduri de model. `500 ml = 0,5 l`; `500 g` nu se transformă în ml fără densitate explicită și fără motiv de produs.
4. **Generare candidați**: referințe aprobate de sursă, GTIN valid, marcă + model, apoi căutare lexicală. Pentru MVP: maximum 20 candidați per rând pentru scor/revizie. Indexurile restrâng după categorie; un model vectorial este opțional ulterior, exclusiv pentru recuperare de candidați.
5. **Filtre stricte**: categorie incompatibilă, procent/model/capacitate incompatibilă, conflict GTIN, compatibilitate toner diferită, ambalaj neinterpretabil sau contradicție de formulă → respinge relația respectivă ori trimite la revizie. Nici similaritatea textuală, nici un model nu pot anula filtrul.
6. **Clasificare relație**: evaluează separat identic, alt ambalaj și echivalent pentru cerere. Produce câmpuri confirmate, lipsuri și conflicte.
7. **Decizie/revizie**: aplică ruta și pragurile de mai jos. Salvează explicația verificabilă, nu doar un scor.
8. **Utilizare**: calculatorul primește numai relații permise de cerere și decizii active. Asocierea acceptată nu validează automat transportul, TVA, stocul ori valabilitatea.

### 5.2 Identificatori și conflicte

- GTIN rămâne șir de caractere, cu zerourile inițiale. Se validează lungimea/checksumul; validarea matematică nu dovedește că sursa l-a atribuit corect.
- Același GTIN cu 250 g versus 500 g, 8 GB versus 16 GB ori procent diferit produce `identifier_conflict`; ambele înregistrări rămân inspectabile. Nu alegem „sursa majoritară” și nu unim automat.
- GTIN diferit nu dovedește singur incompatibilitatea: pot exista revizii de ambalaj. Necesită evidență și mapare aprobată; nu se deduce din simpla asemănare.
- Codul producătorului are domeniu `producător + categorie/model`. SKU are domeniu `sursă + comerciant + SKU`, conform contractului sursei. `Catprod.Id` are domeniu Monitorul și rol de candidat; nu este GTIN.
- O mapare aprobată pentru `(sursă, comerciant, SKU, fingerprint semantic)` se poate reutiliza numai dacă fingerprintul atributelor decisive și semantica ambalajului nu s-au schimbat. Prețul nou nu rupe maparea; schimbarea titlului/gramajului/modelului declanșează reevaluarea.
- La Lidl, indexul rândului identifică dovada din acel fișier. Nu devine SKU stabil între fișiere; ordinea se poate schimba. Cheia nume + gramaj este candidat de deduplicare, nu garanție de unicitate.

### 5.3 Scorul inițial de candidați și deciziile

Scorul euristic `candidate_score ∈ [0,100]` prioritizează revizia. Nu se afișează ca „95% sigur” și nu reprezintă probabilitate calibrată.

| Componentă | Punctaj maxim | Regulă inițială |
|---|---:|---|
| Marcă | 20 | 20 pentru marcă/alias aprobat identic, altfel 0 |
| Familie/model | 35 | 35 pentru cod/gamă exactă aprobată, 20 pentru candidat lexical fără conflict, 0 dacă lipsește |
| Atribute decisive, fără ambalaj | 25 | `25 × atribute egale confirmate / atribute necesare`; lipsa nu intră ca egalitate |
| Ambalaj interpretabil | 10 | 10 dacă structura este verificată pentru relația evaluată; altfel 0 |
| Asemănare lexicală rămasă | 10 | 10 × Jaccard al tokenilor normalizați relevanți; cuvintele critice rămân păstrate |

Punctajul se calculează după detectarea conflictelor. Un conflict explicit produce decizie blocată indiferent de total. Pentru o relație de alt ambalaj, cele 10 puncte cer cantități și niveluri logistice cunoscute, nu egalitatea gramajului.

| Rută/prag inițial | Decizie în prima etapă | Condiție pentru extindere |
|---|---|---|
| Mapare manuală activă, fingerprint neschimbat, toate câmpurile critice verificate | Reutilizare deterministă, jurnalizată | Monitorizare schimbări și posibilitate revocare |
| GTIN exact, toate câmpurile decisive compatibile și complete | Propunere de revizie în MVP | Automatizare numai pentru surse/categorii care trec gate-ul de evaluare |
| Scor ≥ 90, diferență ≥ 10 față de următorul candidat, câmpuri decisive complete | Candidat principal pentru revizie | Nu devine automatizare doar prin ridicarea scorului |
| Scor 70-89 sau diferență < 10 | Revizie comparativă, maximum 3 candidați în UI | Solicită câmpul care separă candidații |
| Scor < 70 ori câmp decisiv absent | Abținere de la asociere; căutare/sugestie separată dacă e utilă | Date suplimentare sau regulă specifică verificată |
| Orice conflict decisiv | Blocat cu motiv; nu recomandă cumpărarea ca identic | Revizie cu dovadă nouă; nu override fără audit |

La egalitate de scor, nu se alege produsul mai ieftin pentru a „rezolva” identitatea. Mai întâi se rezolvă identitatea, apoi se compară prețul.

Asistența AI, dacă se configurează ulterior, primește numai câmpurile necesare, returnează un obiect validat prin schemă, candidați din catalog și fragmente de evidență. Poate propune marcă, categorie, atribut sau explicație. Nu creează SKU/GTIN/prețuri și nu oferă verdict final de identitate. Textul comercial și textul din documente sunt date, niciodată instrucțiuni pentru model. La lipsă API, timeout, răspuns invalid sau buget epuizat, pipeline-ul determinist și revizia manuală continuă.

### 5.4 Revizia și efectul corecțiilor

Revizorul vede două produse, câmpurile originale, atributele extrase, sursa/data, ambalajul, conflictul și opțiunile: confirmă identic, confirmă alt ambalaj, acceptă alternativă pentru cerere, respinge sau lasă nerezolvat. Confirmarea cere motiv/evidență pentru câmpurile critice neclare. În MVP, citirea numelui nu transformă o bază de preț ambiguă în fapt verificat; se poate salva doar o presupunere de scenariu, etichetată și exclusă din recomandările ferme.

Se păstrează actor, firmă/domeniu, versiunea regulii, timestamp, dovezi, înainte/după și relația anulată. Confirmarea unui utilizator dintr-o firmă rămâne privată dacă se bazează pe facturi/contracte; promovarea unei mapări globale cere revizie pe dovezi publice ori autorizate. Nu se expun altor firme prețuri negociate sau exemple de facturi prin motorul comun.

Revocarea unei mapări marchează rezultatele dependente drept depășite și declanșează recalcul. Rezultatul istoric salvat rămâne în audit, cu motivul invalidării.

### 5.5 Cazuri obligatorii

| Intrări | Rezultat cerut |
|---|---|
| Aceeași cafea, aceeași gamă/formă, 250 g și 500 g | `SAME_VARIANT_OTHER_PACK`, dacă atributele și baza prețului sunt confirmate; niciodată `IDENTICAL_PACK` |
| Cafea boabe vs măcinată; cafea standard vs decofeinizată | Incompatibil pentru identitate; alternativă numai când cererea acceptă explicit diferența |
| „Kronung Alintaroma” vs „Kronung Intense” sub același ID | `UNRESOLVED`, conflict potențial de gamă; nu decide doar după ID |
| Lapte 1,5% vs 3,5%, inclusiv Zuzu vs Pilos din probe | Produse diferite; alternativa cere relaxarea explicită a procentului și a mărcii |
| 6 × 1 l vs 1 × 6 l | Volum egal, ambalaj diferit; verifică numărul de recipiente cerut |
| Toner același nume de familie, imprimante compatibile diferite | Blocat; nu se inferează compatibilitatea din prefixul codului ori forma cartușului |
| Toner original vs compatibil, aceeași imprimantă | Alternativă funcțională, niciodată identic; randamentul nu se presupune egal |
| Laptop același model de familie, 8/256 vs 16/512 | Variante diferite; RAM/stocare sunt diferențe explicite |
| Același model/configurație, nou vs recondiționat | Clasamente de ofertă separate; utilizatorul trebuie să accepte condiția |
| Același model/configurație, garanție absentă vs garanție declarată | Lipsa nu se completează din alt magazin; comparație condiționată ori neeligibilă pentru cerința de garanție |
| Cod GTIN comun și gramaje contradictorii | Carantină de identitate; scorul nu deblochează |

## 6. Măsurarea corectitudinii și porți de lansare

### 6.1 Setul de evaluare

Prima etapă are o suită deterministă și un set de revizie mic, nu o pretenție de precizie statistică pentru piață. Se pregătesc minimum 120 perechi etichetate: 40 pozitive verificate, 40 negative dificile și 40 cu date lipsă/conflicte; în plus toate exemplele reale de unități și variante din probe. Se includ toate categoriile în teste sintetice de blocare, chiar dacă numai cele trei categorii alimentare au cotații în demo. Etichetele sintetice și cele observate sunt distincte.

Fiecare pereche are sursă, categorie, relație așteptată, atribute decisive, raționament, dovadă, etichetator și adjudecare. Înainte de automatizarea extinsă se construiește un set de calibrare și un holdout separat. Același produs/SKU/ambalaj, variantele sale aproape identice și aparițiile sale repetate în magazine nu se distribuie între antrenare/calibrare și holdout. Repetarea aceluiași lapte la 16 magazine nu echivalează cu 16 exemple independente de identitate.

Pentru autorizarea unei rute automate într-un domeniu delimitat: cel puțin 600 decizii automate evaluate pe holdout independent, reprezentative pentru acea rută, cu categorii/surse și cazuri dificile raportate separat; dacă datele disponibile nu permit acest set, ruta rămâne în revizie. Aceste 600 nu pot fi obținute prin duplicarea ofertelor aceluiași produs.

### 6.2 Metrici și praguri inițiale

- `precision_auto = asocieri automate corecte / toate asocierile automate evaluate`; raport separat pentru identic și alt ambalaj.
- `false_merge_critical`: fuziuni care ignoră un atribut critic. Ținta de lansare este zero în suitele de blocare și zero observate în holdoutul folosit la aprobare.
- `recall_candidates@20`: câte potriviri corecte cunoscute apar între cei maximum 20 candidați; țintă inițială ≥ 95% pe setul etichetat relevant. Recuperarea slabă nu justifică relaxarea identității.
- `auto_coverage`: proporția rândurilor eligibile rezolvate automat. Se publică intern împreună cu precizia; fără prag minim care să forțeze asocieri nesigure.
- Rată de abținere, rată de revizie, minute de revizie/100 rânduri, corecții după acceptare și drift pe categorie/sursă.
- Gate automatizare: precizie observată ≥ 99,5% și limita inferioară Wilson la 95% ≥ 99%, plus zero erori critice observate. Se calculează intervalul, nu se afirmă din scoruri. Cu 600/600 corecte, limita inferioară este aproximativ 99,36%; cu puține date nu se poate demonstra aceeași limită.
- Pentru fiecare categorie activată se raportează și mărimea efectivă a eșantionului; categoria insuficient evaluată rămâne în revizie chiar dacă totalul agregat trece gate-ul.
- Acceptările utilizatorilor nu sunt automat adevăr de referință. Eșantionarea independentă trebuie să includă confirmări grăbite și relații respinse.

Niciun procent de mai sus nu este deja măsurat în proiect. Pentru demo este acceptabilă acoperire automată foarte mică, cu mapări curate și explicații precise.

### 6.3 Degradare sigură

La prima eroare critică confirmată se dezactivează automatizarea pentru regula/sursa/categoria afectată, se marchează rezultatele dependente și se cere revizie. Nu se oprește fără motiv întregul catalog. Se păstrează ultima observație validă ca istoric, dar nu se prezintă drept ofertă actualizată. Schimbarea unei scheme de feed sau a unui vocabular critic cere rerularea suitei și un eșantion de revizie înainte de reactivare.

## 7. Contractul calculului monetar

### 7.1 Reprezentare, monedă și rotunjire

Se folosește aritmetică zecimală exactă sau întregi cu scară explicită; niciodată `float` binar pentru bani. API-ul și dovezile păstrează sume ca șiruri zecimale cu monedă. Cantitățile pot avea mai mult de două zecimale; prețul pe kg/l nu se rotunjește înainte de înmulțire. Nu se pierde precizia prețului unitar din factură.

Pentru estimările în RON, regula de aplicație este rotunjire la 0,01, jumătățile în sus (`ROUND_HALF_UP`) la pasul documentat. Este o regulă de estimare a produsului, nu afirmație despre obligația fiscală a unui comerciant. Documentul fiscal importat păstrează sumele declarate și politica identificată; dacă politica este necunoscută, aplicația arată diferența și nu rescrie factura pentru a impune propria regulă.

O politică de calcul versionată declară: scara monedei, ordinea reducerilor, nivelul rotunjirii (linie/grup/total), includerea taxelor și proveniența. Nu însuma valori deja rotunjite doar pentru afișare. Valoarea de afișare a economiei procentuale se rotunjește după calculul diferenței monetare.

MVP compară RON cu RON. Pentru altă monedă, rezultatul rămâne separat până când există curs, sursă, dată și politică de conversie explicită; nu se inventează un curs și nu se ascunde riscul valutar.

### 7.2 Baza prețului și cantitățile

Fiecare ofertă are `price_basis = per_sellable_pack | per_piece | per_mass | per_volume | unknown`, împreună cu `basis_quantity`, `basis_unit`, ambalaj și dovada interpretării. `Unit=Kg` lângă un nume „250g” nu este suficient pentru a stabili dacă 23,99 reprezintă pachetul ori kilogramul. În acest caz se poate afișa „23,99 lei raportat de sursă; baza necesită confirmare”, fără lei/kg calculat automat.

Pentru cerere în cantitate fizică minimă `Q`, ambalaj cu conținut utilizabil confirmat `q` și vânzare în pachete întregi:

```text
n = ceil(Q / q)
cantitate_cumpărată = n × q
surplus = cantitate_cumpărată − Q
cost_produse = costul tarifat pentru n pachete, după condițiile aplicabile
preț_normalizat = preț_pachet / q       # numai pentru informare și comparații admise
```

Cantitatea disponibilă, pasul de comandă și multiplii logistici pot schimba `n`. Dacă sursa nu oferă stoc numeric, nu afirmăm că se pot comanda `n` pachete; rezultatul este cotație de cost, cu disponibilitate neconfirmată.

Cererea permite explicit unul dintre: număr exact de articole, cantitate fizică minimă, sau cantitate cu surplus maxim acceptat. Nu se mărește coșul pentru a obține un preț/kg mai mic fără a afișa suma de plătit și surplusul. Nu amortizăm surplusul în „economia actuală”; o eventuală utilizare viitoare este scenariu separat.

### 7.3 TVA, taxe și reduceri

- Pentru fiecare sumă se păstrează `VAT_included`, `VAT_excluded` sau `VAT_unknown`; cota/valoarea sunt opționale și vin din document/sursă verificată.
- Nu se atribuie automat o cotă după categorie, data curentă sau ceea ce „se aplică de obicei”. Acest plan nu prescrie cote fiscale.
- Când sunt cunoscute baza `N` și cota declarată `r`, `TVA = round(N × r)` conform politicii documentului; dacă este cunoscut brutul `G` și cota, `N = G/(1+r)` înainte de rotunjirea adecvată. Cota necunoscută nu se rezolvă ghicind din preț.
- Compararea standard folosește sume de plătit cu taxe incluse numai când baza este confirmată. Se poate compara separat valoarea publicată, cu eticheta „bază TVA neconfirmată”, fără economie netă contabilă.
- „Cost după recuperarea TVA” se activează numai pentru date și tratament confirmate de firmă; aplicația nu decide deductibilitatea. TVA deductibilă necunoscută nu este economie.
- Reducerile pe linie, pe coș și cupoanele au domeniu, condiții, plafon și cumulabilitate. Nu le cumulăm implicit. Reducerea deja inclusă în preț nu se scade din nou.
- Prețul negociat importat este privat, specific firmei și perioadei/contractului confirmate. O factură veche dovedește un preț istoric, nu că acel preț negociat se poate obține azi.
- Cardul de fidelitate are stare `confirmat`, `neconfirmat`, `nu are`; apartenența nu se deduce din faptul că oferta are un badge promoțional. O ofertă condiționată poate fi comparată ca scenariu separat.

### 7.4 SGR, transport și alte costuri

SGR se păstrează ca element distinct: aplicabilitate, sumă pe recipient, număr recipiente, inclus/exclus/neclar în preț și dovadă. Faptul că pagina Lidl declară excluderea garanției nu dovedește aplicabilitatea la fiecare rând și nu furnizează singur suma pe recipient. Nu se adaugă o valoare implicită tuturor băuturilor.

Garanția returnabilă intră în suma de numerar la achiziție când este confirmată. Se arată separat scenariul de cost după o restituire efectivă sau presupusă explicit; o rambursare viitoare nu se scade automat din suma de plătit. Identitatea recipientului și eligibilitatea returului nu se deduc doar din volum.

Transportul se calculează per comandă/furnizor/adresă/mod de livrare și aplică pragurile confirmate. Distanța returnată de sursă nu este distanță de rută, tarif de curier sau cost/km. Costul deplasării poate fi introdus de utilizator ca ipoteză; timpul nu se monetizează fără valoare aleasă. Ridicarea personală nu înseamnă automat cost zero: UI poate afișa „cost deplasare exclus de utilizator”.

Minimum de comandă și prag de transport gratuit sunt condiții de fezabilitate. Motorul nu adaugă produse necerute pentru a le atinge; poate propune explicit cantitatea suplimentară și cere acceptare. Taxele de manipulare, taxele de plată ori alte costuri intră numai dacă sunt documentate și aplicabile.

### 7.5 Formulele rezultatului

```text
subtotal_produse = Σ cost_linie_confirmată
total_numerar = subtotal_produse − reduceri_neincluse + taxe_neincluse
                 + SGR_neinclus + transport + alte_costuri_confirmate
```

Fiecare componentă are stare și proveniență. `total_numerar` este numeric complet numai dacă toate componentele necesare în scenariul ales sunt cunoscute ori confirmate neaplicabile. În rest se returnează subtotalul și componentele cunoscute, lista necunoscutelor și, doar când există limite justificate, un interval. Un cost neprecizat nu primește arbitrar intervalul `[0,0]`.

Chiar cu toate componentele cunoscute, eticheta este „Total calculat pentru condițiile declarate”, până la un checkout ori document efectiv. Stocul și disponibilitatea pentru cantitatea cerută sunt stări separate. Aritmetica completă nu transformă o cotație informativă într-o promisiune de vânzare.

## 8. Coșuri, împărțire între magazine și limitele optimizării

### 8.1 Trei dimensiuni de completitudine

Rezultatul are trei câmpuri separate:

1. `quote_coverage`: câte linii au măcar o cotație utilizabilă în sursa/scenariul analizat;
2. `product_coverage`: câte linii au relație acceptată, ambalaj și bază de tarifare valide, în cantitatea cerută;
3. `cost_completeness`: taxe, garanții, transport și condiții cunoscute pentru scenariu.

`product_coverage` este agregatul de prezentare; contractul API detaliază separat `semantic_coverage` și `quantity_coverage`, conform arhitecturii. Se păstrează în plus eligibilitatea, prospețimea și disponibilitatea. O reducere la trei indicatori vizibili nu elimină aceste verificări interne.

Criteriul de cotație utilizabilă este specific adaptorului: pentru Monitorul, data prețului validă este obligatorie conform probei; pentru fișierul Lidl se păstrează o observație cu moment de colectare și valabilitate individuală necunoscută. Nu inventăm `Pricedate` pentru Lidl și nu-i promovăm observația în ofertă actuală garantată. Un rezultat poate număra rândurile citite din fișier, dar separă câte sunt comparabile în scenariul temporal cerut.

Un rezultat poate fi `3/3 cotații`, `2/3 produse validate`, `cost incomplet`. UI nu comprimă aceste stări în simplul „complet”. „Disponibil” se rezervă informației de stoc confirmate; „are cotație” este formularea pentru sursele care nu confirmă stocul.

Fiecare rezultat include linii satisfăcute, linii lipsă, substituții acceptate, cantități cumpărate, surplus, condiții și necunoscute. Procentul liniilor acoperite este separat de procentul valorii istorice acoperite; o linie de 500 lei nu are aceeași contribuție la cheltuială ca una de 5 lei.

### 8.2 Ordinea implementării

**Mai întâi, coș într-un singur magazin:** în E1b/E2 se fixează o ofertă și un ambalaj eligibil pentru fiecare linie-magazin în scenariul analizat, apoi se tarifează cantitățile și se evaluează împreună condițiile de coș, reducerile și transportul. Rezultatul este „variantă calculată”, nu automat „minimul în magazin”. Alegerea celui mai mic preț pe linie urmată de recalcularea transportului nu garantează minimul dacă există cupoane, reduceri pe subset, praguri sau alte ambalaje. Ofertele respinse ori ambalajele neconfirmate nu contribuie la totalul comparabil. Păstrează raportarea separată a cotațiilor brute, ca să se poată reproduce probele.

Scenariile fixate explicit de utilizator sunt distincte de preselecția făcută de motor. Dacă motorul lasă alte oferte/ambalaje/scenarii relevante neevaluate, rezultatul rămâne `optimality=heuristic`; dacă doar tarifează un scenariu ales, fără sarcină de optimizare, este `not_applicable`. `exact_within_scope` se folosește numai când toate opțiunile din domeniul declarat au fost enumerate sau când se optimizează o repartizare în domeniul fixat explicit, fără a extinde afirmația la alegerea ofertelor ori a ambalajelor. O versiune delimitată poate enumera toate scenariile admise și apoi compara costurile complete; nu este necesar un solver general pentru E1b/E2.

**În E2, coș împărțit:** maximum două magazine în prima versiune cu împărțire, numai la cererea/acceptarea utilizatorului. Evaluează combinațiile magazinelor eligibile și repartizarea liniilor, folosind costul complet per comandă. Pentru maximum 10 linii și maximum 10 magazine candidate, fiecare linie are în acest mod un produs/ambalaj aprobat și o ofertă eligibilă per magazin. Enumerarea tuturor atribuirilor per pereche înseamnă maximum `45 × 2^10 = 46.080` atribuiri, înainte de eliminarea celor imposibile; se includ și cele 10 coșuri dintr-un singur magazin. Preselecția ofertelor cu condiții diferite nu se face doar după preț: se fixează scenariul eligibil pentru firmă. Variantele, ambalajele și magazinele excluse se raportează, astfel că exactitatea este numai în acest domeniu fixat.

Combinarea mai multor gramaje pe aceeași linie este extensie separată: se generează planuri de ambalare cu limite explicite de surplus/cantitate și se evaluează toate planurile admise înainte de declararea unui minim în acel domeniu. Exemplul 250 g + 500 g de mai jos este un test pentru această extensie; versiunea care nu o implementează trebuie să spună că nu a analizat combinații de gramaje. Nu se numește minim global rezultatul unei preselecții euristice.

Nu se folosește doar minimul independent pe articol când există praguri de transport, reduceri pe coș, minimum de comandă, multipli de ambalaj sau stoc limitat. În versiunea delimitată se enumeră atribuirile și apoi se tarifează fiecare coș complet; condițiile neliniare sunt evaluate la final pentru fiecare candidat. O condiție pe care motorul nu o poate evalua face scenariul condiționat, nu ieftin prin omitere.

Pentru coșuri mai mari, E2 păstrează clasamentul pe magazin și afișează că optimizarea împărțirii nu este disponibilă. E5 poate extinde scala, domeniul de variante și numărul de furnizori printr-un solver, păstrând același contract și testele. O euristică poate veni numai cu eticheta „variantă găsită”, nu „minim garantat”.

„Cel mai mic total calculat” este permis numai în domeniul finit enumerat complet, cu aceleași condiții și costuri cunoscute. Dacă ofertele/ambalajele au fost preselectate de motor și alte scenarii relevante nu au fost evaluate, se afișează „variantă calculată”, chiar dacă repartizarea între magazine a fost enumerată exact după preselecție. Rezultatul păstrează `solver`, versiune, număr magazine/oferte/candidați analizați, originea selecției scenariului, limite, timp, `optimality = exact_within_scope | heuristic | not_applicable`. Nu se afirmă optimul întregii piețe ori al tuturor traseelor.

### 8.3 Exemple sintetice obligatorii pentru calculator

Toate valorile din această secțiune sunt **sintetice**, alese pentru teste; nu descriu magazine sau cote fiscale reale.

**A. Gramaj și surplus:** aceeași cafea este 24,00 lei/250 g și 44,00 lei/500 g, cu baza de preț verificată. Pentru minimum 750 g și fără alte costuri:

- trei pachete de 250 g: 72,00 lei, exact 750 g;
- două de 500 g: 88,00 lei, 1.000 g, surplus 250 g;
- unul de 500 g și unul de 250 g, dacă se pot combina în scenariu: 68,00 lei, exact 750 g.

Pachetul mare are 88,00 lei/kg, iar cel mic 96,00 lei/kg. Minimul lei/kg singur ar recomanda greșit plata a 88,00 lei pentru nevoia curentă, dacă se omite suma și combinația fezabilă. Dacă cererea este exact „3 pachete de 250 g”, numai prima variantă respectă cererea.

**B. Rotunjire:** trei unități la prețul net declarat 3,335 lei dau bază de linie 10,005 lei, rotunjită conform politicii sintetice la 10,01. Rotunjirea mai întâi a prețului la 3,34 și apoi înmulțirea ar produce 10,02, deci politica trebuie explicitată. Nu se atribuie TVA în acest exemplu.

**C. TVA cunoscut dintr-un document fictiv:** baza 100,00 lei și cota declarată în fixture `r=0,10` dau taxă 10,00 și brut 110,00. Aceasta nu este o cotă recomandată pentru România. Dacă oferta alternativă este 105,00 cu bază fiscală necunoscută, nu se declară economie de 5,00; se cere clarificarea bazei.

**D. SGR fictiv:** șase recipiente la 4,00 lei/bucată și garanție explicită în fixture de 0,40 lei/recipient, exclusă din preț, dau produse 24,00, garanție 2,40, numerar 26,40. Valoarea 0,40 este artificială pentru test, nu informație despre SGR real. O rambursare ulterioară neconfirmată nu reduce numerarul calculat.

**E. Transport și coș împărțit:** magazinul A are produsele X/Y la 10/30 lei și transport 5; B le are la 14/20 și transport 6. Total A = 45, B = 40; minimul pe produse împărțit este 10 + 20 = 30, dar cu ambele transporturi devine 41. Recomandarea corectă pentru costul scenariului este B, 40, nu coșul împărțit. Dacă transportul A este necunoscut, împărțirea are subtotal cunoscut 36 + transport A și nu poate primi automat primul loc.

**F. Prag cantitate:** prețul este 12,00/bucată pentru 1-5 și 10,00/bucată pentru minimum 6. O cerere de 5 costă 60,00; cumpărarea a 6 costă tot 60,00 dar produce surplus 1. Motorul nu pretinde economie de 10,00 raportând cele cinci bucăți la prețul inaccesibil de 10,00.

## 9. Economii: trei comparații care trebuie separate

### 9.1 Baza comună

O comparație păstrează un baseline explicit: document/linie sau coș salvat, data, cantitatea și unitatea, produs/variantă/ambalaj, reducerile, baza TVA, garanțiile, transportul inclus/exclus și proveniența. Fără această bază, se poate arăta diferență între valori afișate, nu „ai economisit”.

**Reduceri globale:** alocarea automată este permisă numai când sunt cunoscute valoarea reducerii, baza ei și toate liniile eligibile. Se distribuie proporțional valorii nete după reducerile de linie, între **toate** liniile eligibile ale documentului, inclusiv cele neasociate la catalog: `alocare_i = reducere_globală × net_i / Σ net_eligibil`. Pentru o reducere pozitivă și baze nenegative cu sumă strict pozitivă, se calculează cu `Decimal`, se alocă întâi partea întreagă în bani fiecărei linii, apoi banii rămași se distribuie în ordinea descrescătoare a resturilor fracționare, cu egalități rezolvate prin identificatorul stabil al liniei originale. Suma alocărilor trebuie să fie exact reducerea; politica și alocările se păstrează în analiză, fără rescrierea documentului. Dacă reducerea este deja inclusă în sumele liniilor, nu se alocă din nou. Domeniul eligibil/baza fiscală necunoscute, suma bazelor zero ori documentele mixte cu credit/avans complex cer revizie, fără alocare automată. Alegerea unui subset pentru comparație nu redistribuie asupra lui reducerea aferentă restului facturii.

**Transport și alte costuri comune:** o comparație de cost total cere același coș acoperit și costurile logistice reale/documentate ale scenariilor respective. Pe un subset al facturii se afișează numai diferențele de produse, cu costul comun exclus explicit din ambele părți; nu se declară economie totală și nu se presupune că renunțarea la câteva articole economisește integral transportul. O alocare analitică introdusă și acceptată de utilizator poate fi păstrată ca ipoteză separată, cu metodă și sumă, dar nu devine cost de checkout dovedit.

**Fixture sintetic:** două linii eligibile au valori nete după reducerile de linie de 60,00 și 40,00 lei; reducerea globală este 10,00 lei. Alocările sunt 6,00 și 4,00 lei, iar neturile pentru comparație devin 54,00 și 36,00 lei. Dacă numai prima linie este asociată la catalog, baseline-ul ei rămâne 54,00 lei; nu se scade întreaga reducere de 10,00 din ea.

```text
economie_absolută = cost_referință_comparabil − cost_alternativ_comparabil
economie_procentuală = 100 × economie_absolută / cost_referință_comparabil
```

Formula procentuală se aplică numai dacă referința este strict pozitivă. Diferența negativă rămâne negativă și se descrie ca un cost suplimentar; nu se taie la zero. Liniile necomparabile nu intră nici în numărător, nici în baza procentului, iar acoperirea se arată explicit. Nu se aplică procentul găsit la întreaga cifră de cumpărături a firmei.

### 9.2 Tipurile de rezultat

| Tip | Intrări | Formulare permisă | Formulare interzisă |
|---|---|---|---|
| Comparație istorică | achiziție confirmată și ofertă cu evidență de aplicabilitate la data achiziției | „Diferență față de oferta documentată atunci”, cu toate condițiile | „Puteai sigur cumpăra mai ieftin” dacă eligibilitatea/stocul nu sunt demonstrate |
| Estimare pentru o cumpărare curentă | achiziție trecută ca referință și cotație curentă verificată/etichetată | „La prețurile observate acum, aceeași cantitate ar costa cu X mai puțin”, cu data și limitele | „Ai pierdut X atunci” ori „ai economisit deja” |
| Diferență după achiziție | factură/comandă nouă confirmată și baseline fixat înaintea deciziei, aceleași cantități/costuri | „Diferență constatată pentru achiziția confirmată față de referința aleasă” | Economie efectiv plătită dacă există doar o ofertă ori plata nu este confirmată |

Dashboardul poate avea „Economii estimate” și „Economii validate prin achiziții”, dar definiția celei de-a doua trebuie să fie vizibilă: diferență față de referința salvată, pe achiziții confirmate, nu dovadă că aplicația a cauzat economia. „Plătit” se folosește numai cu informație de plată confirmată; o factură dovedește în primul rând suma facturată. Retururile, stornările și anulările reduc/anulează indicatorul și rămân legate de documentele originale.

Un istoric de prețuri se construiește din observații păstrate. Nu se reconstruiește un preț trecut din cotația de azi sau din data ultimei modificări a fișierului. Nu se compară retrospectiv coșul din octombrie cu o ofertă din altă lună sub eticheta „economie ratată”.

### 9.3 Exemplu sintetic și exemplu din probe

**Sintetic:** factura confirmată indică 10 unități identice, cost comparabil 120,00 lei. Pentru aceeași cantitate, oferta curentă are produse 100,00 și transport aplicabil 8,00: total 108,00, estimare 12,00 lei, 10%. Dacă garanția/transportul de referință nu pot fi separate ori baza TVA diferă, se raportează comparația numai pe componentele confirmate, nu 10% economie totală. O ofertă de acum nu dovedește că firma putea obține 108,00 la data facturii.

**Probă reală, limitată:** în snapshotul Slatina, subtotalurile raportate pentru cele trei ID-uri sunt 33,86 lei Supeco și 41,07 lei Kaufland. Diferența aritmetică este 7,21 lei, aproximativ 17,56% din 41,07. Aceste numere reproduc cotațiile din probă. Nu sunt economii efective sau totaluri de checkout; relația produs/variantă, baza prețului și componentele suplimentare trebuie confirmate. Pentru 42,87 lei Carrefour Aleea Muncii există și denumirea de cafea „INTENSE”, deci nu afirmăm automat identitate cu varianta din celelalte magazine.

## 10. Recomandări de furnizor bazate pe dovezi

Recomandarea are trei niveluri:

1. **Observație:** „Am găsit o cotație mai mică pentru 2 din 5 produse; transportul nu este cunoscut.” Nu îndeamnă la schimbare.
2. **Propunere de verificat:** „Pentru următorul coș, furnizorul B ar putea reduce costul cu X; confirmă condițiile marcate.” Poate cere ofertă/validare utilizatorului, fără a trimite mesaje în numele său.
3. **Recomandare pentru o achiziție delimitată:** toate liniile cerute sunt satisfăcute prin relații acceptate, costurile necesare sunt cunoscute, condițiile sunt accesibile firmei, iar diferența rămâne pozitivă în scenariul conservator. Se recomandă cumpărarea acelui coș ori un test limitat, nu abandonarea întregii relații comerciale.

O propunere de schimbare recurentă a furnizorului cere suplimentar un istoric confirmat al firmei și evidență repetată a ofertei: minim trei achiziții relevante în istoricul analizat și minim trei observații distincte ale alternativei pe cel puțin 14 zile, ca prag inițial de produs. Aceste praguri sunt o precauție de produs, nu demonstrația statistică a stabilității. Acoperirea istorică a articolelor și cheltuielii analizate se arată; minimum 90% din cheltuiala relevantă comparabilă permite o recomandare pentru acel grup de articole, iar restul rămâne explicit exclus. Pentru întreaga relație cu furnizorul, condițiile și articolele omise trebuie rezolvate; altfel recomandarea rămâne limitată la grupul verificat.

Recomandarea păstrează baseline, calcul pe linii, transport/comandă minimă, eventuale beneficii contractuale pierdute, termen de plată/livrare când firma le consideră obligatorii, data, sursele, limitele și motivul. O singură factură nu justifică eticheta „furnizor scump”. Recenziile, ratingurile ori promisiunile logistice ale magazinului nu devin „furnizor de calitate” fără metodă și evidență; MVP nu atribuie asemenea etichete.

Nu estimăm volum anual dintr-o singură factură. Dacă utilizatorul confirmă recurența, estimarea viitoare arată orizontul și ipoteza de cantitate, separat de economiile validate.

### 10.1 Sensibilitate și criteriu de emitere

Se arată pragul la care recomandarea se inversează. Pentru economie pe produse `S` și cost suplimentar necunoscut `x`, diferența este `S − x`; avantajul există numai dacă `x < S`. Dacă există intervale dovedite, economia conservatoare este `cost_referință_min − cost_alternativ_max`. Fără limită justificată pentru un cost, nu se inventează interval.

**Exemplu sintetic:** avantajul produselor este 40,00 lei/coș. Costul suplimentar de livrare/deplasare confirmat într-un interval 15-30 și costul de tranziție alocat de utilizator de 5 dau avantaj 5-20 lei. Dacă limita superioară a transportului este necunoscută, aplicația afișează „avantaj înainte de transport 40 lei; recomandare de schimbare neconfirmată”, nu economie minimă pozitivă.

Pragul operațional pentru a evidenția o schimbare este inițial avantaj conservator de cel puțin 20 lei/coș și 5% din baseline comparabil, ambele îndeplinite. Este o regulă de relevanță pentru evitarea sugestiilor mărunte, nu un prag de adevăr; utilizatorul poate vedea toate diferențele, inclusiv sub prag. Nu confundăm depășirea pragului cu validarea produselor sau a disponibilității.

## 11. Contractul importului și OCR

### 11.1 Moduri de intrare și disponibilitate onestă

| Intrare | Procesare planificată | Comportament fără infrastructură OCR |
|---|---|---|
| XML structurat | parser UBL pentru subsetul explicit implementat în E1b, câmpuri și validări; păstrarea originalului | Funcționează local pentru formatele implementate; format necunoscut → eroare explicată; nu promite validare fiscală ANAF |
| CSV în E1b; text introdus/fișier text în E2 | parser explicit, mapare coloane și previzualizare | Funcționează local când parserul este implementat; ambiguitățile se corectează înainte de confirmare |
| PDF cu strat de text în E2 | extragere locală a textului, poziții/pagini dacă biblioteca permite, apoi structurare | Nu se numește OCR; text absent ori inutilizabil → necesită OCR |
| PDF scanat/fotografie JPEG/PNG | adaptor OCR real configurat, cu text/poligoane/confidence și proveniență | Status „OCR neconfigurat”; păstrează documentul pentru revizie manuală numai cu opțiunea utilizatorului; nu generează linii fictive |
| PDF mixt | extragere text per pagină; OCR numai pentru paginile care îl cer, fără duplicare | Identifică paginile neprocesate și blochează importul ca document complet |

În E3, primul candidat evaluat este adaptorul local Tesseract, dacă runtime-ul este configurat; un furnizor extern este opțional. Nici instalarea Tesseract, nici selecția unui furnizor extern nu sunt efectuate de acest plan. Orice adaptor trebuie să îndeplinească același contract de extragere, validare și evidență; schimbarea motorului cere reevaluare.

Nu există în director facturi reale ori un corpus OCR etichetat demonstrat. Testele inițiale de import pot folosi documente sintetice marcate vizibil. Ele verifică pipeline-ul și aritmetica, nu demonstrează acuratețea pe facturile clienților. Nu folosim date sintetice drept rezultat al unui OCR care nu a rulat.

### 11.2 Etape și stări

```text
uploaded → validated → extracting → extracted → needs_review
         → confirmed → matched → comparison_ready
```

Stările de eroare sunt distincte: fișier neacceptat, prea mare, protejat prin parolă, format invalid, document trunchiat, lipsă text, OCR neconfigurat, OCR eșuat, timeout, pagini lipsă, aritmetică neconformă, posibil duplicat. OCR eșuat nu devine document gol confirmat. Reîncercarea este idempotentă și nu creează achiziții duplicate.

### 11.3 Trei straturi de date

1. **Original imuabil:** fișier/hash, nume sigur, tip detectat, dimensiune, pagini, moment import, firmă și permisiuni.
2. **Extragere:** text original, câmp propus, valoare normalizată, motor/versiune, pagină și bounding box sau cale XML/coloană, confidence furnizat de motor, alternative/erori, transformări aplicate. Nu se rescrie când utilizatorul corectează.
3. **Date confirmate:** identitatea documentului și furnizorului, data/moneda, linii, cantități, unități, preț, reducere, taxe, subtotal/total, status de confirmare pe câmp/linie/document, actor și timestamp. Legătura spre extragerea inițială rămâne.

Confirmarea de document nu confirmă implicit potrivirea fiecărei linii la catalog. O linie poate avea suma și cantitatea confirmate, dar produsul nerezolvat; poate intra în istoricul de cheltuieli, însă nu în economii pe produse comparabile.

Confidence OCR este semnal furnizat de motor, necomparabil automat între furnizori și diferit de scorul de matching. Confidence lipsă rămâne lipsă. Verificarea aritmetică reușită nu înseamnă automat că descrierea, codul produsului sau toate paginile sunt corecte.

### 11.4 Praguri de revizie inițiale

În MVP, orice document importat cere confirmare explicită înainte de a alimenta achizițiile efective. Câmpurile obligatorii fără valoare sau cu ambiguitate blochează confirmarea pentru domeniul afectat. Nu este obligatoriu să cunoaștem TVA pentru a păstra o sumă brută confirmată, dar fără baza fiscală necesară nu se produce comparație netă.

Dacă motorul OCR oferă confidence pe scara 0-1 documentată: sub 0,90 pentru cantitate, sumă, monedă, dată, identificator sau sub 0,80 pentru descriere → evidențiere obligatorie pentru revizie. Peste prag nu elimină confirmarea și nici verificările. Aceste praguri sunt inițiale și se calibrează pe corpusul local; nu se prezintă ca acuratețe garantată. Motoarele cu altă scală nu sunt convertite arbitrar.

**Gate G3 pentru OCR asistat în E3:** setul inițial cuprinde minimum 60 documente/600 linii și minimum 6 layouturi de furnizor, inclusiv fotografii dificile; 15 documente sunt ținute separat pentru evaluarea finală. Layouturile și duplicatele apropiate nu se împart între calibrare și test. Pe setul ținut separat se cer minimum 95% exactitate a câmpurilor numerice esențiale înainte de corectură, 100% din neconcordanțele aritmetice ale setului semnalate și zero facturi neconfirmate folosite în economii. Câmpurile lipsă/greșite și documentele ilizibile ori cazurile de abținere rămân raportate și în numitorul aplicabil; se publică separat rezultatele per format/dificultate. Pragurile nu înlocuiesc confirmarea utilizatorului. Dacă nu sunt atinse, funcția rămâne „scanare asistată în evaluare”.

**Gate separat, numai pentru eventuala confirmare automată viitoare:** se cer metrici pe câmp, linie și document, pe cel puțin 100 documente ținute în afara calibrării, cu furnizori/layouturi diferite și fotografii dificile, plus criterii de autorizare a automatizării stabilite și validate separat. Cele 100 documente nu sunt o condiție pentru livrarea OCR asistat în E3 și nici suficiente singure pentru automatizare. Orice sumă eronată acceptată automat este incident critic. Până la evaluare și gate separat, confirmarea manuală rămâne obligatorie.

### 11.5 Validarea aritmeticii

Pentru fiecare linie, numai dacă semantica documentului o permite:

```text
cantitate_în_unitatea_bazei = conversie_verificată(cantitate, unitate_cantitate, unitate_bază_preț)
bază_linie = (cantitate_în_unitatea_bazei / price_basis_quantity) × PriceAmount
             − reduceri_linie + majorări_linie
taxă_linie/grup = baza declarată × cota declarată, rotunjită prin politica documentului
total_factură = Σ baze + Σ taxe + costuri − reduceri_globale ± ajustări_declarate
```

`price_basis_quantity` este cantitatea strict pozitivă la care se referă `PriceAmount`; unitatea sa trebuie cunoscută și compatibilă cu cea a cantității facturate. Dacă baza este ambiguă sau conversia lipsește, se cere revizie și verificarea liniei rămâne neconcludentă. Cititorul poate folosi valoarea implicită 1 numai când schema/sursa suportată documentează explicit acel implicit; această regulă și versiunea ei intră în proveniență. Nu se atribuie 1 unei baze necunoscute pentru a obține un total.

**Fixture sintetic de bază de preț:** 20 bucăți, `PriceAmount=50,00 RON`, `price_basis_quantity=100 bucăți`, fără ajustări, dau `(20 / 100) × 50,00 = 10,00 RON`. Calculul `20 × 50,00 = 1.000,00` trebuie respins ca interpretare greșită. O cantitate în baxuri cere întâi conversie verificată în bucăți; fără numărul confirmat de bucăți/bax nu se poate recalcula linia.

Se diferențiază prețul per 1/10/100 unități, cantitatea de ambalaje și cantitatea fizică, valoarea unitară de valoarea liniei și totalul documentului de suma de plată după avansuri. Reducerea globală nu se aplică din nou dacă liniile sunt deja nete. Transportul și SGR pot fi linii separate; nu se clasifică drept produse comparabile.

Pentru verificarea inițială, toleranța tehnică este maximum 0,01 RON per egalitate de linie și maximum 0,01 RON rezidual neexplicat la totalul documentului. Toleranța nu se multiplică automat cu numărul de linii. O diferență mai mare poate fi validă dacă documentul declară o ajustare/rotunjire ori o altă politică, dar necesită interpretare și revizie; nu se modifică un preț pentru a forța potrivirea totalului. Se păstrează `difference`, `rule`, `tolerance`, câmpurile folosite și rezultatul.

`1.234,56`/`1,234.56`, `O/0`, `I/1`, semnul minus pierdut, procentul și separatorul de mii sunt ambiguități explicite. Contextul și aritmetica pot genera alternative, nu corecții silențioase. Dacă două interpretări sunt aritmetic valide, decide utilizatorul. Stornările/credit notes și retururile se păstrează cu tip/semn și legătură la original; prețurile negative din aceste documente nu sunt oferte comerciale negative.

O linie zero dintr-o factură confirmată poate reprezenta un bonus ori o reducere și nu se elimină prin regula parserului de cotații Monitorul. Tipul documentului și evidența decid tratamentul; baseline zero nu produce economie procentuală. Distincția previne reutilizarea greșită a validării `Price > 0` asupra tuturor datelor contabile.

### 11.6 Corecții, duplicate, securitate

Revizia prezintă documentul lângă câmpul editabil, sursa exactă și recalcul imediat. Modificarea cantității/prețului/ambalajului recalculează verificările și invalidează asocierile dependente. Se poate salva ciornă; datele incomplete nu se pierd și nu sunt afișate ca achiziție confirmată.

Duplicatul exact se detectează prin hash în aceeași firmă. Un duplicat logic se propune prin furnizor + număr + dată + monedă + total, cu posibilitate de document corectiv; nu se șterge automat. Același document în două firme nu expune existența fișierului celeilalte firme.

Fișierele se validează prin conținut/tip, dimensiune și limite de pagini/resurse; extensia nu este suficientă. XML nu permite DTD/entități externe; procesarea nu urmărește linkuri/QR și nu execută macrocomenzi ori instrucțiuni din document. Erorile și logurile tehnice nu includ integral factura sau date personale. Transmiterea către OCR extern se face numai după configurarea explicită a furnizorului și a fluxului autorizat pentru documentele firmei; reîncercările nu schimbă furnizorul pe ascuns.

## 12. Contractele de ieșire și trasabilitatea

Acestea sunt contracte logice; denumirile SQL și schema finală sunt în arhitectură.

**Rezultat matching:** ID-uri originale/canonice, relație, rută, scor euristic opțional, versiuni parser/reguli, dovezi, atribute egale/lipsă/conflictuale, status `proposed/approved/rejected/revoked`, domeniu firmă/global, actor, timestamp și fingerprint semantic.

**Rezultat cost:** cererea originală și versiunea ei, ofertele exacte, cantități/ambalaje, reduceri, taxe, garanții, transport, condiții, fiecare componentă cu statut/proveniență, politică zecimală/rotunjire, total complet sau subtotal, necunoscute, surplus și moneda.

**Rezultat comparație:** baseline fixat, scenariu alternativ, relațiile acceptate, acoperire pe linii și valoare, diferență monetară și procent, tip istoric/curent/după achiziție, limite de valabilitate și motivul abținerii.

**Rezultat recomandare:** toate referințele precedente, domeniul exact al recomandării, condițiile demonstrate, sensibilitate, prag aplicat, limita optimizării, data dovezilor și evenimente de invalidare.

**Rezultat extragere:** document/hash, motor/versiune, pagină/zonă sau cale, text brut, câmp/valoare propusă, confidence original, operații de normalizare, validări, decizia utilizatorului și versiunea datelor confirmate.

Se păstrează separat `observed_at` (descărcare), `source_price_time_raw`, timp interpretat și regula/fusul orar folosit, `valid_from/to` dacă există, `confirmed_at`, `computed_at`. XML-ul local nu exprimă singur un offset; dacă adaptorul presupune Europe/Bucharest, presupunerea este explicită și versionată, nu prezentată ca metadată primită de la sursă. Data fișierului Lidl nu se copiază în `valid_from`.

Un replay cu aceleași intrări, reguli și politică de calcul produce același rezultat. O recalculare cu oferte sau reguli noi creează o versiune nouă, cu diferență inspectabilă. Reproducerea extragerii depinde de păstrarea originalului conform politicii de retenție: după ștergere, interfața spune „original șters”, fără a pretinde că dovada poate fi deschisă sau OCR-ul reluat. Reproducerea aritmeticii rămâne posibilă numai pentru intrările structurate care sunt încă păstrate legitim; ștergerea datelor private are prioritate față de comoditatea auditului.

## 13. Suite de verificare pentru implementare

### 13.1 Regresii pe probele reale

| Test | Intrare | Rezultat obligatoriu |
|---|---|---|
| R01 | catalog XML salvat | 104.794 înregistrări; 12 fără nume; nu le numim oferte |
| R02 | Slatina trei produse inițiale | 18 magazine, 54 linii, 5 cotații utilizabile, zero coșuri complete pe ID |
| R03 | Slatina șapte ID-uri | 126 linii, 65 cotații utilizabile, zero coșuri complete pe ID |
| R04 | București șapte ID-uri | 19 magazine, 133 linii, 73 cotații utilizabile, zero coșuri complete pe ID |
| R05 | lapte separat vs în lot Slatina | aceleași 16 cotații pe magazin/preț/data sursei |
| R06 | cele trei ID-uri alimentare | 48 cotații, 15 coșuri complete pe ID; statusul semantic nu derivă automat din aceste numere |
| R07 | subtotaluri brute | 33,86/41,07/42,87 reproduse ca valori raportate; nicio etichetă checkout/live/economie efectivă |
| R08 | `Price=0`, dată goală, preț invalid/negativ | exclus din cotațiile utilizabile, motiv păstrat; nu „gratuit” |
| R09 | `Basketprice` parțial și ID comerciant ≠ catalog | total recalculat; ID-ul comerciantului nu selectează un ID de catalog |
| R10 | cafea 250 g cu `K/Kg` și denumiri `INTENSE` | interpretare de preț și identitate cer revizie; niciun lei/kg automat nejustificat |
| R11 | ID Borsec fără cotație vs ID asemănător cu cotații | nu se transferă ofertele automat între ID-uri |
| R12 | Lidl JSON/XLSB salvat | 2.444 rânduri, 34 categorii, 8 duplicate suplimentare inspectabile; valabilitate/GTIN/stoc necunoscute păstrate |
| R13 | Pilos 3,5% vs Zuzu 1,5% | niciodată același produs; nicio economie implicită prin substituție |
| R14 | eșec refresh simulat | ultima dovadă rămâne istoric; timestampul comercial nu este rescris cu ora refreshului |
| R15 | Ariel `1449689` în `LAPTE`, Fairy `1282436` în `DEZINFECTANTI` | conflict de categorie; fără mapare internă automată bazată doar pe categoria sursei |
| R16 | `Promo` gol în rândurile profilate | condiție necunoscută, fără inferență „preț fără card” |
| R17 | Jacobs 500 g `1019036` vs 250 g `1013048` | ambalaje distincte; familia comună nu completează varianta lipsă și nu validează baza prețului |
| R18 | `Brand=Jacobs Douwe Egberts` | candidat contextual; fără alias global automat companie→marcă pentru toate produsele |

R01-R18 sunt cerințe pentru implementarea viitoare; citirea raportului nu dovedește că noua aplicație le trece. Cele 32 verificări PowerShell existente rămân baza parserului, nu substitutul acestor teste de produs.

### 13.2 Teste sintetice care dovedesc comportament

- Matching: toate cazurile din secțiunea 5.5, aliasuri, diacritice, modele cu sufix, conflict GTIN, SKU reutilizat, lipsa atributelor, egalitate scor, revocarea unei mapări și protecția între firme.
- Unități: `250g`, `0,25kg`, `6x1L`, `8x200Foi`, `buc`, cantitate lipsă, preț per 100 unități, conversie interzisă masă→volum, păstrarea cantității exacte cerute.
- Bani: toate exemplele din secțiunea 8.3; rotunjire de linie vs unitară; TVA necunoscut; card neconfirmat; discount deja inclus; SGR necunoscut; transport per comandă; stornări; monede diferite.
- Coșuri: magazin incomplet foarte ieftin nu bate unul complet; coș împărțit cu transport dublu; prag minimum; cantitate insuficientă; costuri necunoscute; aceeași linie nu se numără de două ori; opțiune echivalentă neacceptată nu intră.
- OCR/import: text/XML valid și invalid, PDF fără text, PDF mixt, OCR neconfigurat/eșuat, cantitate `1O` ambiguă, separator zecimal, document aritmetic consistent cu produs greșit, pagină lipsă, duplicat, corecție și audit, total cu avans, retur/storno, XML cu entități externe respins.
- Proprietăți ale calculului: reordonarea liniilor nu schimbă totalul; repetarea aceluiași import nu dublează cheltuiala; conversia g↔kg păstrează cantitatea; adăugarea unei linii fără preț nu poate micșora un total complet; mărirea cererii nu reduce costul decât când o condiție explicită de tarif justifică acel salt.
- Economii: procent numai la baseline pozitiv, diferență negativă păstrată, comparație curentă ≠ istorică, linii necomparabile excluse transparent, stornare reduce indicatorul, recalcul cu ofertă nouă nu rescrie analiza istorică.
- Recomandări: cost suplimentar necunoscut produce abținere; pragul de rentabilitate corect; un singur snapshot nu declanșează recomandare recurentă; ratinguri fără evidență nu apar.

## 14. Checklist de preluare pentru chatul de implementare

- [ ] Păstrează snapshoturile și parserul de probă ca dovezi; noua aplicație poate importa copii cu hash, fără să suprascrie fișierele existente.
- [ ] Implementează întâi valorile necunoscute, proveniența și cele trei niveluri de completitudine; UI și calculatorul folosesc același contract.
- [ ] Adaugă taxonomia și schemele atributelor; activează comparația doar pe domeniile revizuite.
- [ ] Construiește importul local al datelor salvate; afișează data snapshotului și „cotație raportată”, inclusiv când deschiderea are loc în aceeași zi.
- [ ] Reproduce numeric probele fără a promova minimele per ID în identități canonice sau checkouturi.
- [ ] Implementează normalizarea, extragerea unităților și revizia; păstrează conflictul Jacobs și ambiguitățile `K/Kg` vizibile.
- [ ] Implementează biblioteca de bani/cantități și testele matematice înaintea indicatorului de economii.
- [ ] Livrează coșul pe magazin, subtotalurile și lipsurile; în E2, împărțirea delimitată între două magazine, cu costuri complete și limite de optimizare vizibile. Solverul general, scala extinsă și mai mult de doi furnizori rămân în E5.
- [ ] Livrează ciorne și confirmare manuală pentru achiziții, import text/XML și PDF text după biblioteca aleasă; fotografiile au OCR real numai când adaptorul este configurat.
- [ ] Păstrează extras/confirmat separat, validează aritmetica și oferă corecții cu audit înainte de matchingul facturilor.
- [ ] Salvează baseline și scenariu pentru fiecare comparație; separă istoric, estimare curentă și achiziție confirmată.
- [ ] În demo, recomandările sunt observații și scenarii limitate; pragurile pentru recomandări recurente nu sunt îndeplinite de snapshoturile existente.
- [ ] Extinde matchingul automat numai după evaluare ținută separat și gates per rută/categorie; altfel păstrează revizia și abținerea.
- [ ] Verifică toate restricțiile între firme la document, preț negociat, mapare privată, cache și explicație de recomandare.
- [ ] La predare raportează separat: teste parser trecute, teste motor noi trecute, date revizuite efectiv și funcții dependente de servicii/configurare. Nu anunța precizie OCR ori matching fără măsurare.
