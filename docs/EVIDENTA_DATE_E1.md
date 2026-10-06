# Evidența datelor în E0/E1a

**5 octombrie 2026 · Date salvate, utilizare exclusiv locală.**

Prima aplicație importă probele existente; nu colectează prețuri noi la pornire. Datele sunt oferite drept cotații raportate, cu proveniență și limite. Un rezultat de căutare sau un ID comun al sursei nu confirmă automat identitatea produsului, disponibilitatea ori totalul de plată.

## Fișiere și integritate

[Manifestul](../fixtures/snapshot-manifest.json) consemnează SHA-256 și dimensiunea efectivă a tuturor celor **11 fișiere originale** din `probe-data`. Importul verifică hashurile înainte de folosirea datelor. Originalele nu sunt rescrise de aceste fixture-uri sau de teste.

`requests.json` conține momente de colectare numai pentru trei răspunsuri. Ele se păstrează ca șiruri exacte, inclusiv fracțiunea de secundă și offsetul `+00:00`:

| Răspuns | Moment documentat al colectării |
|---|---|
| Slatina, șapte ID-uri | `2026-10-05T14:31:03.9187173+00:00` |
| București, șapte ID-uri | `2026-10-05T14:31:04.5721154+00:00` |
| Slatina, lapte separat | `2026-10-05T14:31:04.7946174+00:00` |

Pentru catalog, rețele, răspunsul celor trei produse și fișierele Lidl, momentul colectării este **null**. Ora importului și ora înregistrării manifestului sunt evenimente distincte; nu completează această lipsă.

Monitor declară `05.10.2026 04:00` în cotațiile pozitive și datate ale celor două scenarii. Fișierele nu declară fusul orar al acestui câmp; forma originală rămâne accesibilă. Data fișierului Lidl și proprietățile XLSB (`created`/`modified` din 4 octombrie) nu reprezintă valabilitatea prețului fiecărui produs. Manifestul păstrează explicit această distincție.

Dimensiunile răspunsurilor raportate în `requests.json` diferă cu doi octeți de fișierele XML salvate. Manifestul păstrează separat dimensiunea original raportată și dimensiunea fișierului local; hashul se aplică exact octeților locali. Manifestul nu certifică independent autenticitatea răspunsului de la distanță.

## Numărători reproductibile

| Set | Evidența salvată |
|---|---|
| Catalog Monitor | 104.794 rânduri; 12 denumiri goale |
| Lidl | 2.444 rânduri; 34 categorii ale sursei |
| Slatina, raza 5 km | 18 magazine; 126 poziții cerute; 65 cotații pozitive și datate |
| București, raza 1 km | 19 magazine; 133 poziții cerute; 73 cotații pozitive și datate |
| Total observații importate | 2.703, incluzând 2.444 poziții Lidl și 259 poziții Monitor |

Numărul de cotații utilizabile pentru afișare nu este numărul de produse identice verificate. Magazinele celor două zone nu sunt adunate pentru o promisiune de acoperire națională. Existența categoriei în interfață nu dovedește existența unor oferte în acea categorie.

## Cazuri reale care împiedică o concluzie automată

[Fixture-ul semantic](../fixtures/semantic-regressions.json) păstrează denumirile, unitățile, categoriile, prețurile, ID-urile și locatorii originali pentru regresii:

- **Jacobs:** `1988/10692315574` este numit `INTENSE`; `2117/10692750159` este `ALINTAROMA`. Ambele sunt asociate catalogului `1013048`. Varianta contradictorie este incompatibilă; varianta concordantă păstrează statutul de asociere a sursei și lipsurile de evidență.
- **Ariel/Fairy:** `1449689` este etichetat `LAPTE`, iar `1282436` este etichetat `DEZINFECTANTI`. Numele produsului comercial este gol în aceste poziții; conflictul trebuie evaluat și din numele catalogului. Categoria brută rămâne păstrată, iar produsul intră la revizie/de clasificat.
- **Baza prețului:** `K`, `Kg`, `L` și `Litru` nu confirmă că prețul este pe pachet, kilogram sau litru. Gramajul din titlu nu justifică singur conversia sau multiplicarea.
- **Borsec:** catalogul `1011559` are preț zero și dată goală în probe. În aplicație înseamnă lipsă cotație, nu gratuitate. Nu moștenește prețul de 3,78 lei al catalogului asemănător `1361463`.
- **Duplicate Lidl:** există opt rânduri suplimentare cu nume și gramaj identice exact, uneori cu prețuri diferite. Toate rămân distincte. Perechea `BIO`/`bio` de la rândurile 183/413 este suplimentar un candidat lexical, nu un duplicat exact. Rândul Excel este locator al dovezii în acel fișier, nu SKU stabil.

[Taxonomia](../config/taxonomy.json) definește 54 categorii pentru alimente, băuturi, curățenie, igienă, birotică, consumabile pentru imprimante, electronice, electrocasnice, mobilier, materiale și alte domenii. Cele 34 etichete Lidl au mapări explicite: 33 categorii provizorii pentru navigare; `OTC` rămâne de clasificat pentru revizie. Grupele generale `Baby`, `Proaspete` și `Uz casnic` rămân generale. Atributele critice sunt declarate per categorie; subcategoriile noi au o schemă pentru navigare, care cere revizie specifică înaintea comparațiilor de echivalență. Echivalențele automate sunt dezactivate în E1a; sursa brută rămâne inspectabilă.

## Ce verifică testele și ce nu demonstrează

[Regresiile aplicației](../tests/test_app_regressions.py) verifică hashurile, momentele documentate/null, refuzul unei probe modificate în copie izolată, importul idempotent, numărătorile reale, variantele Jacobs, categoriile contradictorii, unitățile ambigue, duplicatele și absența unui preț transferat între ID-uri Borsec. Regresiile API verifică separat listele persistente și abținerea de la totalul plătibil/economie când identitatea, baza prețului, cantitatea sau acoperirea sunt insuficiente.

Comanda, din `backend` după setup:

```powershell
..\.venv\Scripts\python.exe -m pytest ..\tests\test_app_regressions.py -q
```

Se folosesc baze temporare separate; originalele nu sunt modificate. Rezultatul executării se consemnează în raportul de livrare. Trecerea acestor regresii nu măsoară precizia matchingului pe piață, stabilitatea unei surse active, acuratețea OCR ori economii realizate. Acestea au seturi de dovezi și etape proprii în [plan](PLAN_IMPLEMENTARE.md).
