# Specificație de produs - Preturi achizitii

Specificație inițială din 5 octombrie 2026, completată la 6 octombrie pentru conturi și emailuri. Descrie produsul țintă; funcțiile implementate și cele planificate sunt separate în [README](../README.md).

Acest document definește comportamentul vizibil al produsului. [Planul de implementare](PLAN_IMPLEMENTARE.md) stabilește ordinea livrării, [deciziile de arhitectură](DECIZII_ARHITECTURA.md) stabilesc stiva și infrastructura, iar [motorul de corectitudine](MOTOR_CORECTITUDINE.md) definește asocierile, regulile de calcul și validarea lor. Faptele și mandatul provin din [cererea inițială](../CERERE_INITIALA.md), [cerințele extinse](CERINTE_EXTINSE.md), [raportul probelor](../RAPORT_TESTARE.md), [validarea identității în date](VALIDARE_IDENTITATE_DATE.md) și fișierele păstrate în `probe-data`. [Cercetarea Compari.ro](CERCETARE_COMPARI.md) completează lecțiile de proiectare, fără a autoriza preluarea datelor sale.

## 1. Promisiunea produsului și utilizatorii

Aplicația ajută o firmă mică să decidă ce să cumpere, în ce cantitate și de la cine, pe baza unor oferte identificate și explicabile. Utilizatorul vede ce s-a comparat, când a fost observat prețul și ce costuri lipsesc. Formularea permisă este „cel mai mic preț găsit în ofertele comparabile din sursele verificate”, însoțită de aria căutării și data datelor.

Utilizatorul principal este administratorul unei firme mici sau persoana care face achizițiile: cumpără recurent cafea, lapte, apă, produse de curățenie și birotică, lucrează frecvent de pe telefon și are facturi de la mai mulți furnizori. Nu trebuie să cunoască GTIN, OCR, TVA tehnic sau structura unui catalog pentru a folosi aplicația. Un utilizator secundar verifică facturile și justificarea economiilor; are nevoie de export și de traseul dintre document și cifrele afișate.

Obiective:

- Găsirea rapidă a produsului și a variantei potrivite; diferențele importante sunt vizibile înainte de alegere.
- Compararea costurilor pentru cantitatea cerută, cu ambalaje și condiții explicite.
- Construirea unei istorii reale a cumpărăturilor din introducere manuală și documente confirmate.
- Propunerea unor alternative și schimbări de furnizor numai când există dovezi suficiente.
- Un produs simplu pe telefon, care se poate extinde la alte categorii fără pierderea corectitudinii.

Nonobiective:

- Acoperirea garantată a tuturor comercianților din România, minimul absolut al pieței sau stoc garantat.
- Checkout, comandă automată, plată, contractare ori trimitere de cereri către furnizori în prima versiune.
- Contabilitate, calcul fiscal normativ, validarea autenticității fiscale a facturii sau integrare automată ANAF.
- Echivalarea automată a produselor numai din asemănarea numelui; inventarea prețurilor sau completarea din memorie a valorilor lipsă.
- Etichete precum „mai serios”, „calitate mai bună” ori „furnizor de încredere” deduse din preț sau din prezența într-un comparator.
- Scraping universal, publicare comercială sau presupunerea existenței unor drepturi/API doar pentru că o pagină este publică.

## 2. Contractul primei versiuni locale

Completare din 6 octombrie 2026: fluxurile viitoarei versiuni găzduite sunt definite în [ACCES_SI_EMAIL.md](ACCES_SI_EMAIL.md). Versiunea locală actuală nu implementează login, verificare email, recuperare cont, invitații sau trimitere de email; numele firmei și sesiunea locală nu oferă aceste funcții.

Aplicația pornește local fără conturi externe și fără chei API. Utilizează snapshoturile existente din 05.10.2026 și un spațiu local pentru datele introduse de utilizator. Nu face cereri către surse la pornire și nu suprascrie probele originale. Adaptarea la telefon se verifică în viewport mobil pe serverul loopback; accesul de pe alt dispozitiv prin LAN nu este promis în E1 și necesită etapa cu acces/autentificare configurate.

Livrarea este incrementală: **E1a** acoperă catalogul, lista și explorarea/compararea cotațiilor salvate; **E1b** adaugă import manual/CSV/UBL, confirmarea, analiza datelor reale introduse și scenarii pe oferte private datate/declarate de firmă; **E2** adaugă importul real de text și PDF cu text, împreună cu restul extinderilor definite în plan; **E3** adaugă OCR real configurat pentru imagini/documente scanate. Specificația descrie produsul complet; nu condiționează E1a de funcțiile E1b-E3. Ecranele neimplementate nu au butoane care pretind că funcționează.

La nivelul aplicației apare **„Mod local, fără actualizare automată”**. Fiecare ecran/card care prezintă cotații publice din probe arată **„Date salvate - 05.10.2026”** și explică „Cotații din fișierele probelor; prețul și disponibilitatea la cumpărare nu sunt verificate”. Ora din `Pricedate` se prezintă ca oră declarată de sursă; data importului aplicației nu devine data prețului. O redeschidere ulterioară a aplicației nu face datele proaspete.

O ofertă privată introdusă manual în E1b păstrează propria dată/perioadă și eticheta **„Valabilitate declarată de firmă, neverificată automat”**; nu primește data snapshoturilor publice. Un rezultat mixt arată separat cotațiile din 05.10.2026 și ofertele private cu datele lor, inclusiv în explicația sumei. Modul fără rețea, proveniența datelor și valabilitatea comercială sunt stări distincte. Un scenariu pe o ofertă privată declarată curentă nu este colectare live, verificare la furnizor sau checkout.

