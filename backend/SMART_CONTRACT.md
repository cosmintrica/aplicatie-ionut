# Comparații explicabile, versiunea 3

Toate câmpurile de mai jos sunt aditive. Contractul vechi rămâne disponibil. Sumele sunt `Money = {amount: string, currency: "RON"}`; valorile necunoscute sunt `null`.

## Catalog și liste

`GET /api/v1/catalog` acceptă `scenario`, `priced_only=true` sau `availability=priced`, respectiv `sort=recommended|price|name`. Filtrarea se aplică în SQL înainte de paginare. Cursorul include filtrele. Ordonarea implicită pune înregistrările cu preț înaintea celor fără preț.

`CatalogItem.price_summary` și `ShoppingLine.price_summary`:

```ts
{
  minimum: Money | null;
  maximum: Money | null;
  spread: Money | null;
  offer_count: number;
  candidate_count: number;
  conflict_count: number;
  needs_details_count: number;
  scope: "selected_area" | "all_saved_areas";
  label: "Prețuri raportate";
}
```

Rezumatul catalogului cuprinde cotațiile raportate pe înregistrarea respectivă. Minimul brut poate include o variantă diferită; comparația pe atribute se afișează separat. Nu se numește cost final.

`CatalogItem.profile` și `ShoppingLine.profile` conțin `kind, brand, pack, fat_percent, form, variant, range, processing, water_type, purpose, concentration, pack_conflict`. Atributele necunoscute sunt `null`; `pack_conflict` este boolean. Pentru o linie introdusă liber, `ShoppingLine.profile` este `null`. `pack` este `{dimension:"mass"|"volume",amount:string,unit:"g"|"ml",count:number,label:string}`. Gramajul normalizat nu confirmă baza prețului. Multipackurile prefixate și sufixate păstrează numărul de ambalaje: `3 x 100 g` și `100 G X3` au `count:3`, fără a deveni un pachet simplu de 100 g.

Tipul declarat în denumire are prioritate față de categorie sau marcă. `kind` poate include `coffee`, `milk`, `water`, `detergent`, `hot_drink`, `coffee_additive`, `snack`; necunoscut rămâne `null`. Mărcile sunt recunoscute printr-un dicționar explicit, fără alegerea arbitrară a unui cuvânt din titlu. Pentru produsele de curățenie, `purpose` distinge de exemplu `vase`, `WC`, `țevi`, `rufe`, `geamuri`, `pardoseli`, `degresare`. Forma și concentrația declarate se păstrează separat.

## Oferte

Quote adaugă:

```ts
{
  source_item_id: string;
  reference_item_id: string;
  verdict: "same_variant_candidate" | "variant_conflict" | "needs_details";
  verdict_label: string;
  match_reasons: string[];
  profile: Profile;
  reference_profile: Profile;
  attribute_conflicts: string[];
  missing_attributes: string[];
  price_label: "Preț raportat";
  price_basis: {
    status: "declared_pack" | "structured_pack" | "equivalent_one_litre" | "declared_mass_unit" | "ambiguous";
    label: string;
    quantity_eligible: boolean;
  };
  unit_price: UnitPrice | null;
  alternative?: {
    kind: "different_pack";
    status: "compatible_characteristics" | "needs_details";
    label: string;
    changes: string[];
    reasons: string[];
  };
  estimated_item_total?: Money;
}
```

`same_variant_candidate` înseamnă corespondență a caracteristicilor declarate, fără confirmarea codului exact al articolului. Badge-ul recomandat este `Aceleași caracteristici`, iar explicațiile sunt în `match_reasons`. Conflictele și atributele lipsă produc verdicte diferite.

O variantă sau formă explicită de cafea, un tratament UHT/ESL al laptelui ori o utilizare/formă/concentrație a produsului de curățenie nu devin alegeri implicite când cererea omite atributul. Rezultatul este `needs_details`. Contextul explicit al catalogului de referință poate completa cererea. Atributele prezente doar în catalogul propriu al ofertei rămân semnale contextuale în motive, fără a fi copiate ca atribute comerciale confirmate.

`GET /offers` adaugă `price_summary`, `related_offers: Quote[]`, `pack_alternatives: Quote[]` și `unit_price_groups: UnitPriceGroup[]`. `related_offers` include observații din alte înregistrări care au aceeași marcă, același tip și același ambalaj, cu verdict propriu. Un ID vechi Borsec fără preț nu primește preț inventat; alternativa provenită din ID-ul nou este distinctă.

`pack_alternatives` include alte gramaje sau multipackuri ale aceleiași mărci și aceluiași tip, cu caracteristici corespondente ori detalii lipsă. Conflictele declarate de variantă, formă, tratament și utilizare sunt excluse. Verdictul normal al Quote rămâne `variant_conflict` pentru ambalajul diferit. Metadatele `alternative` explică separat utilitatea opțiunii. Aceste opțiuni nu intră automat în `comparable_options`, în coș sau în calculul cantității cerute. Alegerea unui alt produs este o acțiune explicită a utilizatorului.

