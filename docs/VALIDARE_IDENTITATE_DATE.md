# Validarea identității produselor și a datelor

Data analizei: 5 octombrie 2026. Analiză exclusiv offline; nu s-au făcut cereri către surse externe.

## Concluzia pentru proiectare

Monitorul Prețurilor oferă o asociere între produse comerciale și un catalog comun, dar același `Catprod.Id` nu demonstrează întotdeauna aceeași variantă comercială. În datele reale, catalogul pentru cafea Jacobs Alintaroma 250 g include și denumiri explicite Intense. Compararea automată trebuie să păstreze această incertitudine.

Putem confirma că o ofertă este asociată de sursă unui anumit ID de catalog, într-un anumit magazin, la o anumită dată. Din aceste fișiere nu putem confirma un SKU identic între magazine printr-un GTIN sau prin documentația producătorului. Laptele, cafeaua de 500 g și apa au candidați cu atribute compatibile; și aceștia necesită verificarea atributelor lipsă și a bazei prețului înaintea unei promisiuni despre suma de plată.

## Fișiere analizate și limitele eșantionului

- `probe-data/summary.json`: rezultatele parserului, inclusiv `FoodBasket` și cazurile Slatina/București.
- `probe-data/slatina-representative.xml`: 18 magazine, eșantionul din raza de 5 km.
- `probe-data/bucharest-representative.xml`: 19 magazine, eșantionul din raza de 1 km.
- `probe-data/networks.xml`: numele rețelelor asociate ID-urilor.
- `probe-data/catalog.xml`: verificare suplimentară a numelor unor ID-uri apropiate.

Profilul de mai jos folosește numai cele patru ID-uri indicate. O cotație numărată ca validă are preț pozitiv și o dată prezentă și validă; aceasta nu reprezintă validarea identității SKU, a stocului sau a condițiilor comerciale.

| Catalog ID și denumire | Slatina: rânduri / cotații valide | București: rânduri / cotații valide |
| --- | ---: | ---: |
| `1012187` - ZUZU LAPTE 1.5% 1L | 18 / 16 | 19 / 19 |
| `1013048` - JACOBS KRONUNG ALINTAROMA 250G | 18 / 17 | 19 / 18 |
| `1019036` - JACOBS KRONUNG 500G | 18 / 17 | 19 / 18 |
| `1361463` - Borsec Apa plata 2l | 18 / 15 | 19 / 18 |
| Total | 72 / 65 | 76 / 73 |

Cele 138 de cotații valide au aceeași dată raportată: `05.10.2026 04:00`. În toate cele 148 de rânduri profilate, câmpul `Promo` este gol. Nu există exemple de promoții sau multipack-uri confirmate în acest eșantion. Câmpul gol trebuie păstrat ca informație necunoscută; nu demonstrează preț obișnuit, absența unei condiții de card sau absența unei promoții.

Coșul existent `FoodBasket` însumează lapte, cafea 250 g și apă: 48 de cotații valide, 15 magazine cu toate cele trei poziții. Totalurile Supeco 33,86 lei și Kaufland 41,07 lei sunt sume ale cotațiilor raportate. Ambiguitățile de variantă și de bază a prețului de mai jos împiedică prezentarea lor drept totaluri de plată validate.

## ID-uri și provenance

`Catprod.Id`, `Product.Id`, `Store.Id` și `Retailnetwork.Id` au roluri diferite. Toate se păstrează ca șiruri opace. `Product.Id` nu este demonstrat de aceste date ca EAN/GTIN sau cod de articol comun tuturor magazinelor. Valorile observate au 10 sau 11 cifre în Slatina și 11 în București. Același nume comercial poate avea ID-uri diferite în magazine din aceeași rețea; de exemplu laptele Profi are `10320293450` la magazinul `5188` și `10320458360` la `5394`. Stabilitatea acestor ID-uri în timp nu a fost testată.

Rețeaua se identifică prin ID și prin lista `networks.xml`. Unele `Retailnetwork.Name` din răspuns sunt numele magazinului, nu numele rețelei. Exemple: `4055329000008` este Lidl, deși numele din răspuns este `Slatina/Alexandru Ioan Cuza`; `5940475006709` este Carrefour, deși apare `MARKET SLATINA ALEEA MUNCII`; `5940475870003` este Mega Image, deși apare `MI REGINA MARIA`.