Limitele geografice sunt selectabile numai dintre probele reale: Slatina, proba de 5 km, și București, proba de 1 km, cu zona/punctul sursei explicat. Acestea nu sunt căutări curente după locația telefonului și nu reprezintă întregul oraș. Lista Lidl este afișată ca listă a sortimentului permanent, cu aria declarată de sursă, fără a simula stocul unui magazin local. Nu amestecăm cele două tipuri de acoperire într-o singură promisiune de disponibilitate.

| Capacitate | Ce poate demonstra local | Ce rămâne condiționat |
|---|---|---|
| Căutare în catalog | Catalogul salvat și produse normalizate/curate; produsele fără oferte sunt marcate | Preț pentru orice rezultat, actualizare live, acoperire națională |
| Oferte și coș | Cotații din probe, cantități și lipsuri, comparații permise de atributele confirmate | Cost total final dacă transportul, taxele ori condițiile sunt necunoscute |
| Facturi - E1b | Introducere manuală; CSV pe șablon; subset UBL/XML documentat, cu verificare | Import de text/PDF în E2; import arbitrar al oricărui XML; integrare fiscală externă |
| Fotografie/PDF scanat | Tip detectat, stare sinceră și opțiunea introducerii manuale | Extragere OCR numai cu adaptor real configurat și funcțional |
| Istoric | Documente confirmate de utilizator, proveniență și export | Economii reale în lipsa unui istoric verificabil |
| Ofertă privată - E1b | Formular cu propria dată/perioadă, condiții declarate și scenariu de comparație condiționat | Verificare automată a valabilității, colectare live sau checkout |
| Recomandări | Explicații bazate pe comparațiile valide din snapshot; scenarii condiționate pe oferte private declarate | O recomandare curentă fermă de cumpărare, cât timp lipsesc dovezile comerciale necesare |
| Firma | Un profil local explicit și datele sale | Acces simultan de la distanță, autentificare și administrare multiutilizator |

Datele publice din probe pot fi folosite într-un tur opțional. Nu se creează facturi sau cumpărături fictive în istoricul firmei. Fixture-urile testelor sunt separate și etichetate; nu sunt dovezi comerciale.

## 3. Funcții selectate și priorități de produs

| Funcție | Motiv | Regula care previne inducerea în eroare |
|---|---|---|
| Listă de cumpărături cu cerințe | Pornește de la sarcina reală a utilizatorului | O denumire liberă rămâne „de identificat” până la alegerea produsului |
| Identificarea variantei și comparație pe unitate | Este centrul utilității și al riscului | Unitatea normalizată nu ascunde ambalajul care trebuie plătit |
| Coș într-un magazin și selecție din mai multe | Arată compromisul dintre preț și efort | Costurile suplimentare și liniile lipsă sunt vizibile înaintea totalului |
| Istoric din facturi și corectare ghidată | Oferă un reper real pentru recomandări | Datele extrase sunt separate de datele confirmate |
| Alternative aprobate explicit | Mărcile/ambalajele diferite pot fi utile | Acceptarea este contextuală; nu rescrie identitatea globală a produselor |
| Liste salvate/reutilizare a cumpărăturilor | Economisește timp la achiziții recurente | Reutilizarea păstrează cerințele; nu păstrează un preț ca fiind actual |
| Explicația diferenței de preț | Face rezultatul verificabil | Arată baza, cantitatea, documentul și costurile omise |
| Sugestie de furnizor alternativ | Poate reduce cheltuielile recurente | Cere istoric comparabil și costuri suficiente; se abține altfel |
| Export date și ștergere documente | Utilizatorul își controlează datele firmei | Exportul și ștergerea au scop și efect explicite |

Ulterior: surse actualizate controlat, alerte de preț pe criterii salvate, OCR real, conturi și colaborare, categorii electronice alimentate din surse autorizate. Ofertele private/negociate introduse manual apar deja în E1b, cu limitele declarate mai sus. Înainte de existența infrastructurii, nu se afișează comutatoare care par să activeze serviciile ulterioare. Un ecran informativ poate indica funcția neconfigurată și alternativa disponibilă.

## 4. Identitatea produsului în interfață

O nevoie, un produs și o ofertă sunt lucruri diferite. „Cafea pentru birou” este o nevoie. „Jacobs Krönung, măcinată, 250 g” este o variantă comercială. Cotația pentru acea variantă la un anumit magazin și moment este o ofertă. Lista permite păstrarea unei nevoi nerezolvate fără a o transforma într-un produs inventat.

Gruparea declarată de o sursă se numește **„Asociat de sursă - identitate neconfirmată”** până la validare. Același `Catprod.Id` nu o promovează automat la produs identic. În E1a există o secțiune „Cotații raportate de sursă” care permite inspectarea datelor reale și arată denumirea/varianta comercială; nu pretinde o comparație semantică validată. Dacă niciun candidat nu trece validarea, secțiunea de produse identice poate rămâne goală.

Fiecare asociere validată sau propusă are o etichetă textuală și o explicație accesibilă prin „De ce sunt comparate?”:

| Relație afișată | Exemplu | Comportament |
|---|---|---|
| **Produs identic** | Aceeași marcă, formulă/model, variantă și ambalaj confirmate | Poate participa la clasamentul strict dacă oferta este utilizabilă |
| **Alt ambalaj, aceeași variantă** | Aceeași cafea măcinată, 250 g versus 500 g, cu atributele verificate | Secțiune separată; arată lei/kg, numărul de pachete și cantitatea în plus; utilizatorul aprobă schimbarea |
| **Alternativă compatibilă** | Altă marcă de lapte cu caracteristicile acceptate pentru acea nevoie | Separată de produsul identic; condițiile acceptate sunt vizibile |
| **Sugestie de verificat** | Text asemănător, dar gramaj sau atribut decisiv lipsă | Nu intră în totaluri/economii; cere confirmarea informației lipsă |

