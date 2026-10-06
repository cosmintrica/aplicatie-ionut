# Acces, conturi și emailuri

Actualizat la 6 octombrie 2026. Stare: specificație pentru E4/E5, nu funcții implementate. Completează [planul](PLAN_IMPLEMENTARE.md), [specificația produsului](SPECIFICATIE_PRODUS.md) și [arhitectura](DECIZII_ARHITECTURA.md).

## 1. Ce există și ce urmează

Versiunea actuală funcționează local pe un calculator, cu un spațiu de lucru al firmei, cookie local și protecție CSRF. Numele firmei nu este un cont verificat. Nu există login de utilizator, înregistrare, recuperare cont, invitații, furnizor de identitate sau trimitere de email. Publicarea codului într-un repository public nu publică aplicația și nu activează aceste servicii.

| Capacitate | Versiunea locală actuală | Etapa planificată |
|---|---|---|
| Catalog, liste și comparații | Implementate pe date salvate | Extinderi conform planului |
| Profilul firmei | Nume local; accesul depinde de calculator | Onboarding, membri și selector multi-firmă în E4 |
| Login, verificarea emailului, recuperare | Neimplementate | E4, înainte de pilotul găzduit |
| Roluri, invitații și sesiuni revocabile | Neimplementate | E4, cu autorizare pe server |
| Emailuri tranzacționale | Neimplementate | E4, necesare fluxurilor de cont și invitații |
| Import și confirmare facturi | Planificate | E1b; PDF text în E2 |
| OCR real | Neimplementat | E3 local; găzduirea documentelor private necesită și G4 |
| Alerte de preț prin email | Neimplementate | E5, după surse active și preferințe explicite |
| Marketing și mesaje către furnizori | Neimplementate | Nu intră în pilotul E4; scope separat |

„Emailuri automate excluse din MVP” înseamnă marketing, cereri/comenzi către furnizori și alerte comerciale în prima versiune locală. Nu exclude verificarea adresei, invitațiile sau recuperarea contului necesare accesului real din E4.

## 2. Autentificare și onboarding în E4

Autentificarea folosește un furnizor OIDC, prin Authorization Code + PKCE, conform arhitecturii. Înainte de implementarea E4 se alege și se documentează furnizorul, regiunea, costurile, metodele de acces și fluxurile sale de verificare/recuperare. Alegerea nu este făcută prin acest document. Aplicația nu implementează propriul depozit de parole.

Identitatea internă se leagă de perechea `issuer + subject`, nu numai de email. Nu se unesc conturi sau membri după o adresă declarată/neconfirmată. Asocierea unui al doilea furnizor cere o sesiune recent autentificată și verificarea ambelor identități; este exclusă din primul pilot dacă nu este testată.

Fluxul inițial:

1. Utilizatorul alege „Creează cont” sau „Autentifică-te” și vede metodele efectiv configurate. Sunt permise email/parolă sau acces fără parolă prin provider; nu se afișează butoane Google/Microsoft neconfigurate.
2. Providerul verifică adresa. Până la verificare utilizatorul vede ecranul „Verifică adresa de email”, adresa parțial mascată, starea, termenul linkului și „Retrimite”. Nu poate accepta o invitație sau accesa datele private ale unei firme cu o adresă neconfirmată.
3. După autentificare, utilizatorul acceptă o invitație validă sau creează firma. Onboardingul cere numele firmei și zona de lucru; CUI și date fiscale devin obligatorii numai când funcția care le consumă le cere. Nu sunt completate automat din email.
4. Creatorul firmei devine Proprietar. Un utilizator invitat primește exclusiv rolul din invitație. Revizuirea numelui firmei și a rolului precede acceptarea.
5. Prima listă și exemplul public sunt opționale. Exemplul nu înregistrează o factură sau o achiziție în istoricul firmei. Revenirea deschide ultima listă accesibilă, fără repetarea onboardingului.

Fluxurile sunt reluabile dacă browserul se închide sau providerul nu răspunde. Nu se pierd ciornele serverului. Datele neconfirmate nu sunt trimise prin email și nu sunt păstrate ca documente private într-un cache public al browserului.

Ecranele minime: login/înregistrare, verificarea adresei, link expirat sau folosit, recuperare acces, invitație, alegerea/crearea firmei, membri și roluri, sesiuni/dispozitive și preferințe de notificare. Toate au stări reale de încărcare, eroare, succes și indisponibilitate, texte românești, focus vizibil și flux utilizabil la 320/390 px.

## 3. Recuperare, schimbarea adresei și sesiuni