Cheia unei observații trebuie să includă sursa, magazinul, produsul din sursă, data prețului și momentul colectării. Ea nu trebuie confundată cu cheia internă a produsului canonic. Sunt necesare legături distincte pentru asocierea declarată de sursă, identitatea verificată și echivalența funcțională acceptată de utilizator.

## Exemple reale de identitate și conflict

### Lapte Zuzu 1,5%, 1 l - `1012187`

| Rețea / magazin exemplu | Product.Id | Denumire comercială | Brand / Unit | Observație |
| --- | --- | --- | --- | --- |
| Supeco / `7520` | `10690146476` | `LAPTE 1.5%GRS.1L ZUZU` | `ZUZU` / `L` | 6,09 lei; atributele din nume sunt compatibile cu catalogul. |
| Kaufland / `1418` | `10663980125` | `OUG ZUZU LAPTE SEMIDEGRESAT 1.5% 1L` | `Zuzu` / `BUC` | 6,69 lei; categoria comercială este `Lapte refrigerat`. |
| Penny / `1619` | `10587979923` | `ZUZU LAPTE 1,5%GRAS 1L` | gol / `BUCATA` | 6,69 lei; marca poate fi extrasă din nume ca sugestie. |
| Profi / `5188` | `10320293450` | `ZUZU LAPTE 1.5%GRASIME 1L` | `ZUZU` / `Litru` | 6,69 lei; codul de unitate diferă de cel Kaufland. |
| Mega Image / `1988` | `10692315487` | `ZUZU LAPTE CONSUM 1.5% 1L` | `Zuzu` / `BUCATI` | 6,39 lei; observat în București. |

Normalizarea `1,5%` → `1.5%`, `1L` → volum de 1 l și ignorarea diferențelor de majuscule sunt justificate pentru atributele textuale. Identitatea exactă rămâne candidat: catalogul nu clarifică toate diferențele posibile precum tipul de tratament al laptelui sau ambalajul. Prefixul `OUG` se păstrează în textul original, cu semnificație necunoscută; nu trebuie interpretat automat ca variantă ori condiție comercială.

### Cafea Jacobs 250 g - `1013048`

Acesta este cazul care blochează regula „același catalog ID = produs identic”.

| Rețea / magazin exemplu | Product.Id | Denumire comercială | Brand / Unit | Preț raportat |
| --- | --- | --- | --- | ---: |
| Mega Image / `1988` | `10692315574` | `JACOBS KRONUNG INTENSE 250G` | `Jacobs` / `BUCATI` | 31,49 lei |
| Mega Image / `2117` | `10692750159` | `JACOBS KRONUNG ALINTAROMA 250G` | `Jacobs` / `BUCATI` | 31,49 lei |
| Kaufland / `1418` | `10662620258` | `JACOBS KRONUNG INT CAFEA MACIN250G` | `Jacobs Kronung Intense` / `BUC` | 29,99 lei |
| Kaufland / `1398` | `10662234255` | `JACOBS KRoNUNG VID 250G` | `Jacobs Kronung` / `BUC` | 29,99 lei |
| Carrefour / `778` | `10688872475` | `CAFEA INTENSE 250G JACOBS` | `JACOBS` / `K` | 31,79 lei |
| Supeco / `7520` | `10690146596` | `CAFEA KRONUNG R&G 250G JACOBS` | `JACOBS` / `K` | 23,99 lei |
| Lidl / `3144` | `10698924263` | `Jacobs Kroenung Cafea mac. Jacobs Douwe Egberts` | `Jacobs Douwe Egberts` / `250g` | 29,99 lei |
| Profi / `7528` | `10649997194` | `JACOBS KRONUNG INTENSE 250G` | `JACOBS` / `Kg` | 36,19 lei |

În București există 9 cotații Mega Image cu numele `INTENSE` și 7 cu `ALINTAROMA`, toate sub catalogul `1013048`. Diferența explicită de variantă impune separarea candidaților sau verificare umană. Numele generice Kronung nu clarifică varianta; nu se completează automat cu Alintaroma. Aceleași valori de preț nu sunt dovadă de identitate.

`Kroenung`, `Kronung` și forma din nume `KRoNUNG` pot genera candidați pentru aceeași familie. Aliasul de scriere nu anulează conflictul Intense/Alintaroma. `Jacobs Douwe Egberts` în câmpul `Brand` poate fi o etichetă pentru companie; nu este dovadă suficientă că orice produs cu acea valoare este marca Jacobs și aceeași variantă. Se păstrează valoarea brută și se validează aliasul în contextul produsului.

### Cafea Jacobs 500 g - `1019036`