„Asociere verificată” înseamnă că regula sau revizia identității are dovezi; nu înseamnă că prețul a fost verificat la casă. Interfața arată separat proveniența identității și a prețului. Nu afișează un procent de încredere ca probabilitate, dacă motorul nu este calibrat pentru acel sens; preferă „atribute confirmate”, „necesită verificare” și motivul.

Diferențe obligatoriu vizibile:

- Cafea: boabe/măcinată/solubilă, amestec/variantă, cofeină, gramaj; același nume de familie comercială nu este suficient.
- Lapte: specie/tip, procent de grăsime, tratament și volum. Laptele 1,5% nu devine identic cu 3,5%.
- Toner: cod de consumabil, tehnologie, culoare, compatibilitate exactă cu dispozitivul, original/compatibil și capacitate/randament când există. O mențiune generică a mărcii imprimantei nu confirmă compatibilitatea.
- Electronice: producător, model/cod de producător, RAM, stocare și alte atribute relevante categoriei; nou/resigilat/recondiționat/folosit și garanția sunt condiții distincte. O condiție sau garanție necunoscută împiedică o recomandare prezentată ca echivalentă complet.

Confirmarea de către utilizator a unei alternative se aplică listei sau regulii personale a firmei, după alegere explicită. Ea nu poate transforma un atribut contradictoriu într-o identitate verificată și nu se propagă la alte firme.

## 5. Categorii inițiale și atribute

Taxonomia este prezentă de la început, dar numărul de oferte utilizabile este afișat pe categorie. O categorie goală spune „Poți înregistra cumpărături aici; nu avem încă oferte comparabile din sursele încărcate”. Nu se umple cu rezultate fabricate. Denumirile originale și categoriile sursei rămân în detalii; categoria internă are o versiune și poate fi corectată.

| Categorie / subcategorii inițiale | Atribute decisive | Atribute utile pentru alternative |
|---|---|---|
| Alimente și băuturi / lactate | Marcă, familie/variantă, tip, procent grăsime, tratament, volum, număr recipiente | Fără lactoză, cerințe alimentare declarate; nu se deduc din fotografie |
| Alimente și băuturi / cafea și ceai | Marcă, gamă, formă, variantă, masă, număr pachete/doze | Cofeină, compatibilitate capsule, preferința explicită de marcă |
| Alimente și băuturi / apă și alte băuturi | Marcă, tip, carbogazificare, volum, recipient, multipachet | SGR documentat, preferința pentru recipient |
| Curățenie / vase, rufe, suprafețe | Marcă, gamă, destinație, formă, concentrație/variantă, cantitate | Dozare și număr utilizări numai când sunt declarate pe aceeași bază |
| Igienă și hârtie / hârtie igienică, prosoape, șervețele | Tip, marcă, număr role/pachete, foi, straturi, dimensiuni relevante | Cost pe 100 foi doar când numărul și dimensiunile sunt comparabile |
| Birotică / hârtie, scriere, arhivare | Format, gramaj hârtie, număr coli, culoare; tip/dimensiune după subcategorie | Certificări/documente numai dacă sursa le furnizează |
| Imprimare / tonere și cartușe | Cod producător, modele compatibile, culoare, original/compatibil, tip | Randament cu standard/bază declarată, multipachet |
| Electronice / laptopuri, telefoane, monitoare, periferice | Model/cod, configurație, regiune/variantă; RAM, stocare, ecran/conectică după caz | Condiție, garanție, accesorii incluse, vânzătorul efectiv |
| Alte produse / de clasificat | Nume original, furnizor, cantitate, unitate și atribute confirmate | Import posibil; fără asociere automată până la definirea categoriei |

Primul set propus pentru revizie este restrâns la lapte, cafea și apă din exemplele raportului. Acest set nu este deja validat semantic: analiza ulterioară a găsit variante Intense/Alintaroma sub același ID de cafea și baze de preț neclarificate. E1a poate demonstra grupările și sumele sursei, cu aceste limite, chiar dacă niciun coș nu este încă eligibil pentru o recomandare strictă. Produsele Lidl intră în catalog cu datele disponibile; lipsa EAN ori a unui atribut nu se „repară” inventându-l. Extinderea consumabilelor și electronicelor trebuie să adauge exemple etichetate și reguli specifice înainte de recomandări automate.

## 6. Navigare și design vizual

Pe telefon, bara de navigare inferioară are patru destinații cu icon și text: **Cumpărături**, **Catalog**, **Facturi**, **Analiză**. Profilul firmei și setările sunt accesibile din antet. Analiză conține filele „Istoric”, „Diferențe de preț” și „Furnizori”. Pe ecran mare aceeași structură devine bară laterală; ordinea și denumirile rămân identice.

Direcție vizuală: un instrument de cumpărături calm, cu mult spațiu și accent pe produs/cantitate/preț. Fundal `#F6F8F7`, suprafețe albe, text principal `#182621`, text secundar `#4E6058`, accent verde `#185D48`. Avertismentele folosesc suprafețe crem și text închis; erorile au text și icon explicite, nu doar roșu. Culoarea verde nu este folosită pentru a prezenta un cost incomplet drept economie. Contrastul combinațiilor efectiv implementate se verifică înainte de acceptare.