- Dacă providerul oferă parole, „Am uitat parola” folosește fluxul său verificat de resetare. Aplicația arată un răspuns generic: „Dacă există un cont pentru această adresă, vei primi instrucțiuni”. Nu confirmă existența unui cont unei persoane neautentificate.
- Pentru acces fără parolă, recuperarea folosește metodele providerului: un nou link, passkey sau coduri de recuperare. Interfața nu pretinde că există o parolă de resetat. Accesul pierdut simultan la adresă și la metodele de recuperare nu este rezolvat prin simpla declarație a numelui/CUI; necesită procedura de suport documentată înainte de pilot.
- Linkurile și codurile sunt limitate în timp și utilizabile o singură dată. Expirarea, reutilizarea și anularea au mesaje distincte și opțiunea de reluare. Termenele reale se afișează din configurația providerului; aplicația nu inventează o valabilitate.
- Deschiderea unui link de către un scanner de email nu acceptă o invitație și nu execută o acțiune sensibilă prin GET. Consumul tokenului/aplicarea schimbării necesită confirmare explicită pe pagina de destinație și operație protejată.
- Schimbarea emailului cere reautentificare recentă, verificarea noii adrese și notificare la adresa veche. Nu schimbă identitatea internă și nu transferă automat membri/invitații. Resetarea parolei sau recuperarea după compromitere invalidează sesiunile aplicabile.
- Sesiunile găzduite au cookie `HttpOnly`, `Secure`, `SameSite` și expirare verificată pe server. Tokenurile de acces/refresh nu sunt păstrate în `localStorage` și nu ajung în URL-uri, bundle sau loguri. OAuth verifică issuer, audience, state, nonce, PKCE și callback-uri fixe.
- Limite inițiale propuse pentru sesiunea aplicației: 30 minute de inactivitate, maximum 12 ore durată absolută; expirarea providerului poate fi mai scurtă. Înainte de pilot se fixează și se testează politica efectivă. Salvarea ciornelor nu prelungește în tăcere sesiunea.
- Pagina „Sesiuni” permite logout curent și „Deconectează toate sesiunile”. Revocarea membrului, schimbarea rolului, suspendarea contului și ștergerea firmei elimină accesul fără a aștepta expirarea unui JWT vechi. Proprietar/Administrator folosesc MFA pentru pilotul găzduit, cu recuperare verificată și un raport de test.

## 4. Firme, invitații și roluri

Un utilizator poate fi membru în mai multe firme. Firma activă este vizibilă permanent; schimbarea ei reîncarcă listele, documentele, analizele și preferințele din acel scope. Serverul validează membershipul la fiecare operație. Trimiterea unui `tenant_id`, existența unui UUID sau alegerea unei firme în interfață nu acordă drepturi.

| Operație | Proprietar | Administrator | Achizitor | Cititor |
|---|---|---|---|---|
| Citire catalog, liste, facturi și analize ale firmei | Da | Da | Da | Da |
| Creare/editare liste, import și confirmare facturi, revizie asocieri | Da | Da | Da | Nu |
| Export complet al firmei și administrarea retenției | Da | Da | Nu | Nu |
| Invitare/eliminare membri și schimbare roluri obișnuite | Da | Da | Nu | Nu |
| Transfer proprietate și ștergere firmă | Da, cu reautentificare | Nu | Nu | Nu |

Rolul implicit al unei invitații este Cititor. Nu există rol administrativ implicit pentru cine cunoaște domeniul de email sau CUI. Administratorul nu poate acorda rolul Proprietar și nu poate elimina ori retrograda Proprietarul. Ultimul Proprietar nu poate părăsi firma fără transfer verificat sau ștergere explicită. Transferul este tranzacțional, necesită reautentificare și acceptarea beneficiarului, apoi jurnal și notificare.

Invitația conține firma, destinatarul și rolul; are stări `pending|accepted|expired|revoked`. Valabilitate inițială propusă: șapte zile. Tokenul secret este aleator, stocat ca hash și nu apare în loguri. Acceptarea cere identitate autentificată cu adresă verificată corespunzătoare destinatarului. Un link redirecționat către altă persoană nu conferă acces. După expirare/revocare se poate crea o invitație nouă, fără reactivarea tokenului vechi. Repetarea acceptării nu creează membershipuri duplicate.

Testele de izolare acoperă API, fișiere, OCR/importuri în worker, cache, căutare, exporturi, emailuri și jurnale. Membershipul se verifică și când rulează un job, nu doar la creare. Eliminarea accesului anulează accesul la downloaduri și rezultatele nepublicate. Catalogul public poate fi comun; facturile, prețurile negociate și mapările private nu sunt agregate într-un catalog global.

## 5. Catalogul emailurilor și preferințe