| Rețea / magazin exemplu | Product.Id | Denumire comercială | Brand / Unit | Preț raportat |
| --- | --- | --- | --- | ---: |
| Supeco / `7520` | `10690147214` | `CAFEA R&G 500G JACOBS KRONUNG` | `JACOBS` / `K` | 39,99 lei |
| Kaufland / `1418` | `10662988681` | `JACOBS KRoNUNG CAFEA VID 500G` | `Jacobs Kronung` / `BUC` | 49,99 lei |
| Lidl / `3144` | `10698987799` | `Jacobs Kroenung Cafea Jacobs Douwe Egberts` | `Jacobs Douwe Egberts` / `500g` | 49,99 lei |
| Mega Image / `1988` | `10692316019` | `JACOBS KRONUNG 500G` | `Jacobs` / `BUCATI` | 49,99 lei |

Cantitatea este explicită în majoritatea numelor și în `Unit` la Lidl. În eșantionul de 500 g nu apare un conflict explicit Intense/Alintaroma, dar absența acestui text nu confirmă aceeași rețetă sau variantă. Cafeaua de 250 g și cea de 500 g sunt ambalaje distincte; se pot compara separat printr-un preț normalizat dacă baza prețului este verificată. Nu se însumează sau substituie automat ca același SKU.

### Apă Borsec plată 2 l - `1361463`

| Rețea / magazin exemplu | Product.Id | Denumire comercială | Brand / Unit | Preț raportat |
| --- | --- | --- | --- | ---: |
| Supeco / `7520` | `10690150370` | `APA MIN NECARB 2L BORSEC.` | `BORSEC` / `L` | 3,78 lei |
| Kaufland / `1418` | `10662276693` | `BORSEC APA MIN NAT PLATA 2L SGR` | `Borsec` / `BUC` | 4,39 lei |
| Profi / `5188` | `10443036613` | `BORSEC APA MINERALA NATURALA PLATA 2L` | `BORSEC` / `Litru` | 4,49 lei |
| Mega Image / `1988` | `10692318640` | `BORSEC APA PLATA 2L` | `Borsec` / `BUCATI` | 4,49 lei |

`PLATA` și `NECARB` susțin un candidat compatibil în categoria apă necarbogazoasă. Numele Kaufland include `SGR`, dar XML-ul nu are un câmp separat pentru garanție, nici confirmarea includerii ei în preț. Nu se adaugă sau elimină automat o sumă de garanție. Tipul materialului, numărul recipientelor și orice condiție de ambalaj trebuie confirmate dacă nu sunt disponibile.

Există și catalogul `1011559`, cu numele apropiat `Apa Min Necarb 2l Borsec.`. În răspunsurile reprezentative testate acesta are preț zero și fără dată pentru toate magazinele. El nu este o ofertă gratuită și nu se unește automat cu `1361463` numai pe baza asemănării numelui.

## Unități, ambalaje și condiții de preț

| Valori brute observate | Ce putem extrage | Ce rămâne de verificat |
| --- | --- | --- |
| `BUC`, `BUCATA`, `BUCATI` | Etichete compatibile cu numărarea bucăților. | Dacă prețul privește o bucată, un pachet, o cantitate minimă sau o condiție comercială. |
| `L`, `Litru` | Etichete pentru o unitate de volum. | Dacă `Price` este per litru sau pentru ambalajul descris; nu se înmulțește automat cu 2 pentru apa de 2 l. |
| `K`, `Kg` | `Kg` sugerează masă; semnificația codului `K` necesită validarea convenției sursei. | Dacă `Price` este per kg sau pe pachet; pentru cafeaua de 250 g nu se împarte automat la patru. |
| `250g`, `500g` | Cantitate explicită în câmpul Lidl `Unit`. | Dacă este cantitatea unei bucăți sau a unei componente dintr-un multipack. |
| `250G`, `500G`, `1L`, `2L` în nume | Cantități candidate extrase din text. | Confirmare pe detaliul produsului, etichetă, factură sau feed de încredere. |

Se păstrează distinct cantitatea ambalajului, numărul de unități din pachet și baza prețului. TVA, SGR, reducerile, condițiile de card, cantitatea minimă, disponibilitatea și costul livrării rămân necunoscute când nu sunt furnizate. Necunoscut nu se transformă în zero. O ofertă cu bază de preț necunoscută poate fi afișată ca preț raportat, cu unitatea brută, dar nu susține economii validate pentru factura unei firme.