- Font de sistem, corp de minimum 16 px, înălțime de rând aproximativ 1,5; cifre tabulare pentru prețuri. Titlurile folosesc 24-28 px pe telefon, fără text decorativ supradimensionat.
- Spațiere bazată pe 4/8 px; carduri cu rază de 12 px, bordură subtilă și umbră rară. Paginile au 16 px margine pe telefon și lățime controlată pe desktop.
- Butonul principal numește acțiunea: „Compară 3 produse”, „Verifică 2 câmpuri”, „Confirmă factura”. Nu există mai multe butoane principale concurente într-un card.
- Zone de apăsare de cel puțin 44×44 px, focus vizibil, etichete reale pentru câmpuri și navigare completă cu tastatura. Mesajele de validare sunt legate de câmp și anunțate cititoarelor de ecran.
- La 320 px lățime nu există scroll orizontal al paginii. Tabelele ample devin carduri cu aceeași ordine de informații; nu se ascund avertismente în afara ecranului.
- Zoom 200%, mișcare redusă și text lung în română sunt verificate. Nu se bazează pe hover și nu folosește animații pentru a comunica o schimbare obligatorie.
- Prețurile se afișează în format românesc, de exemplu `23,99 lei/pachet` și `95,96 lei/kg`, cu unitatea lângă număr. Datele au forma `05.10.2026`; intervalele și fusul orar se precizează unde afectează interpretarea.

Cardul standard de ofertă, în această ordine: produs și variantă; tipul asocierii; vânzător/magazin; prețul ambalajului și prețul normalizat verificat; cantitatea care trebuie cumpărată; data și sursa; condiții și lipsuri; acțiunea „Vezi detalii” sau „Alege”. Imaginile sunt opționale; un placeholder neutru nu sugerează o marcă și produsul rămâne identificabil din text.

## 7. Fluxuri și ecrane

### 7.1 Prima deschidere și contextul firmei

Ecranul inițial explică în două propoziții scopul și datele salvate. Acțiuni: „Începe o listă” și „Vezi exemplul din Slatina”. Exemplul încarcă numai produse și cotații publice; nu înregistrează o achiziție.

Profilul local cere un nume intern pentru firmă; CUI, adresă completă și date de contact nu sunt obligatorii pentru comparație. Utilizatorul alege zona dintre probele disponibile și preferințe de cumpărare: produs exact implicit, dacă acceptă alt ambalaj, număr maxim de magazine. Setarea firmei privind TVA nu completează automat TVA necunoscut pe o ofertă. Opțiunea de bază pentru o comparație monetară se activează numai când datele necesare există.

Stări: profil absent → inițializare scurtă; date locale indisponibile → explicație și reluare; profil existent → ultima listă, fără repetarea onboardingului. În modul local nu se afișează autentificare fictivă, recuperare parolă sau invitații de echipă.

### 7.2 Cumpărături: lista de nevoi

Lista are titlu, zonă, proveniența/datele ofertelor, produse și cantități. Adăugarea pornește cu „Ce ai nevoie să cumperi?”; utilizatorul poate căuta un produs sau păstra o linie liberă. Selectarea rezultatului arată varianta înainte de confirmare. Cantitatea se introduce ca pachete/bucăți sau necesar în kg/l, când unitatea are sens; conversia trebuie arătată.

Fiecare linie are: cerința originală, produs/variantă selectate sau „De identificat”, cantitate, alternative acceptate și starea ofertei. Editarea unei variante sau a cantității invalidează calculul precedent și păstrează lista. Eliminarea permite anulare imediată.

Acțiunea fixă de jos este „Compară N produse”; nu acoperă ultima linie ori mesajele tastaturii. Liniile nerezolvate nu dispar: comparația explică „Comparăm 2 din 3; identifică tonerul pentru un coș complet”. Utilizatorul poate salva/reutiliza lista. „Am cumpărat” deschide introducerea facturii ori a cumpărării reale și nu transformă cotația în achiziție confirmată.

Stări: listă goală → un singur apel la adăugare și exemplu opțional; căutare în desfășurare → schelet simplu; produs fără rezultate → păstrează textul și permite completarea manuală; produs fără preț → păstrează nevoia; calcul eșuat → lista rămâne intactă, cu reluare.

### 7.3 Catalog: căutare și rezolvarea variantelor

Căutarea acceptă diacritice și aliasuri aprobate. Rezultatele arată marcă, variantă, gramaj/ambalaj, categoria și numărul ofertelor utilizabile în zona selectată. Filtre: categorie, marcă, atribute specifice, numai produse cu oferte utilizabile. Nu este suficient să numărăm rânduri brute ca „oferte”.

Când există variante apropiate, se deschide un selector explicit: „250 g / 500 g”, „1,5% / 3,5%”, „8 GB / 16 GB”, după categorie. Un produs incomplet spune care atribut lipsește. Fișa produsului include denumiri din surse, atributele confirmate și „Corectează asocierea” pentru o propunere verificabilă. Corectura utilizatorului rămâne în aria firmei, dacă nu există un proces separat de revizie globală.

Stări: categorie fără acoperire → mesajul din secțiunea 5; multe rezultate → paginare/încărcare progresivă fără a încărca întregul catalog în telefon; rezultat ambiguu → alegeri clare, fără selectare automată; sursă cu denumire goală → nu apare ca produs fără nume în listă și intră în raportul de date invalide.

### 7.4 Oferte pentru un produs

Secțiunea „Cotații raportate de sursă” este distinctă de filele „Produs identic”, „Alt ambalaj” și „Alternative”. Ultimele două nu intră în clasamentul strict de produse identice; după acceptare explicită pot participa la un scenariu separat, „Cu alternative acceptate”. Sortarea implicită folosește numai baza comparabilă: costul pentru cantitatea cerută, dacă este calculabil; altfel prețul cotat în propria bază, într-o secțiune separată, fără clasament comun fals. Conflictul real Jacobs Intense/Alintaroma apare ca exemplu de asociere a sursei care necesită revizie, nu ca preț mai bun pentru un produs identic.

