# Revizie a comparațiilor inteligente pe probe reale

**5 octombrie 2026. Revizie locală, fără acces la rețea și fără modificarea probelor.**

Lipsa EAN nu justifică un singur mesaj nediferențiat pentru toate ofertele. Probele conțin marcă, denumire, procent de grăsime, gramaj sau volum și uneori variantă. Aceste dovezi permit candidați explicați și estimări condiționate. Nu permit confirmarea tuturor SKU-urilor, a stocului ori a sumei finale de plată.

## Dovezi și clasificări utile

| Produs cerut | Dovezi reale | Concluzie utilă |
|---|---|---|
| Zuzu lapte 1,5%, 1 l, `1012187` | 16 cotații Slatina și 19 București. Toate denumirile comerciale valabile indică Zuzu, 1,5% și 1 l; virgula și punctul sunt variante de scriere. | Candidat aceeași variantă pe atributele cunoscute. Tratamentul și materialul ambalajului lipsesc. Nu este SKU confirmat. |
| Borsec apă plată, 2 l, `1361463` | 15 cotații Slatina și 18 București. `PLATA` și `NECARB` susțin apă necarbogazoasă; marca și volumul sunt explicite. | Candidat aceeași variantă pe atributele cunoscute. Nu se compară automat cu altă marcă sau cu apă carbogazoasă. SGR din nume nu dovedește suma garanției inclusă în preț. |
| Jacobs Kronung 250 g, `1013048` | Catalogul global spune generic cafea măcinată 250 g; catalogul din răspunsurile magazinelor spune Alintaroma. În Slatina există trei oferte Intense explicite sau abreviate; București are 11 Intense și șapte Alintaroma. | Separare de variante. Intense contrazice Alintaroma explicit. O denumire generică Kronung nu devine Alintaroma prin completare tacită. |
| Jacobs Kronung 500 g, `1019036` | 17 cotații Slatina și 18 București, fără conflict explicit Intense/Alintaroma în numele salvate. | Candidat pe marcă, familie, formă dacă e declarată și gramaj. Nu este același ambalaj cu 250 g și nu implică aceeași rețetă neprecizată. |

Relația cu cererea utilizatorului și conflictul dintre câmpurile sursei trebuie explicate separat. O cerere generică pentru Kronung nu dovedește că utilizatorul a acceptat orice subgamă. Motorul poate propune variantele separat și permite o alegere explicită; nu trebuie să le unească într-un SKU imaginar.

## Unitatea prețului și estimarea cantității

| Date observate | Calcul care poate fi prezentat | Limită care trebuie păstrată |
|---|---|---|
| `BUC`, `BUCATA`, `BUCATI` și ambalaj scalar coerent | Cantitatea de ambalaje cerută înmulțită cu prețul raportat, ca estimare pe ambalaje. | Codul susține numărarea bucăților, dar nu confirmă checkout, multipack ascuns, condiții de card sau comandă minimă. |
| Lapte 1 l cu `L` sau `Litru` | Estimarea pentru un ambalaj de 1 l este numeric aceeași și dacă prețul este pe litru. Pentru două ambalaje de 1 l, valoarea estimată este `2 x Price`. | Invarianța aritmetică nu confirmă identitatea produsului și nu documentează convenția tuturor categoriilor sursei. |
| Borsec 2 l cu `L` sau `Litru` | Se poate arăta ipoteza explicită că prețul raportat este pe ambalaj și suma estimată în această ipoteză. | Dacă prețul ar fi per litru, diferența ar avea factorul doi. Nu se normalizează automat drept lei/l verificați. |
| Jacobs 250 g cu `K` sau `Kg` | Ipoteză explicită pe ambalaj, separată de o interpretare per kg. | Diferență posibilă de factor patru. Faptul că prețul seamănă cu cel din alte magazine nu documentează convenția câmpului. |
| Jacobs 500 g cu `K` sau `Kg` | Ipoteză explicită pe ambalaj. | Diferență posibilă de factor doi; nicio conversie verificată doar din titlu. |
| Gramaj Lidl scalar `250g`, `500g`, `1l` | Perechea denumire, gramaj și preț susține o estimare a numărului de ambalaje ale rândului respectiv. | Valabilitatea individuală, stocul, SKU și costul final lipsesc. Rândul reprezintă lista rețelei, nu un magazin geografic verificat. |
| Gramaj Lidl `per kg` | Bază distinctă pentru o cerere exprimată explicit în kg. | O cantitate de o bucată nu devine un kg. Unitatea cererii trebuie cunoscută. |
| Multipack Lidl, de exemplu `8x200Foi` | Structură de ambalaj distinctă, cu opt componente și 200 foi dacă parserul o susține. | Nu se confundă opt role cu opt pachete și nu se compară pe foaie fără dimensiuni comparabile. |