| Mesaj | Declanșator | Regula de conținut și acces |
|---|---|---|
| Verificarea adresei | Înregistrare sau adresă schimbată | Providerul sau un singur responsabil desemnat trimite mesajul; nu se dublează cu emailul aplicației |
| Recuperare/alertă de securitate | Cerere de recuperare, adresă/parolă schimbată, incident de acces | Fără parolă, token de sesiune sau conținut de factură; link cu valabilitate clară |
| Invitație și schimbarea accesului | Membru invitat, rol schimbat, acces revocat, transfer proprietate | Firma și rolul, fără listarea datelor private în corpul mesajului |
| Export/ștergere finalizată | Cerere autorizată de export sau ștergere | Confirmare scurtă; exportul se descarcă în aplicație după verificarea accesului, nu ca atașament public |
| Import/OCR finalizat | E4, opțiune activată de utilizator | Numărul documentelor și link spre aplicație; nu atașează originalul și nu expune furnizori/sume în subiect |
| Alertă de preț sau rezumat oportunități | E5, criterii salvate și surse active | Scope, vechime și condiții; nu anunță economii realizate dintr-o estimare sau preț snapshot |

Mesajele de securitate și de acces sunt tranzacționale, fără promovare. Emailurile opționale de import și alertele comerciale sunt inactive implicit și au preferințe distincte pe utilizator/firmă, frecvență și perioadă de liniște. Retragerea unei preferințe oprește și mesajele aflate în coadă. Interfața afișează „solicitat”, „acceptat de serviciul de email”, „livrat către serverul destinatarului” sau „eșuat”, după dovezile reale; HTTP 200 nu dovedește citirea emailului.

Marketingul cere scope, mecanism de acord și dezabonare distincte înainte de activare. Acordul pentru marketing nu este o condiție pentru cont. Nu se presupune acordul prin verificarea adresei, acceptarea termenilor sau invitarea în firmă. Cererile către furnizori sunt un flux separat, cu destinatari și text revizuibile și autorizare pentru trimitere; acest plan nu trimite automat negocieri/comenzi în numele firmei.

## 6. Livrare fiabilă și protecție împotriva abuzului

Mesajele providerului de identitate rămân în mecanismul său documentat. Emailurile aplicației folosesc un adaptor unic de trimitere și un outbox durabil în baza de date. Acțiunea de business și înscrierea în outbox sunt în aceeași tranzacție; workerul preia numai evenimente comise.

Outboxul păstrează `event_id`, `tenant_id` când există, destinatar/identitate, tip, versiune template, cheie de idempotency, termen de expirare, starea, încercările, următoarea încercare și ID-ul mesajului providerului. Stări: `queued|sending|accepted|delivered|failed|suppressed|expired`. Payloadurile cu tokenuri sunt protejate și șterse după expediere/expirare; logurile nu păstrează tokenuri, linkuri complete sau corpuri cu informații private.

- O cheie stabilă se generează o singură dată pentru eveniment și se refolosește la retry. Constrângerea unică locală și idempotency providerului previn duplicatele normale; nu promitem livrare „exact o dată” în orice întrerupere de rețea.
- Timeoutul după expediere lasă starea incertă: se reconciliază prin ID/cheie în fereastra providerului, fără trimitere nouă cu altă cheie. Workerul repornit reia evenimentul, nu recreează mesajul de business.
- Reîncercarea acoperă 429, 5xx și probleme de rețea, cu backoff, jitter și `Retry-After`. Payload/adresă invalidă, chei greșite, domeniu nevalidat și alte erori permanente nu sunt reîncercate la nesfârșit.
- Numărul/fereastra de retry și timeoutul sunt stabilite după contractul providerului și măsurate în test. Nu se trimit linkuri deja expirate, invitații revocate, alerte fără abonare ori documente pentru care accesul a fost retras.
- Mesajele definitiv eșuate intră într-o coadă de revizie cu motiv și posibilitate autorizată de reluare. UI nu spune „Email trimis” când providerul este neconfigurat sau a eșuat.
- Webhookurile verifică semnătura pe corpul brut, timestampul și replay-ul. Evenimentul valid se persistă înainte de confirmarea HTTP; procesarea este idempotentă după ID. Evenimente duplicate sau sosite în altă ordine nu pot activa un cont, confirma o factură sau accepta o invitație.
- Hard bounce și reclamațiile actualizează lista de suprimare; mesajele opționale și retryurile aferente se opresc. Un email critic nelivrat are cale de reluare/verificare în aplicație sau prin suport, nu ocolire silențioasă a suprimării.

Înainte de trimitere reală: domeniu/expeditor verificate, SPF/DKIM/DMARC configurate și testate, TLS, secret server-side, webhooks și bounce handling funcționale. Folosirea unui provider nu presupune aceste condiții deja satisfăcute. DNS, contul providerului, costul și publicarea endpointului sunt operațiuni ulterioare configurării autorizate.