Antetul rezultatului spune câte oferte și surse au fost evaluate, aria și datele seturilor incluse. Detaliile ofertei conțin denumirea originală, prețul original, data sursei sau data declarată de firmă, momentul colectării/introducerii, unitatea/ambalajul, stocul dacă este cunoscut, promoția, cardul sau alte condiții și dovezile asocierii. Câmpurile necunoscute sunt „Nespecificat de sursă”, nu valori zero.

Stări specifice sursei: pentru Monitorul Prețurilor, `Price ≤ 0`, preț invalid ori `Pricedate` absent/invalid → „Fără cotație utilizabilă”, exclus din clasament. Rândul Lidl cu preț valid rămâne afișabil ca cotație din fișier, cu momentul colectării și „Data prețului și valabilitatea individuală: nespecificate”; nu este eligibil pentru o recomandare fermă curentă, dar poate participa la o estimare condiționată, afișată distinct. Data fișierului nu completează automat data sau valabilitatea prețului.

Stări comune: informații contradictorii → „Ofertă în verificare”; preț vechi → eticheta datei și excludere din recomandarea curentă conform politicii motorului; reîmprospătare viitoare eșuată → se păstrează ultima observație cu vechimea și eroarea, fără actualizarea artificială a timestampului.

### 7.5 Compararea coșului

Rezultatul are două secțiuni:

1. **Un singur magazin**: coșuri complete comparabile primele; fiecare arată produsele, cantitățile și costurile incluse. Coșurile parțiale sunt într-o secțiune distinctă, cu „Subtotal pentru 2 din 3 produse” și numele produsului lipsă. Un subtotal nu primește insigna câștigătorului.
2. **Mai multe magazine**: arată numărul de opriri, împărțirea liniilor, cantitatea în plus și costurile cunoscute. Dacă deplasarea/transportul nu sunt cunoscute, rezultatul spune „Subtotal produse; avantajul total nu poate fi stabilit”. O preferință introdusă de utilizator pentru cost/deplasare este o ipoteză etichetată, nu un tarif măsurat.

În ambele secțiuni, completitudinea are trei dimensiuni vizibile: **cotații prezente** (regulile adaptorului îndeplinite pentru toate liniile; la Monitor inclusiv data validă, la Lidl valabilitatea necunoscută rămâne explicită), **produse comparabile** (identitate/variantă/unitate validate) și **costuri complete** (condiții și costuri relevante cunoscute). Cele 15 magazine și sumele 33,86/41,07/42,87 lei din raport reprezintă prima dimensiune, nu le demonstrează pe celelalte. Când identitatea rămâne incertă, ecranul spune „Sumă a cotațiilor grupate de sursă - comparație comercială nevalidată”; nu acordă o insignă „cel mai ieftin coș”.

Panoul „Ce include suma?” separă marfa, reducerile aplicabile, TVA cunoscut, SGR, transportul și alte costuri cunoscute. Necunoscutele rămân lângă sumă, nu doar într-un tooltip. Prețurile cu card, cantitate minimă ori contract se includ numai după confirmarea eligibilității. Prețul public și prețul negociat al firmei rămân distincte.

Utilizatorul poate modifica numărul maxim de magazine și poate accepta o alternativă pe o linie; vede înainte de aplicare diferența de variantă și cantitate. Acceptarea recalculează rezultatul și actualizează explicația. Nu se promite optimul absolut când motorul a evaluat un set restrâns de combinații; se numește „cea mai bună variantă dintre combinațiile evaluate”, cu aria calculului în detalii.

Stări: niciun coș complet → mesaj înaintea subtotalurilor; ambalaj imposibil de convertit → linie în verificare; condiție minimă neîndeplinită → ofertă neeligibilă; costuri necunoscute → suma disponibilă este subtotal; calcul în curs → rezultatul anterior marcat ca depășit nu poate fi confirmat ca nou.

### 7.6 Facturi: încărcare și introducere - E1b, extensii E2/E3

Ecranul Facturi arată documentele, furnizorul, data, totalul cunoscut și statusul: „Ciornă”, „În procesare”, „Necesită verificare”, „Confirmată”, „Eșuată”. „Adaugă o factură” deschide metodele efectiv disponibile:

- **Introducere manuală**: furnizor, număr/data documentului, monedă, linii, cantități/unități, valori și taxe cunoscute. Datele lipsă sunt semnalate; nu se inventează cote TVA.
- **CSV după șablon**: descărcarea șablonului, previzualizare și mapare de coloane documentată. Ambiguitatea separatorului zecimal sau a unității trebuie rezolvată înainte de confirmare.
- **XML/UBL acceptat**: importatorul verifică structura și profilul suportat. Formatele necunoscute, notele de credit ori cazurile neimplementate se identifică explicit și nu sunt interpretate tacit ca facturi obișnuite. Un fișier XML nu devine valid doar prin extensie.
- **Text copiat - E2**: se păstrează textul original; extragerea deterministă limitată poate propune câmpuri, iar restul se completează manual. Câmpurile neidentificate nu sunt completate de un model absent.
- **Fotografie sau PDF scanat - E3**: numai când un adaptor OCR real este configurat. În modul local fără adaptor, controlul arată „Citirea imaginilor nu este configurată. Poți introduce datele manual sau importa CSV/XML”; nu afișează o scanare fictivă ori rezultate de probă. Dacă fișierul a fost selectat printr-un control general, utilizatorul primește această stare și nu se salvează un document inutil fără alegerea lui.

Un PDF cu text primește extragere locală în E2 dacă parserul real este implementat și verificat. În absența lui, nu este prezentat ca format suportat. OCR extern transmite documentul doar după configurare și informarea clară a utilizatorului despre furnizor și datele trimise; selectarea unui fișier nu produce upload ascuns către terți.