Exemple numerice ale ipotezei pe ambalaj: Supeco Zuzu 1 l la 6,09 lei, două ambalaje, produce 12,18 lei estimat; Supeco Jacobs 250 g la 23,99 lei, două ambalaje, produce 47,98 lei în ipoteza pe ambalaj. A doua valoare cere și revizia variantei generice. Nu reprezintă două economii realizate și nu sunt totaluri de plată.

## Lidl și alternativele între surse

- Rândul `615`: Jacobs Kronung cafea măcinată 250 g, 29,99 lei. Susține un candidat pentru familia Jacobs 250 g, fără completarea variantei Alintaroma.
- Rândul `614`: Jacobs `Krönung` măcinată 500 g, 49,99 lei. Titlul original conține corect `ö`; fișierul JSON are zero caractere U+FFFD. Aliasul lexical Kronung permite recuperarea familiei, fără a confirma singur SKU-ul.
- Rândul `1729`: Zuzu 1,5%, 1,8 l, 13,99 lei. Are alt ambalaj decât cererea de 1 l; nu trebuie afișat ca aceeași variantă și același ambalaj. Compararea pe volum cere acceptarea altui ambalaj și o bază explicită.
- Rândurile `1721` și `1740`: Pilos 1,5%, 1 l, respectiv ESL la 4,39 lei și UHT la 4,75 lei. Pot fi alternative de evaluat, cu marcă și tratament distincte, fără substituție automată a Zuzu.
- Rândul `587`: Pilos lapte condensat 340 g apare în categoria comercială `Cafea`. Categoria sursei poate descrie raionul sau utilizarea. Nu dovedește că produsul este cafea ori lapte de consum comparabil cu Zuzu.
- Cele opt duplicate exacte nume plus gramaj, uneori cu prețuri diferite, rămân rânduri separate. Selecția celui mai mic nu este o deduplicare justificată.

## Ce trebuie să spună rezultatul

Pentru fiecare ofertă, explicația trebuie să distingă atributele concordante, atributele decisive necunoscute, conflictele și ipoteza de calcul. O potrivire după marcă, 1,5% și 1 l este mai utilă decât o etichetă generică de neconfirmare. Un conflict Intense/Alintaroma este mai grav decât lipsa unui GTIN și nu poate fi ascuns de un scor lexical.

Un clasament estimat se limitează la aceeași cerere, aceeași acoperire și ipotezele afișate. Un subtotal parțial nu câștigă împotriva unei liste acoperite. Diferența dintre două cotații poate fi afișată drept diferență estimată între ofertele salvate, cu baze compatibile. Fără achiziție confirmată și condiții comparabile, nu înseamnă că firma a economisit deja și nu justifică o recomandare fermă de schimbare a furnizorului.

## Audit după integrare

Auditul motorului `attributes-explainable-2` a citit baza locală prin conexiune SQLite `mode=ro`. Comparațiile au fost executate într-o copie separată în memorie. Nici baza de lucru, nici fixture-urile sau probele originale nu au fost modificate. Nu a fost rerulată întreaga suită de teste.

| Rezultat verificat | Slatina 5 km | București 1 km |
|---|---|---|
| Zuzu 1,5%, 1 l | 16 candidați; 13 baze echivalente de 1 l și trei baze pe bucată | 19 candidați; două baze echivalente de 1 l și 17 baze pe bucată |
| Jacobs 250 g | Zero candidați; trei conflicte și 14 oferte cu detalii lipsă | Zero candidați; 11 conflicte și șapte oferte cu detalii lipsă |
| Jacobs 500 g | 17 candidați; două baze pe bucată, 15 baze ambigue | 18 candidați; 16 baze pe bucată, două baze ambigue |
| Borsec 2 l | 15 candidați; două baze pe bucată, 13 baze ambigue | 18 candidați; 16 baze pe bucată, două baze ambigue |

Cele 17 verdicturi pentru cafeaua de 500 g nu inventează forma cafelei. Catalogul global și cel contextual spun generic Kronung 500 g și au `form=null`. Ofertele Supeco/Profi extrag forma măcinată din `R&G` sau `MACINATA`; ofertele Kaufland `VID` și Lidl din Monitor păstrează forma necunoscută. Verdictul de candidat compară marca, tipul, gramajul și familia cererii generice. Explicația nu trebuie formulată drept verificare a cafelei măcinate ori a unei rețete exacte.

Catalogul returnează intervalul cotațiilor raportate, distinct de minimul eligibil pentru estimarea cantității:

