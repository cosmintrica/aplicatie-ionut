# Fezabilitate și teste - 5 octombrie 2026

**Un MVP cu surse și produse delimitate este fezabil. Testele nu susțin promisiunea „toate prețurile din România” sau garantarea celui mai mic preț disponibil unei firme.**

Cererea este o aplicație pentru firme mici: utilizatorul introduce o listă de cumpărături (lapte, cafea, consumabile), iar aplicația compară ofertele magazinelor. Textul inițial este păstrat în `CERERE_INITIALA.md`. Acest proiect conține acum probe de acces și parsare, datele colectate și verificări; interfața aplicației nu este încă implementată.

## Ce am executat efectiv

Am făcut șapte cereri HTTP GET către serviciul public Monitorul Prețurilor: catalog, rețele, trei produse din testul precedent, șapte produse în Slatina, aceleași șapte în București și lapte separat în Slatina. Toate au răspuns HTTP 200 cu XML. Am descărcat separat, o singură dată, fișierul oficial Lidl: HTTP 200, 90.088 bytes. Nu au fost necesare conturi, API keys ori ocolirea protecțiilor pentru aceste cereri.

Catalogul Monitorul Prețurilor conține **104.794 de înregistrări**, dintre care 12 cu numele gol; nu am găsit ID-uri duplicate. Sunt ID-uri de catalog, nu o garanție că fiecare înregistrare are oferte actuale. Fișierul are aproximativ 19,8 MB, iar descărcarea testată a durat 4,19 secunde.

| Probă | Magazine returnate | Linii de produs | Prețuri pozitive cu dată validă | Coșuri complete |
|---|---:|---:|---:|---:|
| Slatina, 5 km, cele trei ID-uri anterioare | 18 | 54 | 5 | 0 |
| Slatina, 5 km, șapte ID-uri selectate | 18 | 126 | 65 | 0 |
| București, 1 km, aceleași șapte ID-uri | 19 | 133 | 73 | 0 |
| Slatina, lapte Zuzu separat | 18 | 18 | 16 | 16 |
| Slatina, subcoș alimentar de trei produse, calculat din răspunsul existent | 18 | 54 relevante | 48 | 15 |

Toate prețurile pozitive extrase în aceste probe au `Pricedate = 05.10.2026 04:00`. Aceasta este data declarată de sursă; nu am verificat prețurile la casele magazinelor. Cele 16 oferte pentru Zuzu sunt identice între cererea individuală și cererea cu șapte produse: aceleași magazine, prețuri și date.

## Exemple de cotații de catalog din Slatina

| Produs exact din catalog | ID | Magazine cu preț | Cel mai mic preț raportat | Magazin |
|---|---:|---:|---:|---|
| Zuzu lapte 1,5%, 1 l | 1012187 | 16 | 6,09 lei | Supeco Slatina |
| Jacobs Kronung cafea măcinată, 250 g | 1013048 | 17 | 23,99 lei | Supeco Slatina |
| Borsec apă plată, 2 l | 1361463 | 15 | 3,78 lei | Supeco Slatina |

Pentru câte un articol din fiecare rând, suma prețurilor raportate este **33,86 lei la Supeco**, **41,07 lei la cele două Kaufland** și **42,87 lei la Carrefour Market Aleea Muncii**. Sunt 15 magazine cu toate cele trei cotații disponibile. Sumele nu includ un calcul separat al transportului, garanției SGR sau beneficiilor personale/contractuale; nu reprezintă un checkout verificat.

**Precizare după verificarea identității comerciale:** cele 15 coșuri sunt complete numai după ID-urile catalogului. Ofertele Jacobs din același ID includ denumiri Intense și Alintaroma la Mega Image, iar Supeco nu precizează această variantă. Identitatea comercială nu este confirmată între toate ofertele. Sumele de mai sus nu pot fi folosite ca recomandare de economii pentru produse identice fără revizuirea atributelor. Dovezile sunt în `docs/VALIDARE_IDENTITATE_DATE.md`.

Magazinele Lidl din răspunsul local au preț pentru cafeaua Jacobs 250 g, dar nu și pentru celelalte două produse ale acestui coș. Absența unei cotații nu demonstrează absența fizică a produsului din magazin.

## Probleme demonstrate de probe

- **Zero nu este un preț de cumpărare.** Pentru produsele fără cotație utilizabilă apar `Price=0` și data goală. Parserul exclude prețurile zero/negative/nevalide și datele absente/nevalide.
- **Totalul serverului poate fi parțial.** În primul test, Supeco are `Basketprice=4.65`, dar doar unul din cele trei articole are preț. Scriptul păstrează separat subtotalul și lista lipsurilor; `CompleteTotal` este nul pentru un coș incomplet.
- **Catalogul singur nu rezolvă produsul.** `1011559` („Apa Min Necarb 2l Borsec.”) nu a avut nicio cotație în cele două zone, în timp ce `1361463` („Borsec Apa Plata 2l”) a avut. Numele asemănător nu este suficient pentru a stabili echivalența.
- **Non-alimentarele au acoperire de verificat.** Cele două ID-uri testate pentru Fairy și Ariel nu au avut prețuri în niciuna dintre zone. Nu extrapolăm această probă la toate consumabilele.
- **Identificatorii diferă.** Căutarea de prețuri folosește `Catprod.Id`, nu `Product.Id` al comerciantului. Rețeaua se identifică prin `Retailnetwork.Id`; unele câmpuri `Retailnetwork.Name` conțin numele magazinului.
- **Unitățile nu sunt uniforme.** Pentru același lapte apar `L`, `Litru`, `BUC`, `BUCATA`. O aplicație trebuie să confirme gramajul, ambalajul și baza prețului înainte de comparații pe litru/kg ori cantități multiple.