Înainte de import: limitele de fișier/pagini și tipurile acceptate apar lângă control și sunt configurate conform arhitecturii. Document duplicat: se arată documentul existent și se oferă deschiderea lui; nu dublează cheltuielile. Indicii slabi de duplicat cer revizie, nu ștergere automată.

### 7.7 Corectarea și confirmarea unei facturi

Pe desktop, documentul/textul sursă și câmpurile stau alăturat. Pe telefon există comutator „Document / Date”, cu păstrarea poziției. Când extractorul oferă coordonate sau referințe XML, atingerea câmpului arată locul sursă. Când nu le oferă, interfața spune asta; nu desenează dovezi fictive.

Revizia are trei pași scurți:

1. **Date document**: furnizor, număr, data, monedă și totaluri. Datele extrase și cele corectate sunt vizibile în istoricul câmpului.
2. **Linii și verificări**: cantitate, unitate, preț, reduceri și taxe; diferențele aritmetice sunt explicate în lei și localizate. „2 câmpuri de verificat” conduce exact la câmpurile problematice. Un scor OCR mare nu anulează o contradicție aritmetică.
3. **Produse și confirmare**: propuneri de asociere, atribute lipsă și linii neasociate. Utilizatorul poate confirma o cheltuială documentată cu produs încă neasociat; linia intră în istoric financiar, dar nu în economii pe produs până la asociere validă. O factură cu probleme materiale nerezolvate rămâne ciornă; regulile de rotunjire și toleranță sunt în motor.

Confirmarea este o acțiune explicită și păstrează cine/când a confirmat, originea fiecărui câmp și versiunea calculelor. „Confirmată” înseamnă acceptată de utilizator pentru aplicație, nu certificată fiscal. Corectarea ulterioară produce o revizie și recalculează analizele afectate; nu schimbă silențios un rezultat istoric.

Stări: extragere în curs → progres real pe document/pagini dacă există; adaptor indisponibil → eroare și opțiune manuală; text ilizibil → recapturare ori completare; aritmetică diferită → revizie obligatorie; document anulat/creditat → tratament explicit conform suportului, niciodată cheltuială dublată; nicio asociere sigură → păstrează liniile și cere identificarea.

### 7.8 Istoric și diferențe de preț

Istoricul listează numai cumpărări confirmate, cu perioadă, furnizor, categorie și produs. Fiecare sumă permite accesul la documentele/liniile care o compun. Produsele neasociate sunt vizibile separat și nu dispar din cheltuieli.

Analiza folosește trei noțiuni distincte:

- **Preț facturat atunci**: prețul efectiv din document, cu reducerile/taxele și cantitatea cunoscute. Factura confirmată de utilizator susține achiziția raportată; nu demonstrează plata bancară. „Preț plătit” se folosește doar dacă utilizatorul a confirmat și plata.
- **Diferență față de ofertele de la aceeași dată**: disponibilă numai dacă există observații comparabile din perioada potrivită. Un snapshot din 05.10.2026 nu dovedește o ofertă disponibilă în septembrie.
- **Diferență față de o ofertă de referință**: scenariu pentru aceeași cantitate și bază, cu ambele date afișate. Pentru snapshot se numește „Diferență față de cotația salvată din 05.10.2026”; pentru oferta privată, „Diferență față de oferta declarată de firmă din [data]”, cu perioada declarată și lipsa verificării automate. O observație live ulterioară își arată propria sursă și dată. Un scenariu mixt păstrează toate aceste etichete per ofertă; niciunul nu devine automat „Ai economisit”.

„Economii realizate” se poate afișa numai dacă există achiziția efectivă și un reper comparabil, justificat și păstrat, conform regulilor motorului. Altfel sunt diferențe de preț sau economii potențiale, cu ipoteze și acoperire. Scăderile și creșterile folosesc semn și text; nu se afișează doar suma diferențelor favorabile ascunzând costurile mai mari.

Un card de analiză arată perioada, baza comparației, numărul liniilor eligibile/total, costurile incluse și lipsurile. Graficul este opțional după existența datelor și are și listă/tabel accesibil; liniile dintre două observații nu pretind prețuri zilnice măsurate. Nu se anualizează o singură factură ca „economie anuală” fără ipoteză explicită și scenariu separat.

Stări: fără facturi → invită importul; facturi neconfirmate → cere revizie; cumpărături confirmate fără ofertă comparabilă → arată cheltuiala, fără economie; baze fiscale incompatibile → explică datele necesare; revizie în curs → indică analizele care urmează să fie recalculate.

### 7.9 Recomandări despre furnizori

Recomandarea începe cu o propoziție verificabilă: „Pentru aceste N produse, alternativa B are un subtotal cotat cu X lei mai mic”, apoi arată datele, ofertele și condițiile. Formularea „Merită schimbat furnizorul” cere evaluarea costului relevant, a acoperirii, a eligibilității și a incertitudinilor conform motorului. În modul cu snapshot se poate arăta un exemplu retrospectiv; nu un îndemn de cumpărare actuală.

Fișa conține: produsele incluse și excluse, factura/reperul, costul actual și alternativ pe aceeași bază, transport/prag minim/card/contract, numărul de livrări/opriri, atributele produselor și condițiile încă neverificate. Utilizatorul poate respinge sugestia cu motiv „am preț negociat”, „produs nepotrivit”, „condiție neîndeplinită” sau „nu mă interesează”; motivul ajustează recomandările firmei, nu faptele publice.