```ts
type UnitPrice = {
  amount: string;
  currency: "RON";
  unit: "kg" | "l";
  label: string;
  basis: string;
};
type UnitPriceGroup = {
  id: string;
  label: string;
  unit: "kg" | "l";
  options: Quote[];
  minimum: UnitPrice;
  maximum: UnitPrice;
  spread: UnitPrice;
  best_option: Quote;
  explanation: string;
};
```

Prețul normalizat folosește `Decimal` și greutatea/volumul total al multipackului. API livrează raportul rotunjit la șase zecimale și eticheta la două zecimale, de exemplu `64,98 lei/kg`; interfața afișează eticheta calculată în backend. `unit_price` este `null` pentru o bază necunoscută sau contradictorie. Unitățile brute Monitor `K`, `Kg` ori `L` pentru ambalaje de 2 l nu stabilesc singure baza. Pentru un ambalaj de exact 1 l, prețul pe litru și pe ambalaj au aceeași valoare numerică. Textul explicit `per kg` oferă prețul pe kilogram, dar nu autorizează multiplicarea unei cantități cerute în `item`; `quantity_eligible` rămâne `false`.

Grupurile normalizate pot include atât produsul ales, cât și alternativele sale cu `status:compatible_characteristics`, când baza este cunoscută. Sunt ordonate în backend după prețul normalizat și țin separat variantele, formele, tratamentele și utilizările. Opțiunile cu detalii lipsă nu intră în aceste grupuri. Exemplul Bellarom Gold măcinată 250 g la 16,49 lei și 500 g la 32,49 lei produce 65,96 lei/kg și 64,98 lei/kg, cu diferență 0,98 lei/kg. Această diferență nu este o economie realizată sau un total al coșului.

Pentru detalii folosește `GET /api/v1/evidence/{observation_id}?reference_item_id={quote.reference_item_id}`. Astfel verdictul rămâne raportat la produsul ales; fără parametru, endpointul explică observația față de propria înregistrare din catalog și declară `evaluation_scope:"source_product"`. Cu parametrul valid declară `evaluation_scope:"selected_product"`.

## Comparații

```ts
line_comparisons: {
  line_id: string;
  description: string;
  source_product_id: string | null;
  source_product_name: string | null;
  quantity: string;
  reference_profile: Profile;
  options: Quote[];
  comparable_options: Quote[];
  conflicting_options: Quote[];
  needs_details_options: Quote[];
  price_min: Money | null;
  price_max: Money | null;
  price_spread: Money | null;
  best_option: Quote | null;
  groups: {
    id: string;
    label: string;
    profile: Profile;
    options: Quote[];
    minimum: Money | null;
    maximum: Money | null;
    spread: Money | null;
    basis_label: string;
    estimate_eligible: boolean;
  }[];
  pack_alternatives: Quote[];
  unit_price_groups: UnitPriceGroup[];
  warnings: string[];
}[];
estimated_baskets: {
  store: Store;
  estimated_total: Money;
  difference_from_best: Money;
  eligible_line_count: number;
  total_line_count: number;
  quotes: Quote[];
  missing_line_ids: string[];
  assumptions: string[];
}[];
incomplete_estimates: /* același obiect, estimated_total:null */ [];
estimated_range: {minimum:Money|null;maximum:Money|null;spread:Money|null};
estimated_savings: null;
```

`options` și grupurile sunt ordonate crescător după preț. `comparable_options` și `best_option` cer atribute corespondente, bază compatibilă și cantități întregi de ambalaje. `groups` permit inspectarea și a cotațiilor cu informații lipsă, dar țin separat profilurile și unitățile brute ambigue. O diferență dintr-un grup ambiguu este diferență între valori raportate, fără multiplicare pentru cantitate.

`source_product_id` și `source_product_name` arată produsul efectiv ales pentru evaluare. `description` păstrează textul cerinței inițiale; după o substituție de 250 g cu 500 g acestea pot fi diferite și trebuie afișate distinct. `reference_profile` descrie referința efectivă, fără a rescrie cerința inițială.

Coșurile estimate se clasifică numai dacă toate liniile au opțiuni eligibile. Magazinele incomplete sunt distincte și nu primesc total sau poziție în clasament. Estimările exclud costurile neverificate de transport, condițiile comerciale și verificarea stocului. `payable_total`, `savings` și `estimated_savings` rămân `null`; diferența între estimări nu este economie realizată.

Identitatea verificată păstrează `semantic_coverage_count=0` în contractul vechi. Această valoare nu se folosește pentru a înlocui verdictele noi pe atribute.