| Caz | Interval raportat | Minimul cu bază eligibilă pentru estimare |
|---|---|---|
| Jacobs 500 g, Slatina | 39,99 - 55,75 lei | 49,99 lei |
| Jacobs 500 g, București | 49,79 - 55,75 lei | 49,99 lei |
| Zuzu 1 l, Slatina | 6,09 - 7,35 lei, 16 oferte | 6,09 lei |
| Zuzu 1 l, București | 6,39 - 8,15 lei, 19 oferte | 6,39 lei |

Fără scenariu, rezumatul Zuzu include explicit ambele zone: 35 observații, `scope=all_saved_areas`, interval 6,09 - 8,15 lei. Acest rezumat nu trebuie etichetat drept intervalul unei singure zone. În catalog, eticheta „de la” trebuie înțeleasă drept preț raportat, nu cel mai mic cost verificat pentru cantitatea cerută.

Paginarea verificată pe catalogul Monitor cu preț în Slatina, ordonat crescător după preț și pagini de câte două produse, returnează exact patru ID-uri distincte: Borsec `1361463`, Zuzu `1012187`, Jacobs `1013048` și `1019036`. A doua pagină încheie cursorul. Căutarea `W5 Laveta` în Lidl păstrează separat rândurile duplicate `2246` la 3,99 lei și `2247` la 5,99 lei; nu combină rândurile ori prețurile într-un produs canonic confirmat.

Comparațiile executate pe date reale au produs:

- **Două ambalaje Zuzu 1 l, Slatina:** 16 estimări complete, între 12,18 și 14,70 lei; diferența între estimări este 2,52 lei. Supeco produce corect 12,18 lei.
- **Zuzu 1 l + Jacobs 500 g + Borsec 2 l, Slatina:** două coșuri estimate complete, magazinele Kaufland `1398` și `1418`, ambele 61,07 lei. Celelalte estimări parțiale nu intră în clasament.
- **Aceeași listă, București:** 16 coșuri estimate complete, între 60,87 și 61,27 lei; diferența este 0,40 lei.
- **Lista cu Jacobs 250 g:** nu produce coș estimat complet, deoarece varianta sau forma cafelei nu este suficient precizată. Grupele de cotații rămân inspectabile.
- **0,5 ambalaje Zuzu:** nu produce estimare pe pachete. O jumătate de articol nu este convertită tacit în 0,5 l.

În toate aceste comparații, `payable_total`, `savings` și `estimated_savings` rămân null. Unitățile `K`, `Kg`, `L` sau `Litru` pentru ambalaje diferite de 1 l sunt grupate ca valori raportate, fără multiplicarea lor în totalurile estimate. Exemplul aritmetic ipotetic de 47,98 lei pentru două pachete Supeco Jacobs 250 g nu este un total activat în motor.

Pentru Borsec `1011559`, rezumatul propriu rămâne fără preț. Motorul expune distinct 15 oferte asociate în Slatina și 18 în București, provenite din `1361463`, cu `source_item_id` și explicație de asociere. Nicio cotație zero nu a devenit gratuitate.

### Problemă găsită la deschiderea dovezii

În versiunea auditată, opțiunea asociată și panoul dovezii pot folosi referințe diferite. `get_evidence(observation_id)` reface verificarea față de catalogul propriu al ofertei; interfața transmite numai ID-ul observației și pierde cererea din comparație.

- Pentru Pilos ESL `lidl:1721`, opțiunea UHT `lidl:1740` este `variant_conflict`. Aceeași observație deschisă prin endpointul dovezii devine `same_variant_candidate`, deoarece referința a devenit UHT.
- Pentru Jacobs `monitor:1013048`, opțiunea `lidl:615` este `needs_details` pentru Alintaroma. Panoul propriu al rândului Lidl devine candidat, deoarece referința sa generică nu mai cere Alintaroma.

Constatarea a fost trimisă editorilor motorului și interfeței. Remediul trebuie să păstreze referința cererii la deschiderea dovezii sau să prezinte panoul drept proveniență, fără un verdict care pare raportat la cererea anterioară. Datele originale și identificatorii observațiilor sunt corecți; contextul comparației se pierde în această navigare.

**Remediu verificat punctual:** fiecare ofertă transmite acum `reference_item_id`, iar endpointul dovezii acceptă aceeași referință. Ambele cazuri reale au păstrat exact verdictul, `reference_profile` și `match_reasons`: Pilos ESL față de UHT rămâne conflict, iar Jacobs Alintaroma față de rândul generic Lidl rămâne cu detalii lipsă. Răspunsul declară `evaluation_scope=selected_product`. Fără referință, endpointul compatibil declară explicit `evaluation_scope=source_product`. Codul interfeței transmite parametrul mai departe la deschiderea dovezii; verificarea vizuală completă este făcută separat de integrare.

La încheierea auditului, toate cele 11 hashuri SHA-256 ale probelor originale coincid cu manifestul. Documentul nu conține caractere em dash sau en dash.