Prețul privat introdus trebuie să aibă furnizor, produs, valoare, bază fiscală cunoscută/necunoscută, cantitate minimă, propria dată/perioadă și sursă (ofertă/factură/manual). Rămâne privat firmei și arată „Valabilitate declarată de firmă, neverificată automat”. În E1b permite un scenariu curent declarat, condiționat de datele firmei; nu este o observare live și nu dovedește costul la checkout. O recomandare privind gama completă nu se deduce din avantajul unui singur articol.

Stări: dovezi insuficiente → „Nu putem recomanda schimbarea pe baza datelor existente”, cu motiv concret; cost total necunoscut → prezintă comparația parțială și informația necesară; ofertă expirată → recomandare retrasă din cele active, păstrată în istoric; sursă în eroare → nu reetichetează observația veche ca verificare nouă.

### 7.10 Setări, surse și confidențialitate

Setările includ firma activă, preferințele listelor, convențiile de afișare, sursele și datele lor, import/export și retenția documentelor. În etapa locală apare clar unde sunt păstrate datele și că accesul depinde de accesul la calculatorul respectiv; aplicația nu se pretinde securizată pentru echipe doar prin existența unui nume de firmă.

Panoul Surse arată pentru fiecare sursă: aria, tipurile de date, ultima colectare reușită, data/validitatea prețurilor, starea adaptorului și câmpurile lipsă. Numărul înregistrărilor de catalog este separat de numărul ofertelor utilizabile. O reîmprospătare viitoare are jurnal și rezultat verificabil, iar eșecul nu șterge ultima probă validă.

Exportul oferă documentele originale păstrate, datele confirmate, corecturile/asocierile și proveniența într-un format documentat. Ștergerea distinge „șterge originalul păstrând datele confirmate” de „șterge documentul și datele derivate”. Efectele asupra istoricului și recomandărilor se arată înainte de confirmarea ștergerii; datele derivate afectate se elimină/recalculează. Retenția și backupurile trebuie explicate conform comportamentului implementat, fără promisiunea unei ștergeri din copii care nu au fost gestionate.

În etapa cu echipe, selectorul firmei active este persistent; drepturile de acces și verificarea izolării sunt condiții de lansare, nu cosmetizare ulterioară. Cheile surselor/OCR și documentele private nu apar în codul sau răspunsurile trimise clientului fără nevoie. Jurnalele și analiticele nu includ conținutul integral al facturilor.

### 7.11 Conturi, acces la firmă și emailuri - E4/E5

[Specificația de acces și email](ACCES_SI_EMAIL.md) definește înregistrarea/loginul real, ecranul de verificare/retrimitere, recuperarea prin provider, schimbarea adresei, onboardingul de firmă, invitațiile și rolurile Proprietar/Administrator/Achizitor/Cititor. Ecranele afișează firma și rolul activ, explică linkurile expirate/folosite și păstrează ciornele când sesiunea expiră. În E1a nu se activează formulare de cont simulate.

Emailurile de acces și securitate sunt distincte de preferințele opționale pentru import/OCR și de alertele de preț din E5. Utilizatorul poate vedea dacă mesajul este solicitat, acceptat de serviciu, livrat sau eșuat; nu se pretinde citire/livrare dintr-un răspuns HTTP. Preferințele de marketing sunt separate, inactive implicit și nu condiționează contul. Documentele private și exporturile se accesează în aplicație după verificarea drepturilor, fără atașamente publice trimise automat.

## 8. Reguli transversale pentru stări și limbaj

| Situație | Text/comportament obligatoriu |
|---|---|
| Încărcare locală sau calcul | Indicator scurt; păstrează contextul și datele introduse; nu simulează procente fără progres măsurabil |
| Niciun rezultat | Distinge „nu am identificat produsul” de „nu există cotație utilizabilă în sursele încărcate” |
| Eroare de rețea/adaptor | Arată sursa afectată, ultima observație păstrată și reluare; nu transformă lipsa în preț zero |
| Necunoscut | „Nespecificat de sursă”, „De confirmat” sau „Nu poate fi calculat”, după caz |
| Date vechi | Data absolută lângă sumă; eligibilitatea pentru recomandare respectă politica sursei |
| Ofertă incompletă | Subtotal și condiții lipsă; fără etichetă de cost total |
| Schimbare de context | Recalculează la schimbarea zonei, firmei, cantității, eligibilității ori alternativei; explică rezultatul invalidat |
| Acțiune reușită | Confirmare scurtă, cu legătură către rezultatul salvat; nu doar toast care dispare |
| Editare/ștergere | Păstrează ciornele; anulare la modificări mici, confirmare clară când se șterg documente/date |

Limbajul folosește „date citite din document” în loc de jargon OCR în fluxul normal și „produs identic / alt ambalaj / alternativă” în loc de scoruri interne. Detaliile tehnice sunt accesibile pentru audit, dar nu blochează sarcina principală. Avertismentele sunt punctuale și apar lângă decizia pe care o afectează.

## 9. Acceptare funcțională și UX

Aceste scenarii completează testele detaliate din motor și plan:

1. Pe un ecran de 360 px, utilizatorul construiește fără asistență o listă cu laptele Zuzu 1,5% 1 l, cerința de cafea Jacobs 250 g și Borsec apă plată 2 l, câte o unitate, și găsește sursa/data fiecărei cotații. Pentru cafea vede varianta Alintaroma/Intense și ambiguitatea denumirilor comerciale înainte de orice asociere. Pe 320 px pagina nu are scroll orizontal.
2. Proba Slatina reproduce suma publicată de **33,86 lei** la Supeco pentru aceste trei cotații, în secțiunea de date raportate de sursă. O numește „Sumă a cotațiilor grupate de sursă - comparație comercială nevalidată”. Nici această sumă, nici cele 15 seturi cu toate cotațiile nu devin coșuri semantic validate sau checkout; lipsurile de variantă, bază a prețului și costuri rămân vizibile.
3. O cotație Monitor cu `Price ≤ 0`, preț invalid ori `Pricedate` absent/invalid nu poate deveni minimul clasamentului. Un rând Lidl cu preț valid și fără dată individuală rămâne vizibil cu incertitudinea declarată; poate apărea într-o estimare condiționată distinctă, fără recomandare fermă curentă ori dată inventată. Un răspuns parțial arată câte linii sunt acoperite și nu concurează ca total complet.
4. Cafeaua 500 g apare la „Alt ambalaj” numai după validarea aceleiași variante. Cererea de 250 g arată plata întregului pachet de 500 g și surplusul; reducerea la lei/kg nu devine automat economie în numerarul cheltuit.
5. Laptele 3,5% nu intră în comparația strictă pentru 1,5%. Un toner cu compatibilitate neconfirmată și un laptop cu RAM/stocare/condiție diferite nu primesc eticheta „produs identic”.
6. Un XML/CSV suportat poate fi importat, revizuit și confirmat; datele originale și corecția sunt accesibile. O diferență aritmetică materială împiedică confirmarea până la rezolvare. Testul folosește un fixture etichetat, nu pretinde că este factura utilizatorului.
7. O fotografie sau un PDF scanat fără adaptor OCR funcțional nu produce linii simulate. Ecranul indică indisponibilitatea citirii și permite continuarea manuală.
8. O linie de factură confirmată dar neasociată intră în cheltuieli și rămâne exclusă din economia pe produs, cu explicație. Reimportul aceluiași document nu dublează totalul.
9. O factură istorică comparată cu snapshotul afișează ambele date și „diferență”, fără „economie realizată”. O ofertă privată introdusă cu altă dată își păstrează data și eticheta valabilității declarate; un rezultat mixt nu aplică data 05.10.2026 întregii comparații și nu se prezintă ca live. Un cost de transport necunoscut împiedică o recomandare necondiționată de schimbare a furnizorului.
10. Toate acțiunile principale sunt utilizabile cu tastatura, au focus vizibil și etichete; mesajele critice nu depind de culoare. Testele automate de accesibilitate sunt completate de verificarea manuală a fluxului pe telefon.
11. Exportul și ștergerea au rezultat verificabil pentru datele firmei locale; după ștergere, documentul nu mai contribuie la istoricul și recomandările active. Comportamentul backupurilor este documentat înainte de activarea lor.
12. Într-un test moderat cu minimum trei utilizatori din publicul țintă, fiecare trebuie să poată explica din ecran dacă oferta este identică, alternativă sau doar asociată de sursă, dacă suma este completă și din ce dată provin prețurile. Confuzia asupra oricăruia dintre aceste trei puncte blochează acceptarea UX pentru pilot și duce la revizuirea textului/layoutului. Acest test cu persoane reale se face înainte de pilot; nu blochează verificarea tehnică locală E1a în lipsa participanților.
13. Pentru E4, un utilizator parcurge loginul, verificarea adresei, invitația, alegerea firmei și recuperarea reală pe conturi de test. Un link expirat, adresă nepotrivită, rol insuficient și sesiune revocată nu permit accesul la date; mesajul explică reluarea permisă. Gates G4-ACCES/G4-FIRME/G4-UX din [ACCES_SI_EMAIL.md](ACCES_SI_EMAIL.md) sunt obligatorii înainte de pilotul găzduit.
14. Pentru emailurile E4, testele acoperă retry/restart fără duplicate normale, link revocat sau expirat, provider indisponibil, bounce/reclamații și retragerea preferinței în timpul cozii. Utilizatorul distinge cererea de trimitere de livrarea documentată. Alertele E5 includ condițiile și datele sursei și nu transformă snapshoturile în oferte curente.

## 10. Limite asumate și extindere

Catalogul de 104.794 înregistrări nu echivalează cu 104.794 produse validate sau disponibile. Cele 18/19 magazine sunt rezultate ale probelor geografice, iar cele 2.444 de rânduri Lidl nu conțin stoc, EAN sau valabilitate pe articol. Expunerea acestor limite în interfață este o cerință de produs permanentă, nu un avertisment temporar de prototip.

Electronicele și alte categorii intră prin aceeași structură de nevoie, variantă, ofertă și evidență, dar cu reguli specifice. Cercetarea Compari.ro susține câteva lecții concrete: [cerințele de feed](https://www.compari.ro/static/feed-requirements.html) separă numele, producătorul, codul, categoria și condițiile livrării; [documentația de asociere](https://www.compari.ro/static/product-pairing.html) cere identificatori și atribute specifice categoriei; [stările ofertelor](https://www.compari.ro/static/displayed-products.html) disting ofertele asociate de cele aflate în procesare. Adoptăm această explicitare în produs, fără a presupune algoritmul intern ori un API de export. Datele Compari nu sunt sursă implicită a aplicației.

Clasamentul principal urmează costul comparabil și condițiile declarate. Eventualele oferte promovate plătit trebuie etichetate și separate și nu pot modifica economia calculată. Este o regulă proprie de produs, motivată și de existența opțiunilor comerciale descrise în [setările Compari pentru comercianți](https://www.compari.ro/static/settings.html), nu o afirmație despre toate clasamentele sale.

Decizia de lansare cu date actualizate, OCR extern și conturi depinde de adaptorii funcționali, securitate, surse și condiții de utilizare verificate. Prima versiune locală rămâne utilă și testabilă prin catalogul curatat, coșurile explicabile și istoricul introdus/confirmat de utilizator, fără a pretinde aceste servicii.
