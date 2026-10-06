# Publicarea surselor

6 octombrie 2026. Repository public: [cosmintrica/aplicatie-ionut](https://github.com/cosmintrica/aplicatie-ionut).

Repository-ul conține codul, configurarea, lockurile dependențelor, testele, documentația, planul și probele publice necesare pornirii. Publicarea codului nu lansează un serviciu online. Serverul din versiunea actuală ascultă pe loopback; conturile și emailurile sunt definite pentru etapele următoare în [ACCES_SI_EMAIL.md](ACCES_SI_EMAIL.md).

## Copia publică și originalele locale

`scripts/prepare-publication.py` copiază directoarele de surse și documentație într-un subdirector nou din `tmp`. Exclude baza locală, fișierele private, variabilele de mediu, dependențele instalate, buildul și cache-urile. Originalele din proiect nu sunt rescrise.

Două fișiere derivate, `lidl-parsed-2026-10-05.json` și `summary.json`, aveau căi absolute ale calculatorului de lucru. Copia publică le înlocuiește cu `probe-data/<fișier>`. Rândurile comerciale, prețurile, datele sursei și observațiile nu se modifică. XML-urile și fișierul XLSB public se păstrează byte cu byte. Aceste surse publice conțin și metadate ale documentului și contacte comerciale ale magazinelor; nu sunt date ale firmei locale.

Manifestul public păstrează hashul original în `original_sha256` pentru fișierele normalizate și folosește `sha256` pentru bytes efectivi incluși în repository. Astfel, verificarea importului rămâne exactă pe o clonă nouă. Mențiunile istorice despre probele originale se referă la corpusul păstrat local înaintea exportului; datele publicate au normalizarea descrisă aici.

Exemplu de pregătire, fără cereri la furnizori sau publicare automată:

```powershell
.\.venv\Scripts\python.exe .\scripts\prepare-publication.py --output .\tmp\copie-publica-noua
```

Destinația trebuie să nu existe. Scriptul nu șterge sau înlocuiește directoare existente și verifică manifestul local înainte de copiere. O clonă publică fără căi absolute nu necesită o nouă normalizare a probelor.

Prima publicare folosește copia pregătită drept arbore de lucru pentru Git. În directorul original, cele două JSON-uri și manifestul pot apărea ca modificări locale față de commitul public: aceasta păstrează probele originale și hashurile lor. Pentru actualizări din acest director se pregătește din nou copia publică, se verifică și se adaugă fișierele din ea. Într-o clonă a repository-ului public, Git funcționează obișnuit.

## Verificarea unei clone

Comenzile din [README](../README.md) instalează dependențele fixate, construiesc interfața și importă numai probele salvate. `scripts/Check-Local.ps1` verifică parserul, aplicația și buildul. Workflow-ul [Windows checks](../.github/workflows/ci.yml) execută același flux pe GitHub Actions, fără deploy sau colectare de prețuri live.