## Fișierul oficial Lidl

Am citit **2.444 de rânduri de produse din 34 de categorii**, toate cu preț numeric. Fișierul are denumire, gramaj, categorie și preț; nu are GTIN/EAN, stoc sau data de valabilitate pe articol. Metadata indică modificarea fișierului la 4 octombrie, 23:08:50 București, fără să dovedească valabilitatea fiecărui preț. Au existat opt rânduri suplimentare cu aceeași cheie nume+gramaj.

Exemple extrase: Pilos lapte 3,5% ESL 1 l - 5,29 lei; W5 detergent de vase 500 ml - 4,69 lei; Floralys hârtie igienică 8×200 foi - 9,99 lei. Acestea sunt produse diferite de cele din tabelul Monitorul, deci nu le substituim automat.

[Pagina Lidl](https://www.lidl.ro/c/preturile-la-zi/s10019622) declară lista sortimentului permanent, publicată luni-vineri, prețuri identice în rețea și garanția SGR exclusă. [Fișierul descărcat](https://www.lidl.ro/explore/assets/webPriceData/ro/preturiZilniceLidl.xlsb) este XLSB. Scriptul local citește valorile stocate ale acestui fișier; nu este un importator Excel general.

## Acoperire și extindere

Monitorul Prețurilor prezintă ofertele rețelelor participante, cu prețuri informative și disponibilitate dependentă de stoc. Nu constituie un inventar al tuturor comercianților sau al prețurilor negociate pentru firme. [Site oficial](https://monitorulpreturilor.info/), [participanți](https://monitorulpreturilor.info/Home/Participanti).

Nu am identificat documentație oficială publică pentru aceste endpointuri, SLA ori o cotă contractuală. [Implementarea terță gov2-ro](https://github.com/gov2-ro/monitorulpreturilor) descrie o rază de aproximativ 5 km și maximum 50 de magazine pe răspuns. Acestea sunt observații ale terțului, nu limite oficiale demonstrate de probele noastre. Nu am testat plafonul de 50, căutarea națională sau stabilitatea pe termen lung.

Pentru magazine online, [2Performant documentează feeduri CSV/XML pentru comparatoare](https://support.2performant.com/how-to-add-product-feeds-to-your-website), cu preț, produs și câmp GTIN; accesul depinde de acceptarea în programul comerciantului. Este o cale de extindere, nu o sursă universală.

API-urile oficiale găsite pentru [eMAG Marketplace](https://marketplace-api.emag.ro/api-doc) și [Kaufland Global Marketplace](https://www.kauflandglobalmarketplace.com/en/seller-university/selling/listing-via-api-interface/) servesc partenerii/sellerii. Ele nu demonstrează acces public la toate prețurile magazinelor. Nu am găsit documentație de API public pentru prețurile supermarketurilor Lidl/Kaufland România; accesul prin parteneriate rămâne de investigat.

În B2B, [RTC oferă soluții și oferte personalizate](https://www.rtc.ro/rtc-partenerul-tau), iar [METRO descrie beneficii în funcție de cantitate](https://www.metro.ro/devino-client-metro). Aplicația trebuie să distingă prețul public de oferta efectivă a firmei.

Accesul tehnic public nu stabilește automat condițiile de republicare comercială; în cercetarea efectuată nu am identificat o licență explicită pentru endpointurile Monitorul. Condițiile surselor și eventualele acorduri cu furnizorii trebuie clarificate pentru o lansare.

## MVP propus pe baza probelor

Un prim produs poate compara un catalog restrâns de lapte/cafea/apă și consumabile selectate, într-o zonă aleasă: Monitorul pentru ofertele disponibile, fișierul Lidl pentru sortimentul publicat și feeduri acceptate pentru alți furnizori. Interfața ar trebui să afișeze „cel mai mic preț găsit în sursele verificate”, data sursei, produsele lipsă și costurile condiționate.

Utilizatorul trebuie să poată alege produsul exact sau accepta explicit un echivalent. Minimul fiecărui articol și minimul unui coș complet sunt rezultate diferite; cumpărarea din mai multe magazine poate introduce costuri suplimentare.

Hostingul și programarea sunt rezolvabile. Munca continuă se concentrează pe accesul la surse, actualizare, potrivirea produselor și calculul costului efectiv. Scrapingul rămâne o opțiune pentru surse fără export, dar schimbările și protecțiile trebuie evaluate pe fiecare sursă. AI poate ajuta extragerea și propunerea echivalențelor; nu furnizează prețuri nepublicate și nu garantează o potrivire corectă.

## Reproducere și verificări

Din directorul proiectului, în PowerShell 7:

```powershell
.\scripts\Test-MonitorPrices.ps1 -Offline
.\tests\Test-MonitorPricesParser.ps1
```

Prima comandă recalculează rezultatele din snapshoturile salvate, fără rețea. Fără `-Offline`, scriptul descarcă din nou catalogul, rețelele și cele patru probe geografice, apoi suprascrie snapshoturile și raportul JSON. Această variantă de orchestrat downloaduri nu a fost rulată cap-coadă; aceleași cereri HTTP au fost executate individual în această sesiune.

Parserul Monitorul a trecut **32 de verificări de regresie**, inclusiv ID-ul corect, preț zero, date lipsă, coș incomplet, alternative duplicate și răspuns XML de eroare. Scriptul de analiză a fost rulat cu succes offline. Parserul Lidl a citit valorile numerice și textuale ale snapshotului, fără instalări suplimentare.

Date: `probe-data/summary.json`, `probe-data/requests.json`, XML-urile originale și fișierele `probe-data/lidl-*`. Răspunsurile HTTP sunt probe pentru 5 octombrie 2026, nu dovezi de uptime sau de acoperire completă.
