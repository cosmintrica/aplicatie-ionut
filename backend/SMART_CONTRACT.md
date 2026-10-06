# Comparații explicabile, versiunea 2

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

`CatalogItem.profile` conține `kind, brand, pack, fat_percent, form, variant, range, processing, water_type`. Atributele necunoscute sunt `null`. `pack` este `{dimension:"mass"|"volume",amount:string,unit:"g"|"ml",count:number,label:string}`. Gramajul normalizat nu confirmă baza prețului.

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
    status: "declared_pack" | "structured_pack" | "equivalent_one_litre" | "ambiguous";
    label: string;
    quantity_eligible: boolean;
  };
  estimated_item_total?: Money;
}
```

`same_variant_candidate` înseamnă corespondență a caracteristicilor declarate, fără confirmarea codului exact al articolului. Badge-ul recomandat este `Aceleași caracteristici`, iar explicațiile sunt în `match_reasons`. Conflictele și atributele lipsă produc verdicte diferite.

`GET /offers` adaugă `price_summary` și `related_offers: Quote[]`. Ultimul include observații din alte înregistrări care au aceeași marcă, același tip și același ambalaj, cu verdict propriu. Un ID vechi Borsec fără preț nu primește preț inventat; alternativa provenită din ID-ul nou este distinctă.

Pentru detalii folosește `GET /api/v1/evidence/{observation_id}?reference_item_id={quote.reference_item_id}`. Astfel verdictul rămâne raportat la produsul ales; fără parametru, endpointul explică observația față de propria înregistrare din catalog și declară `evaluation_scope:"source_product"`. Cu parametrul valid declară `evaluation_scope:"selected_product"`.

## Comparații

```ts
line_comparisons: {
  line_id: string;
  description: string;
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

Coșurile estimate se clasifică numai dacă toate liniile au opțiuni eligibile. Magazinele incomplete sunt distincte și nu primesc total sau poziție în clasament. Estimările exclud costurile neverificate de transport, condițiile comerciale și verificarea stocului. `payable_total`, `savings` și `estimated_savings` rămân `null`; diferența între estimări nu este economie realizată.

Identitatea verificată păstrează `semantic_coverage_count=0` în contractul vechi. Această valoare nu se folosește pentru a înlocui verdictele noi pe atribute.