Nu există în aceste două eșantioane o dovadă de multipack sau o promoție explicită. Exemple precum „6 × 1 l”, „2 + 1 gratuit” sau „preț cu card” trebuie introduse numai ca scenarii de test viitoare, etichetate ca atare, ori după obținerea unor înregistrări reale cu acele condiții.

## Categoriile sursei necesită verificare

În XML-urile reprezentative, catalogul `1449689` numit `ARIEL DETERGENT LICH` este sub `Prodcateg.Name=LAPTE`; `1282436` numit `FAIRY APPLE 800ML` este sub `DEZINFECTANTI`. Aceste rânduri nu au cotații valide în eșantion, dar demonstrează că nici categoria catalogului nu poate fi tratată drept adevăr automat. În `catalog.xml`, categoriile acestor intrări sunt goale, deci informația diferă și între răspunsuri.

Schema internă trebuie să aibă categorii și atribute independente de codurile sursei. Se păstrează categoria brută, mappingul intern, motivul și versiunea mappingului. Un conflict între nume și categorie trimite înregistrarea la verificare; nu trebuie să inventeze o ofertă sau să determine singur categoria internă. Exemplele de mai sus sunt teste reale utile pentru acest mecanism.

## Reguli propuse pentru asociere

1. **Asociere declarată de sursă:** aceeași cheie de catalog leagă ofertele, fără eticheta „identic verificat”. Păstrează toate denumirile și atributele originale.
2. **Candidat compatibil:** marcă, familie, variantă explicită, cantitate și tip de produs se potrivesc; câmpurile relevante lipsă rămân marcate. Absența unui atribut nu este dovada egalității sale.
3. **Conflict:** variante diferite, cantități diferite pentru aceeași cerere de ambalaj sau categorii incompatibile blochează unirea automată. Conflictul Intense/Alintaroma are prioritate față de catalogul comun.
4. **Identitate verificată:** o dovadă suplimentară suficientă pentru categoria respectivă confirmă exact produsul și ambalajul. Poate fi un GTIN verificat împreună cu varianta, un mapping documentat de furnizor sau o confirmare umană pe dovezi păstrate. În aceste fișiere nu există un câmp GTIN care să permită această verificare.
5. **Echivalent funcțional / alt ambalaj:** este o relație separată, explicată și acceptată în contextul cererii. Nu moștenește identitatea SKU și nu înlocuiește produsul în coș fără o regulă explicită.

O explicație de asociere trebuie să spună ce s-a potrivit și ce lipsește: de exemplu „Zuzu, lapte, 1,5%, 1 l; tratamentul și baza prețului neconfirmate”. Nu se afișează un scor de încredere ca și cum ar fi o probabilitate calibrată până când acesta nu este evaluat pe un set etichetat.

## Teste reale disponibile acum

Acestea sunt recomandări pentru motorul de asociere și categorizare; nu înseamnă că motorul este deja implementat.

| Test din datele salvate | Rezultat așteptat |
| --- | --- |
| Mega Image `1988/10692315574` vs `2117/10692750159`, ambele catalog `1013048` | Conflict explicit Intense/Alintaroma; interzicerea unirii automate ca produs identic. |
| Jacobs `1013048` 250 g vs `1019036` 500 g | Ambalaje distincte, chiar dacă familia și marca se potrivesc. |
| Zuzu Penny `1,5%` vs Zuzu Kaufland `1.5%` | Atributul numeric se normalizează; rezultatul este candidat, cu diferențele de câmpuri păstrate. |
| Lidl Brand=`Jacobs Douwe Egberts` vs alte Brand=`Jacobs` | Generarea unui candidat în contextul numelui, fără alias global automat al tuturor produselor companiei. |
| Lapte `L` vs `BUC`, apă `Litru` vs `BUC`, cafea `K` vs `250g` | Separarea cantității de baza prețului; abținere de la calculul normalizat până la verificarea convenției. |
| Borsec `1011559` vs `1361463` | Similaritate de nume; ID separat, cotațiile zero/undatate indisponibile. |
| Ariel în categoria `LAPTE`, Fairy în `DEZINFECTANTI` | Conflict de categorie și verificare; sursa brută rămâne accesibilă. |
| NetworkId Lidl cu nume `Slatina/Alexandru Ioan Cuza` | Rețeaua se rezolvă prin ID, iar numele magazinului se păstrează separat. |
| Același nume și catalog, mai multe `Product.Id` în aceeași rețea | Identitățile observațiilor rămân distincte; Product.Id nu devine cod canonic global. |

