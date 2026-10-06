# Revizia interfeței și a comparațiilor

5 octombrie 2026. Revizie locală a aplicației, după feedbackul privind prețurile greu de găsit, explicațiile repetitive și lipsa comparațiilor utile.

## Ce s-a schimbat

Interfața folosește rânduri compacte pentru catalog și listă, cu prețul și numărul ofertelor vizibile direct. Filtrul „Doar produse cu preț” este activ implicit și se aplică în baza de date înainte de paginare. Catalogul complet rămâne accesibil prin debifare. „Minim raportat” descrie cotațiile salvate; „Preț comparabil de la” folosește ofertele cu caracteristici și bază de preț corespondente.

Comparația are o matrice produs-magazin, minimum comparabil, diferențe între prețuri și grupuri distincte de variante. Magazinele cu coșuri complete și cele cu minime comparabile apar primele. Etichetele diferențiază caracteristicile corespondente, conflictele și detaliile lipsă. O bază ambiguă este indicată în tabel, chiar dacă marca și gramajul corespund. Explicațiile și proveniența se deschid la cerere.

Motorul extrage atributele declarate și păstrează diferențele de marcă, ambalaj, grăsime, formă, variantă și tratament. Lipsa unei variante nu devine echivalență. De exemplu, Jacobs Intense nu este unit automat cu declarația Alintaroma din sursă. Deschiderea unei alternative păstrează produsul cerut ca referință; explicațiile sunt în română și indică valoarea care lipsește.

Estimările înmulțesc numărul întreg de ambalaje numai pentru o bază eligibilă. Pentru exact 1 l, prețul pe litru și pe ambalaj au aceeași valoare numerică. Coșurile complete sunt ordonate separat; un magazin cu poziții lipsă nu primește total comparabil. Diferențele între estimări sunt prezentate fără a declara economii realizate. Contractul este în [SMART_CONTRACT.md](../backend/SMART_CONTRACT.md), iar auditul pe probe reale este în [REVIZIE_COMPARATII.md](REVIZIE_COMPARATII.md).

Toate em dash-urile și en dash-urile din fișierele text ale proiectului au fost înlocuite cu cratime obișnuite. Originalele din `probe-data` au rămas intacte.

## Verificări

- `scripts/Check-Local.ps1`: 74 teste de integrare/regresie, 32 verificări ale parserului și build TypeScript/Vite trecute. După ajustarea textelor explicative, cele opt teste afectate au trecut, inclusiv noua regresie de localizare. Suita curentă conține 75 teste; nu a fost rerulată integral doar pentru această ajustare de text.
- Revizie independentă pe copia în memorie a datelor reale: minimum raportat distinct de minimum eligibil, separarea variantelor Jacobs, cantități întregi, alternative între înregistrări, paginare fără duplicate și excluderea coșurilor incomplete.
- Flux în browser: catalogul cu preț are 2.448 înregistrări, catalogul complet 107.226; ordonarea crescătoare și revenirea filtrului verificate.
- Lista nouă cu Zuzu 1 l, Jacobs 500 g și Borsec 2 l produce două estimări complete la 61,07 lei în Slatina. Două ambalaje de lapte ridică estimarea la 67,76 lei. Cantitatea a fost readusă la unu după test.
- Aceeași listă în București produce 16 estimări complete, cu intervalul 60,87 - 61,27 lei și diferența de 0,40 lei afișată. Lista de demonstrație a fost creată separat; listele existente sunt păstrate.
- Butonul de extindere afișează toate cele 16 coșuri; ultimul arată 61,27 lei și +0,40 lei față de prima opțiune. Scenariul listei de demonstrație a fost readus la Slatina după test.
- Alternativa Lidl pentru Jacobs 250 g păstrează verdictul „Detalii de verificat” în panoul dovezii, inclusiv lipsa variantei Alintaroma.
- Layoutul listei și comparației a fost verificat la 320 și 390 px. Defectul de overflow din antetul ascuns al tabelului a fost reparat prin poziționarea corectă a containerului, fără ascunderea globală a overflowului.
- La 320 px, documentul are `clientWidth=scrollWidth=305`; la 390 px are `clientWidth=scrollWidth=375`. Tabelul se derulează local prin tastatură, iar pagina rămâne la `scrollLeft=0`. Consola browserului nu raportează erori sau avertismente. Viewportul a revenit la dimensiunea implicită.
- Hashurile SHA-256 ale celor 11 probe originale coincid cu manifestul. Scanarea surselor și a interfeței construite nu găsește em dash sau en dash.

Avertismentul preexistent Starlette/TestClient privind httpx apare în testele Python, fără eșecuri. Datele rămân snapshoturi salvate, fără actualizare live ori stoc confirmat. OCR-ul facturilor și recomandările bazate pe istoricul achizițiilor rămân în etapele ulterioare ale planului.

Capturi finale: [lista desktop](images/lista-desktop.jpg), [comparația desktop](images/comparatie-desktop.jpg), [comparația mobilă](images/comparatie-mobile.jpg).