Abuzul este limitat per adresă, utilizator, firmă și IP: signup, login, reset, retrimitere verificare, invitații și costul outboxului au limite și monitorizare. Propunere inițială pentru retrimitere: cooldown 60 secunde și maximum cinci cereri pe oră/adresă, completate cu plafon IP/firmă stabilit în G4. Providerul poate impune limite mai restrictive. Răspunsul generic, CAPTCHA adaptiv dacă există abuz și linkurile fixe pe domeniul aplicației nu trebuie să compromită accesibilitatea. Nu se permite HTML/URL arbitrar în invitații, schimbarea liberă a expeditorului sau folosirea aplicației ca releu de email.

## 7. Confidențialitate și controlul utilizatorului

Email, identitate, membership, preferințe și evenimente de acces sunt date separate de facturi și documentele OCR. Se păstrează minimul necesar fiecărui scop; furnizorii de identitate/email/OCR, regiunea și retenția lor sunt documentate înainte de pilot. Termenii și informarea privind datele au versiune și dată. Se înregistrează separat acceptarea termenilor, preferințele opționale, acordurile unde sunt necesare și revocările; nu se folosesc casete preselectate pentru marketing.

Politica aplicabilă și responsabilitățile sunt verificate pentru operațiunea reală înainte de lansare. Această specificație tehnică nu declară conformitate juridică. Retenția documentelor rămâne în arhitectură. Datele de cont, outbox, tokenuri expirate, suprimări și audit primesc perioade explicite și un test de ștergere/restaurare în G4; nu se adaugă păstrare nelimitată prin provider sau loguri.

Ștergerea contului nu șterge automat o firmă cu alți membri. Ultimul Proprietar trebuie să transfere ori să ștergă firma. UI explică separat ștergerea contului, părăsirea firmei și ștergerea datelor firmei. Exporturile/linkurile temporare expiră, iar refacerea unui backup reaplică revocările și ștergerile. Un email expediat deja sau un export descărcat nu poate fi retras de server.

Citirea emailurilor nu este urmărită cu pixeli implicit. Clickurile de verificare dovedesc doar executarea fluxului autorizat; nu devin acord de marketing. Accesul extern OCR se activează separat, cu provider/date trimise explicite; un cont verificat sau o factură aleasă nu autorizează automat trimiterea documentului la terți.

## 8. Gates și verificări înainte de pilot

Extensiile următoare fac parte din G4, nu din acceptarea E1a. Se raportează teste executate și rezultate, nu doar ecrane sau butoane existente.

| Gate | Probe obligatorii |
|---|---|
| G4-ACCES | Signup/login/verificare și recuperare reală pe conturi de test; adresă neconfirmată, link expirat/folosit, scanner GET și retrimitere; MFA Proprietar/Administrator; logout, expirare și revocare de sesiuni |
| G4-FIRME | Două firme, același utilizator cu roluri diferite și alt utilizator fără acces; invitat cu alt email, invitație revocată/duplicată, schimbare rol, transfer ultim Proprietar; API/fișier/OCR/job/cache/export fără acces cross-tenant |
| G4-EMAIL | Sandbox fără destinatari externi accidentali, apoi test live autorizat către adrese de test deținute; DNS/expeditor și deliverability documentate; timeout, 429/5xx, retry, restart, duplicate și expirare; webhook fals/replay/bounce/reclamație; nicio etichetă „livrat” fără eveniment |
| G4-DATE | Export/ștergere cont și firmă, preferință retrasă în timp ce mesajul este în coadă, acces revocat în timpul OCR; backup anterior ștergerii restaurat fără reactivarea accesului; secrete/linkuri/conținut privat absente din bundle/log/Git |
| G4-UX | Fluxurile de cont, invitație și eroare sunt utilizabile pe 320/390 px și cu tastatura; utilizatorul poate identifica firma și rolul activ și înțelege dacă emailul a fost doar solicitat sau livrat |
| G5-ALERTE | Surse active permise, valabilitate verificabilă, criterii reale și preferințe per utilizator; snapshotul sau estimarea nu devin ofertă curentă/economie realizată; dezactivarea oprește alertele în așteptare |

G4 nu este îndeplinit de repository public, de un formular login sau de cookie-ul local actual. Un pilot cu firme reale găzduit așteaptă aceste probe; dezvoltarea locală a importului și OCR poate continua conform E1b-E3 fără conturi simulate.

## 9. Referințe folosite la proiectare

Fluxurile de email au fost revizuite cu skill-ul [email-best-practices](https://github.com/resend/email-best-practices), în special catalogul tranzacțional, outbox/idempotency/retry și evenimentele de livrare. Nu este ales implicit Resend și nu a fost activat un cont sau serviciu. Exemplele unui provider se verifică în documentația oficială a furnizorului ales înainte de implementare; semnăturile și limitele lui nu sunt presupuse universale.
