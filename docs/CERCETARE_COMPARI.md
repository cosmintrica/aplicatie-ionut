# Compari.ro: mecanism documentat și lecții pentru aplicația B2B

Verificat la 5 octombrie 2026. Cercetare publică, exclusiv prin surse oficiale Compari.ro; fără cont, solicitări către comercianți, import de cataloage sau testarea unor endpointuri private.

## Concluzia relevantă

Compari.ro demonstrează că agregarea ofertelor din mai multe magazine este realizabilă prin colaborare cu comercianții, identificatori de produs și date structurate. Nu demonstrează că se poate garanta cel mai mic preț din întreaga Românie. Pentru proiectul nostru, mecanismul poate inspira arhitectura; datele Compari nu trebuie presupuse reutilizabile.

## Ce descriu oficial

### 1. Intrarea datelor

Comercianții publică pe propriul site un feed XML/CSV și înregistrează URL-ul în Centrul de clienți. Pagina cerințelor indică descărcare zilnică la 17:00 și procesare inițială de 3-7 zile lucrătoare. Schema include identificator stabil al magazinului, producător, nume oficial, categorie ierarhică, URL și preț brut pentru cantitatea minimă comandabilă. Codul producătorului este obligatoriu la electronice, informatică și electrocasnice. Sunt documentate transportul, termenul de livrare, descrierea, imaginea și atributele; `DeliveryTime=NO` semnalează indisponibilitatea. [Cerințe feed](https://www.compari.ro/static/feed-requirements.html)

Pagina de prezentare actuală menționează și integrări API, în funcție de soluția comerciantului, pentru sincronizarea produselor și stocului. Descrie atât redirecționarea spre magazine, cât și cumpărarea directă pentru produsele din Marketplace. Help Center are încă formularea mai restrânsă, de promovare a ofertelor. Aceste texte trebuie citite în context; nu deducem din ele că fiecare comerciant are API sau că orice produs poate fi comandat în platformă. [Prezentare actuală](https://www.compari.ro/static/despre_noi.html), [Help Center](https://www.compari.ro/static/help-center.html)

### 2. Asocierea produselor

Compari descrie potrivirea pe baza producătorului și codului oficial `ProductNumber`, cu EAN într-un câmp separat pentru accelerarea procesării. Categorizarea folosește categoria declarată, producătorul și numele. EAN este obligatoriu pentru Shopping; cărțile necesită ISBN. Regulile variază pe categorie: parfumurile includ volumul și ambalajul, iar anvelopele dimensiunile și marcajele. Documentația recunoaște prelucrarea diferențelor mici, fără să publice algoritmul, modelele folosite sau rate de precizie. Nu putem afirma că folosesc un anumit sistem AI. [Asociere produse](https://www.compari.ro/static/product-pairing.html)

Produsele asociate apar împreună pe o pagină de comparație. Alte oferte pot rămâne individuale sau în căutare când nu există un corespondent, identificarea nu este finalizată ori datele sunt incomplete. Procesarea este automată în numeroase categorii, dar poate fi periodică în altele. Actualizările sunt periodice; Premium adaugă șase actualizări zilnice și un interval suplimentar configurabil. Aceasta nu constituie o garanție de stoc/preț în timp real. [Status și actualizări](https://www.compari.ro/static/displayed-products.html)

### 3. Monetizare și ordinea ofertelor

Documentația descrie PPC și un multiplicator al costului pe clic care poate promova oferta în secțiunea de oferte evidențiate. Premium este un abonament pentru actualizări suplimentare, statistici și monitorizarea prețurilor. [Setări comercianți](https://www.compari.ro/static/settings.html), [Premium](https://www.compari.ro/static/premium-package.html)

O pagină publică de tabletă explică faptul că ordinea ofertelor ține cont de reputație, evaluări, relația de preț și plata opțională pentru evidențiere. Pagina arată și variante de produs, transport, disponibilitate și sortare. Este un exemplu de comportament observat, nu un audit al tuturor categoriilor sau al algoritmului de ranking. [Exemplu oficial: iPad Air](https://tablet-pc.compari.ro/apple/ipad-air-2026-13-256gb-mh5x4-p1307290243/)

### 4. API și reutilizare

Nu am identificat în paginile publice examinate documentația unui API deschis pentru citirea întregului catalog de prețuri de către o aplicație terță. Mențiunea de API pentru integrarea comercianților nu stabilește un asemenea drept sau serviciu. PDF-ul API pentru programul Magazin de Încredere tratează informațiile de cumpărare și colectarea feedbackului, nu exportul bazei de prețuri. [API Magazin de Încredere](https://www.compari.ro/admin/trustedshop/doc/TrustedShopDocumentation-RO.pdf)

Condițiile de utilizare publicate pe site afirmă protecția conținutului și necesitatea acordului scris anterior pentru folosire. Pagina afișează versiunea din 25 mai 2018; este pagina disponibilă la verificare. Este o constatare despre condițiile publicate, nu o analiză juridică a fiecărui fapt, preț sau drept. Pentru orice integrare reală trebuie stabilite explicit accesul, reutilizarea, imaginile, actualizările și limitele contractuale. [Condiții de utilizare](https://www.compari.ro/static/conditii_de_utilizare.html)

## Ce inferăm și propunem pentru proiectul nostru

Recomandările de mai jos sunt design propus pentru aplicație; nu pretind că descriu implementarea internă Compari.

### A. Catalog general de la început, reguli specifice fiecărei categorii

Separăm entitățile: familia de produse, varianta identificabilă, ambalajul comercial, oferta comerciantului și observația de preț. Identificatorul intern al magazinului nu este identificator universal. Păstrăm GTIN/EAN, cod producător, marcă, model și toate valorile originale pentru audit.

Taxonomia inițială trebuie să prevadă alimente/băuturi, curățenie/igienă, birou/papetărie, consumabile imprimante, electronice/IT, mobilier și alte materiale. Categoriile fără surse suficiente pot exista în model și în administrare, cu acoperirea explicată în interfață. Nu prezentăm o categorie ca disponibilă doar fiindcă există în meniu.

Fiecare categorie are atribute obligatorii pentru comparație. Exemple:

- Lapte: volum, procent grăsime, UHT/proaspăt, număr de unități, restricții alimentare relevante.
- Cafea: boabe/măcinată/capsule, gramaj, variantă, compatibilitatea capsulelor.
- Hârtie: format, gramaj, număr de coli și topuri.
- Toner: cod cartuș, dispozitive compatibile, original/compatibil, randament și starea produsului.
- Laptop: cod/model exact, configurație, regiune/tastatură când contează, stare, garanție și accesoriile incluse.

O marcă poate avea aliasuri normalizate; mărcile diferite sau mărcile private ale supermarketurilor nu devin aceeași identitate doar fiindcă au descrieri similare.

### B. Identitate exactă, ambalaj diferit și alternativă sunt relații distincte

Aplicăm întâi identificatori și verificări ale atributelor. Un cod valid structural nu este singur dovada identității: conflictele dintre cod, marcă și ambalaj intră la verificare. Propunerile bazate pe nume și similaritate semantică primesc motive, încredere și statut, fără a uni automat cazurile ambigue.

UI trebuie să distingă clar:

1. Același produs și același ambalaj.
2. Același produs, ambalaj/cantitate diferită, cu preț pe unitate și rotunjire la pachete întregi.
3. Alternativă compatibilă cu cerințele firmei, acceptată separat de utilizator.

Un produs nou, un produs resigilat și un produs recondiționat nu pot fi comparați ca ofertă identică. Nici tonerul compatibil nu este același produs ca tonerul original. Propunerea semantică poate găsi candidați; validarea categoriei decide ce se poate compara.

### C. OCR facturi cu verificare și proveniență

Fluxul: încărcare document → extragere → verificare aritmetică → revizuire a câmpurilor incerte → asociere produse → confirmare → analiză. Păstrăm textul de origine și zona documentului pentru fiecare linie, astfel încât utilizatorul să vadă de unde a rezultat o cantitate sau sumă.

Extragem furnizor, dată, monedă, descriere, cod când există, cantitate, unitate, preț, reduceri, TVA și total. Verificăm consistența liniilor și totalurilor în limitele rotunjirii, detectăm duplicate și separăm avansuri, servicii, retururi și depozite de marfă. Nu completăm din imaginație codul de produs, TVA, gramajul sau unitatea lipsă.

Factura dovedește o achiziție istorică, nu prețul actual oferit oricărui client. Prețul negociat rămâne privat în organizație. Putem învăța asocieri din corecțiile confirmate, cu istoric și posibilitate de anulare.

### D. Economii calculate pentru o bază comparabilă

Calculul de cost total include cantități comandabile, transport pe comandă/furnizor, praguri de livrare, reduceri eligibile, depozite și baza de TVA aleasă consecvent. Transportul necunoscut nu este zero. Compararea coșurilor trebuie să raporteze produse lipsă și gradul de acoperire; un subtotal incomplet nu concurează cu un coș complet.

Etichetele trebuie să distingă diferența față de factura istorică, oportunitatea față de o ofertă curentă a furnizorului și economia efectiv realizată după o achiziție confirmată. O estimare anuală trebuie să arate volumul presupus și să nu promită că prețurile vor rămâne constante.

### E. Recomandări de furnizor care pot fi explicate

În loc de verdict vag despre un furnizor, arătăm motivul concret: de exemplu, costul estimat al aceluiași coș este mai mare la sursele comparabile, cu datele și produsele analizate. Lipsa datelor nu justifică un calificativ negativ.

Schimbarea furnizorului poate fi propusă când există o economie relevantă, repetată, după transport și costuri de schimbare, cu acoperire suficientă. Analiza trebuie să țină cont de livrare, facturare pentru firmă, termene de plată, cantități minime, garanție/service, localitate și preferințe confirmate. Putem sugera o ofertă de negociere sau un test de comandă înaintea schimbării complete, fără comenzi ori mesaje automate.

### F. Contract de corectitudine și măsurare

Fiecare rezultat afișează sursa, data observației, localitatea/eligibilitatea, disponibilitatea cunoscută și limitele ofertei. Schimbările anormale de preț, conflictele de identitate, unitățile lipsă și feedurile vechi intră în carantină sau sunt excluse din recomandarea principală.

Înainte de recomandări automate, pregătim un set etichetat de cazuri reale și dificile pentru fiecare categorie: OCR ambiguu, multipack, variante aproape identice, coduri contradictorii, coș incomplet și transport cu prag. Măsurăm precizia asocierilor, proporția abstinențelor și erorile economiilor; pragurile trebuie aprobate pe dovezi, nu inventate ca rezultate obținute. Un test aritmetic corect nu demonstrează că produsele au fost asociate corect.

Clasamentul principal pentru cumpărător trebuie să urmărească costul și condițiile declarate. Orice promovare plătită are etichetă și secțiune distinctă și nu alterează economia calculată. Acesta este un principiu de produs propus pentru încrederea utilizatorilor.

## Ce rămâne de validat înaintea integrării

- Contracte/feeduri directe ale comercianților pentru categoriile extinse; Compari nu a fost tratat ca sursă de date a proiectului.
- Acoperirea și drepturile fiecărei surse; disponibilitatea pentru firme, localități și cantități.
- Setul real de facturi anonimizate, calitatea OCR și costurile procesării.
- Acuratețea asocierilor pe categorie și volumul de revizuire manuală.
- Dovezile suficiente pentru recomandări de schimbare furnizor; precizia calculului de cost total.

Această cercetare clarifică mecanismul public documentat. Nu constituie o evaluare completă a acordurilor private, tehnologiei interne sau a tuturor ofertelor Compari.ro.