Parserul curent are separat 32 de verificări offline pentru ID-uri, rânduri necerute, prețuri/date invalide, coș parțial, deduplicare și răspunsuri XML Error. Ele protejează aritmetica și citirea datelor, nu validează identitatea comercială.

## Setul de verificare OCR recomandat

Nu au fost analizate facturi reale și nu a fost executat OCR în această analiză. Etapa următoare cere un set de facturi reale, anonimizate când este necesar, cu rezultatul corect transcris și verificat manual. Se păstrează documentul original, poziția fiecărui câmp extras, corecturile și decizia de asociere.

Setul trebuie să cuprindă facturi lizibile și fotografii cu rotație, umbre ori rezoluție redusă, documente cu mai multe pagini și formate de furnizori diferiți. Cazurile de verificat sunt:

- cantitate, unitate, preț unitar și valoare de rând, inclusiv virgule zecimale și separatori de mii;
- produs cu denumire abreviată, cod furnizor prezent, marcă absentă și descriere insuficientă pentru variantă;
- aceeași familie cu 250 g și 500 g, respectiv bucată și bax: motorul cere confirmare dacă ambalajul nu poate fi stabilit;
- TVA extras din document, fără presupunerea unei cote; poziții cu tratamente diferite și documente care arată prețuri nete sau brute;
- reduceri pe rând și pe document, SGR ori alte taxe separate, transport și retururi; acestea nu se asociază automat cu un produs cumpărat;
- nepotrivirea dintre suma rândurilor și totalurile documentului, linii duplicate și document importat de două ori;
- confuzii OCR între cifre și litere în coduri și nume, fără inventarea unui cod de produs;
- recomandarea unei economii numai după confirmarea produsului, cantității, bazei prețului și perioadei de comparație.

Pentru fiecare document se măsoară separat extragerea câmpurilor, verificarea sumelor, asocierea produsului și necesitatea corectării umane. Un total corect nu validează automat denumirea produsului. Predicțiile cu informații insuficiente trebuie să se poată abține, păstrând rândul ca neasociat.

## Setul de verificare pentru electronice recomandat

În această analiză nu există oferte reale de electronice. Nu se deduce acoperire pentru această categorie din catalogul alimentar. Testele următoare trebuie construite din feed-uri, pagini ori fișe tehnice reale obținute în cadrul sursei autorizate și verificate manual; nu se introduc modele și prețuri inventate în demonstrația comercială.

Pentru identitate sunt necesare, după categorie, producătorul, modelul exact și codul MPN/part number, GTIN când există, capacitatea, configurația, culoarea dacă definește SKU-ul, regiunea și starea produsului. Accesoriile incluse, kitul, garanția și condițiile vânzării se păstrează ca atribute ale produsului sau ale ofertei, după caz. Vânzătorul efectiv se separă de platforma marketplace.

Testele reale trebuie să confrunte același model și cod în magazine diferite, modele cu nume apropiate dar coduri diferite, capacități/configurații diferite, kit vs produs individual și nou vs resigilat/refurbished. O categorie de accesoriu nu se unește cu dispozitivul compatibil. Asocierea după titlu sau imagine poate produce candidați; contradicțiile în model, capacitate, configurație ori stare blochează identitatea. Normalizarea unui nume comercial nu trebuie să elimine tokenuri care diferențiază modelul.

## Criterii de verificare înaintea comparațiilor și recomandărilor

Se construiește un set etichetat manual cu perechi identice, ambalaje diferite, echivalente acceptabile, conflicte și cazuri insuficiente. Evaluarea folosește perechi păstrate separat de cele folosite pentru reguli și aliasuri. Se raportează asocierile corecte, unirile greșite, candidații omişi și abținerile, separat pe categorie și sursă.

Pentru setul verificat, niciun conflict explicit din exemplele reale de mai sus nu trebuie unit automat ca identitate. Trecerea acestui set finit nu garantează precizie perfectă pe date viitoare. Regulile se revizuiesc când apar noi variante, schimbări de feed sau neconcordanțe; modificările au versiune și probe de regresie.

Economiile și schimbarea furnizorului se recomandă numai pe baza produselor confirmate și a condițiilor comparabile. Prețul istoric din factură, prețul raportat curent și costurile totale cunoscute sunt valori distincte. Pozițiile fără identitate sau condiții suficiente rămân vizibile ca oportunități de verificat, fără sumă de economie prezentată drept certă.
