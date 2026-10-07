import { useEffect, useState } from 'react';
import { ArrowLeft, ArrowRight, ArrowUpRight, Check, ChevronDown, Download, Info, Package, Scale, ShoppingBag, Store, TriangleAlert } from 'lucide-react';
import { money, type Comparison as ComparisonData, type LineComparison, type Quote } from './api';
import { Badge, EmptyState } from './components';
import { relationLabel, relationTone } from './Details';
import './comparison.css';
import { ProductFacts } from './ProductFacts';

type EvidenceAction = (id: string, referenceItemId?: string) => void;
type Basket = NonNullable<ComparisonData['estimated_baskets']>[number];
const LIDL_NETWORK_STORE = { id: 'lidl_network', name: 'Lidl · listă la nivel de rețea', network_name: 'Lidl', address: null };
function quoteStore(quote: Quote): NonNullable<Quote['store']> | null {
  return quote.store ?? (quote.source_id === 'lidl' ? LIDL_NETWORK_STORE : null);
}
function productName(line: LineComparison): string { return line.source_product_name ?? line.description }

function csvCell(value: string | null | undefined): string {
  const text = value ?? '';
  const safe = /^[\s\uFEFF]*[=+@-]|^[\t\r\n]/.test(text) ? "'" + text : text;
  return '"' + safe.replaceAll('"', '""') + '"';
}

function exportComparison(data: ComparisonData) {
  const rows: (string | null | undefined)[][] = [[
    'Cerință inițială', 'Produs ales', 'Ambalaj ales', 'Cantitate cerută', 'Magazin', 'Denumire raportată', 'Preț raportat', 'Monedă',
    'Baza prețului', 'Preț unitar', 'Unitate', 'Eligibil pentru coș', 'Asociere', 'Motiv',
    'Data prețului', 'Sursă', 'Observație', 'Zonă', 'Tip date',
  ]];
  for (const line of data.line_comparisons ?? []) {
    const seen = new Set<string>();
    const eligible = new Set(line.comparable_options.map((quote) => quote.observation_id));
    for (const quote of [...line.options, ...(line.pack_alternatives ?? [])]) {
      if (seen.has(quote.observation_id)) continue;
      seen.add(quote.observation_id);
      rows.push([
        line.description, productName(line), line.reference_profile.pack?.label, line.quantity, quoteStore(quote)?.name ?? quote.source_id, quote.commercial_name,
        quote.price?.amount, quote.price?.currency, quote.price_basis?.label,
        quote.unit_price?.amount, quote.unit_price?.unit,
        eligible.has(quote.observation_id) ? 'Da, estimare pe caracteristici' : 'Nu',
        quote.alternative?.label ?? relationLabel(quote),
        [...(quote.alternative?.changes ?? []), ...(quote.match_reasons ?? [])].join(' | '),
        quote.source_priced_at, quote.source_id, quote.observation_id, data.scenario.name,
        'Snapshot offline; fără confirmarea stocului, a identității sau a costului final',
      ]);
    }
  }
  const blob = new Blob(['\uFEFF', rows.map((row) => row.map(csvCell).join(';')).join('\r\n')], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'comparatie-preturi.csv';
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function QuoteOptions({ options, onEvidence, onOpenProduct, alternative = false }: {
  options: Quote[]; onEvidence: EvidenceAction; onOpenProduct?: (id: string) => void; alternative?: boolean;
}) {
  return <ul className="cmp-offers">{options.map((quote) => <li className="cmp-offer" key={quote.observation_id}>
    <div className="cmp-offer-product"><strong>{quoteStore(quote)?.name ?? quote.source_id}</strong><p>{quote.commercial_name}</p>
      <Badge tone={alternative ? quote.alternative?.status === 'compatible_characteristics' ? 'green' : 'amber' : relationTone(quote)}>{alternative ? quote.alternative?.label ?? 'Alt ambalaj' : relationLabel(quote)}</Badge>
      {quote.match_reasons?.[0] ? <small>{quote.match_reasons[0]}</small> : null}
      {alternative && quote.alternative?.changes.length ? <small>{quote.alternative.changes.join(' · ')}</small> : null}
    </div>
    <div className="cmp-offer-price"><strong>{money(quote.price)}</strong><small>{quote.price_basis?.label ?? 'Bază de preț de verificat'}</small>{quote.unit_price ? <span className="cmp-unit-price">{quote.unit_price.label}</span> : null}</div>
    <div className="cmp-offer-actions"><button className="text-button" onClick={() => onEvidence(quote.observation_id, quote.reference_item_id ?? quote.source_item_id)}>Vezi dovada <ArrowUpRight size={15} /></button>
      {alternative && onOpenProduct && quote.source_item_id ? <button className="text-button" onClick={() => onOpenProduct(quote.source_item_id!)}>Vezi produsul <ArrowRight size={15} /></button> : null}
    </div>
  </li>)}</ul>;
}

function PackAlternatives({ line, onEvidence, onOpenProduct }: { line: LineComparison; onEvidence: EvidenceAction; onOpenProduct?: (id: string) => void }) {
  const alternatives = line.pack_alternatives ?? [];
  const groups = line.unit_price_groups ?? [];
  const groupedIds = new Set(groups.filter((group) => group.options.length > 1).flatMap((group) => group.options.map((quote) => quote.observation_id)));
  const ungrouped = alternatives.filter((quote) => !groupedIds.has(quote.observation_id));
  if (!alternatives.length && !groups.some((group) => group.options.length > 1)) return null;
  return <section className="cmp-pack-section" aria-label="Comparație pe kilogram sau litru">
    <div className="cmp-subheading"><span className="cmp-section-icon"><Scale size={20} /></span><div><h3>{alternatives.length ? 'Merită un alt ambalaj?' : 'Comparație pe aceeași unitate'}</h3><p>Compară prețul pe kilogram sau litru. Ambalajele alternative nu înlocuiesc automat produsele din listă.</p></div></div>
    {groups.filter((group) => group.options.length > 1).map((group) => <div className="cmp-unit-group" key={group.id}>
      <div className="cmp-unit-summary"><div><strong>{group.label}</strong><p>{group.explanation}</p></div><div><small>Minim pe {group.unit}</small><strong>{group.minimum.label}</strong></div></div>
      <ul className="cmp-unit-options">{group.options.map((quote) => <li key={quote.observation_id} className={group.best_option.observation_id === quote.observation_id ? 'is-best' : ''}>
        <div><strong>{quote.commercial_name}</strong><span>{quoteStore(quote)?.name ?? quote.source_id}</span><small>{quote.alternative ? 'Ambalaj alternativ' : 'Ambalajul cerut'} · {money(quote.price)} preț raportat</small></div>
        <div className="cmp-unit-value"><strong>{quote.unit_price?.label}</strong>{group.best_option.observation_id === quote.observation_id ? <Badge tone="green">Minim pe {group.unit}</Badge> : null}</div>
        <div className="cmp-offer-actions"><button className="text-button" onClick={() => onEvidence(quote.observation_id, quote.reference_item_id ?? quote.source_item_id)}>Detalii <ArrowUpRight size={15} /></button>{quote.alternative && onOpenProduct && quote.source_item_id ? <button className="text-button" onClick={() => onOpenProduct(quote.source_item_id!)}>Vezi produsul <ArrowRight size={15} /></button> : null}</div>
      </li>)}</ul>
    </div>)}
    {ungrouped.length ? <details className="disclosure"><summary>{ungrouped.length} oferte cu alt ambalaj care cer verificare</summary><p className="subtle-note">Lipsesc atribute sau alte oferte cu o bază explicită de preț pentru o comparație pe aceeași unitate.</p><QuoteOptions options={ungrouped} alternative onEvidence={onEvidence} onOpenProduct={onOpenProduct} /></details> : null}
  </section>;
}

function ProductComparison({ line, onEvidence, onOpenProduct }: { line: LineComparison; onEvidence: EvidenceAction; onOpenProduct?: (id: string) => void }) {
  const comparableIds = new Set(line.comparable_options.map((quote) => quote.observation_id));
  const extraGroups = line.groups.filter((group) => group.options.length > 1 && !group.options.every((quote) => comparableIds.has(quote.observation_id)));
  return <section className="product-comparison" aria-label={`Comparație ${productName(line)}`}>
    <div className="section-heading"><div><span className="cmp-eyebrow">Produsul ales</span><h3>{productName(line)}</h3><ProductFacts profile={line.reference_profile} />{line.source_product_name && line.source_product_name !== line.description ? <p className="cmp-request-note">Cerința inițială: {line.description}</p> : null}<p>{line.quantity} {line.quantity === '1' ? 'articol cerut' : 'articole cerute'} · {line.options.filter((quote) => quote.price).length} prețuri găsite</p></div>{line.price_spread ? <div className="price-spread"><span>Diferență pe același ambalaj</span><strong>{money(line.price_spread)}</strong></div> : null}</div>
    {line.comparable_options.length ? <><div className="comparison-section-label"><Check size={17} /><strong>Corespund caracteristicilor și cantității cerute</strong><span>{line.comparable_options.length} oferte</span></div><QuoteOptions options={line.comparable_options} onEvidence={onEvidence} /></> : <div className="cmp-context-note"><Info size={18} /><p>Nicio ofertă nu poate intra încă în estimarea acestui produs. Verifică varianta, baza prețului și cantitatea cerută în detaliile de mai jos.</p></div>}
    <PackAlternatives line={line} onEvidence={onEvidence} onOpenProduct={onOpenProduct} />
    {extraGroups.map((group) => <details className="disclosure variant-group" key={group.id}><summary><span>{group.label}</span><span>{money(group.minimum)}{group.spread ? ` · diferență ${money(group.spread)}` : ''}</span></summary><p className="subtle-note">Caracteristici declarate similare, unitate raportată identică. {group.basis_label}</p><QuoteOptions options={group.options} onEvidence={onEvidence} /></details>)}
    {line.conflicting_options.length ? <details className="disclosure"><summary><span><TriangleAlert size={15} />{line.conflicting_options.length} variante diferite</span><span>Excluse din estimarea produsului ales</span></summary><QuoteOptions options={line.conflicting_options} onEvidence={onEvidence} /></details> : null}
    {line.needs_details_options.length ? <details className="disclosure"><summary><span>{line.needs_details_options.length} prețuri cu detalii insuficiente</span><span>Vezi ce trebuie verificat</span></summary><QuoteOptions options={line.needs_details_options} onEvidence={onEvidence} /></details> : null}
    {line.warnings.length ? <details className="disclosure"><summary>Condiții pentru calcul</summary><ul>{line.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul></details> : null}
  </section>;
}

function BasketContents({ basket, lines, onEvidence }: { basket: Basket; lines: LineComparison[]; onEvidence: EvidenceAction }) {
  return <div className="cmp-basket-contents" id="basket-contents">
    <div className="cmp-basket-contents-heading"><div><span className="cmp-eyebrow">Conținutul estimării</span><h3 id="basket-contents-heading" tabIndex={-1}>{basket.store.name}</h3><p>{basket.store.address ?? basket.store.network_name}</p></div><Badge tone="green">Toate cele {basket.total_line_count} produse</Badge></div>
    <ul>{basket.quotes.map((quote) => {
      const line = lines.find((value) => value.line_id === quote.line_id);
      return <li key={`${quote.line_id}:${quote.observation_id}`}><span className="cmp-basket-quantity">{line?.quantity ?? '?'}<small>buc.</small></span><div className="cmp-basket-product"><strong>{line ? productName(line) : quote.commercial_name}</strong><span>{quote.commercial_name}</span><small>{money(quote.price)} · {quote.price_basis?.label}</small></div><div className="cmp-basket-line-total"><strong>{money(quote.estimated_item_total)}</strong><button className="text-button" onClick={() => onEvidence(quote.observation_id, quote.reference_item_id ?? quote.source_item_id)}>Dovadă <ArrowUpRight size={14} /></button></div></li>;
    })}</ul>
    <div className="cmp-basket-summary"><span>Total estimat pentru cantitățile cerute</span><strong>{money(basket.estimated_total)}</strong></div>
    {basket.assumptions.length ? <details className="disclosure"><summary>Ipotezele acestei estimări</summary><ul>{basket.assumptions.map((value, index) => <li key={index}>{value}</li>)}</ul></details> : null}
  </div>;
}

export function Comparison({ data, onBack, onEvidence, onOpenProduct }: { data: ComparisonData; onBack: () => void; onEvidence: EvidenceAction; onOpenProduct?: (id: string) => void }) {
  const [activeLine, setActiveLine] = useState<string | null>(null);
  const [selectedBasket, setSelectedBasket] = useState<string | null>(null);
  const [showAllStores, setShowAllStores] = useState(false);
  const [showAllBaskets, setShowAllBaskets] = useState(false);
  const [onlyCompleteStores, setOnlyCompleteStores] = useState(false);
  const [exported, setExported] = useState(false);
  const lines = data.line_comparisons ?? [];
  const baskets = data.estimated_baskets ?? [];
  const basketOrder = new Map(baskets.map((basket, index) => [basket.store.id, index]));
  const bestStoreIds = new Set(lines.map((line) => line.best_option ? quoteStore(line.best_option)?.id : null).filter(Boolean));
  const matrixStores = new Map<string, { store: NonNullable<Quote['store']>; quotes: Quote[] }>();
  for (const value of data.source_quote_sums) matrixStores.set(value.store.id, { store: value.store, quotes: [...value.quotes] });
  for (const value of baskets) {
    if (!matrixStores.has(value.store.id)) matrixStores.set(value.store.id, { store: value.store, quotes: [...value.quotes] });
  }
  for (const line of lines) for (const quote of line.options) {
    const store = quoteStore(quote);
    if (!store || !quote.price) continue;
    const entry = matrixStores.get(store.id);
    if (entry) entry.quotes.push(quote);
    else matrixStores.set(store.id, { store, quotes: [quote] });
  }
  const stores = [...matrixStores.values()].filter((value) => value.quotes.some((quote) => quote.price)).sort((a, b) => {
    const basketA = basketOrder.get(a.store.id);
    const basketB = basketOrder.get(b.store.id);
    if (basketA !== undefined || basketB !== undefined) return (basketA ?? Number.MAX_SAFE_INTEGER) - (basketB ?? Number.MAX_SAFE_INTEGER);
    const bestA = bestStoreIds.has(a.store.id);
    const bestB = bestStoreIds.has(b.store.id);
    if (bestA !== bestB) return bestA ? -1 : 1;
    return a.store.name.localeCompare(b.store.name, 'ro');
  });
  const filteredStores = onlyCompleteStores ? stores.filter((store) => basketOrder.has(store.store.id)) : stores;
  const visibleStores = showAllStores ? filteredStores : filteredStores.slice(0, 8);
  const candidateLines = lines.filter((line) => line.comparable_options.length > 0);
  const selected = lines.find((line) => line.line_id === activeLine) ?? lines[0];
  const basket = baskets.find((value) => value.store.id === selectedBasket);
  const alternativesCount = lines.reduce((sum, line) => sum + (line.pack_alternatives?.length ?? 0), 0);
  const bestBasket = baskets[0];
  useEffect(() => {
    if (!selectedBasket) return;
    const heading = document.getElementById('basket-contents-heading');
    heading?.scrollIntoView({ block: 'center', behavior: 'smooth' });
    heading?.focus({ preventScroll: true });
  }, [selectedBasket]);
  function selectProduct(id: string) {
    setActiveLine(id);
    document.getElementById('product-comparison-heading')?.scrollIntoView({ block: 'start', behavior: 'smooth' });
    document.getElementById('product-comparison-heading')?.focus({ preventScroll: true });
  }
  return <div className="comparison-workspace">
    <div className="cmp-page-actions"><button className="text-button back-link" onClick={onBack}><ArrowLeft size={17} />Înapoi la listă</button><button className="button secondary" onClick={() => { exportComparison(data); setExported(true) }} disabled={!lines.some((line) => line.options.length || line.pack_alternatives?.length)}><Download size={16} />Exportă CSV</button></div>
    {exported ? <p className="cmp-export-status" role="status">Fișierul CSV include prețurile raportate, motivele asocierii și sursele. Valorile sunt din datele salvate.</p> : null}
    <header className="cmp-hero"><div><span className="cmp-eyebrow">Decizia de cumpărare</span><h1>Unde merită să cumperi?</h1><p>{lines.length} produse · {stores.length} magazine și liste de rețea · {data.scenario.name}</p><span className="cmp-hero-note"><Info size={15} />Estimări din datele salvate, cu caracteristici explicate.</span></div><div className="cmp-hero-result">{bestBasket ? <><span>Cel mai mic coș complet estimat</span><strong>{money(bestBasket.estimated_total)}</strong><p>{bestBasket.store.name}</p><button onClick={() => { setSelectedBasket(bestBasket.store.id); document.getElementById('basket-contents-heading')?.scrollIntoView({ block: 'center', behavior: 'smooth' }); document.getElementById('basket-contents-heading')?.focus({ preventScroll: true }) }}>Vezi produsele incluse <ArrowRight size={16} /></button></> : <><ShoppingBag size={27} /><strong className="cmp-no-basket">Lista nu are încă un coș complet</strong><p>Explorează ofertele pe produs și verifică pozițiile care cer detalii.</p></>}</div></header>
    <div className="cmp-metrics"><div><span className="cmp-metric-icon"><Check size={20} /></span><div><strong>{candidateLines.length} / {lines.length}</strong><span>produse cu oferte comparabile</span></div></div><div><span className="cmp-metric-icon"><Store size={20} /></span><div><strong>{baskets.length}</strong><span>coșuri complete estimate</span></div></div><div><span className="cmp-metric-icon"><Package size={20} /></span><div><strong>{alternativesCount}</strong><span>oferte cu alte ambalaje</span></div></div></div>
    {baskets.length ? <section className="panel basket-panel cmp-basket-panel" id="basket-section" aria-labelledby="basket-heading"><div className="section-heading"><div><span className="cmp-eyebrow">01 · Toată lista</span><h2 id="basket-heading">Lista completă, la un singur furnizor</h2><p>Numai ofertele care acoperă toate produsele și cantitățile eligibile intră în clasament. Lista de rețea rămâne distinctă de un magazin local.</p></div>{data.estimated_range?.spread ? <div className="price-spread"><span>Diferență între estimări</span><strong>{money(data.estimated_range.spread)}</strong></div> : null}</div>
      <div className="cmp-basket-grid" id="basket-options">{(showAllBaskets ? baskets : baskets.slice(0, 4)).map((value, index) => <article className={`cmp-basket-card ${index === 0 ? 'is-best' : ''} ${selectedBasket === value.store.id ? 'is-selected' : ''}`} key={value.store.id}><div className="cmp-basket-card-top"><span className="cmp-rank">{index + 1}</span>{index === 0 ? <Badge tone="green">Minimul estimat</Badge> : <span>Coș complet</span>}</div><h3>{value.store.name}</h3><p>{value.eligible_line_count} / {value.total_line_count} produse</p><strong className="cmp-basket-cost">{money(value.estimated_total)}</strong><small>{index > 0 ? `+${money(value.difference_from_best)} față de prima opțiune` : 'Pentru cantitățile din listă'}</small><button className="button secondary" aria-expanded={selectedBasket === value.store.id} aria-controls="basket-contents" onClick={() => setSelectedBasket((current) => current === value.store.id ? null : value.store.id)}>{selectedBasket === value.store.id ? 'Ascunde conținutul' : 'Vezi conținutul'}<ChevronDown size={16} /></button></article>)}</div>
      {basket ? <BasketContents basket={basket} lines={lines} onEvidence={onEvidence} /> : null}
      {baskets.length > 4 ? <div className="load-more"><button className="button secondary" aria-expanded={showAllBaskets} aria-controls="basket-options" onClick={() => setShowAllBaskets((value) => !value)}>{showAllBaskets ? 'Arată primele 4' : `Toate cele ${baskets.length} coșuri`}<ChevronDown size={16} /></button></div> : null}<p className="cmp-cost-note"><Info size={16} />Diferența dintre estimări nu este economie realizată. Transportul, SGR, stocul și condițiile pentru firme trebuie verificate.</p>
    </section> : <div className="cmp-context-note"><Info size={18} /><p>Un preț lipsă sau o variantă diferită poate împiedica estimarea întregii liste. Verifică fiecare produs mai jos sau <button className="text-button" onClick={onBack}>ajustează lista <ArrowRight size={14} /></button>.</p></div>}
    <section className="panel matrix-panel" aria-labelledby="matrix-heading"><div className="section-heading"><div><span className="cmp-eyebrow">02 · Pe produs</span><h2 id="matrix-heading">Prețuri, magazin cu magazin</h2><p>Prețuri raportate de sursă; baza și eligibilitatea sunt explicate la fiecare ofertă. Cantitățile se aplică doar coșurilor estimate.</p></div>{baskets.length && baskets.length < stores.length ? <label className="cmp-store-filter"><input type="checkbox" checked={onlyCompleteStores} onChange={(event) => setOnlyCompleteStores(event.target.checked)} />Doar coșuri complete</label> : null}</div>
      {stores.length && lines.length ? <><div className="table-scroll matrix-scroll" tabIndex={0} role="region" aria-label="Tabel comparativ, derulabil orizontal"><table className="price-matrix"><thead><tr><th scope="col">Magazin</th>{lines.map((line) => <th scope="col" key={line.line_id}><button onClick={() => selectProduct(line.line_id)}>{productName(line)}</button>{line.source_product_name && line.source_product_name !== line.description ? <small>Cerință: {line.description}</small> : null}<small>{line.reference_profile.pack?.label ? `${line.reference_profile.pack.label} · ` : ''}{line.quantity} articole cerute</small>{line.price_min ? <span className="matrix-header-price">De la {money(line.price_min)}</span> : null}</th>)}</tr></thead><tbody>{visibleStores.map((store) => <tr key={store.store.id}><th scope="row"><strong>{store.store.name}</strong><small>{basketOrder.has(store.store.id) ? 'Coș complet disponibil' : store.store.network_name}</small></th>{lines.map((line) => {
        const eligible = line.comparable_options.filter((value) => quoteStore(value)?.id === store.store.id);
        const quote = eligible[0] ?? line.options.find((value) => quoteStore(value)?.id === store.store.id && value.price) ?? store.quotes.find((value) => value.line_id === line.line_id && value.price);
        if (!quote) return <td key={line.line_id}><span className="no-price-cell">Fără preț</span></td>;
        const compatible = eligible.some((value) => value.observation_id === quote.observation_id);
        const conflict = quote.verdict === 'variant_conflict' || quote.conflicts.length > 0;
        const best = compatible && line.best_option?.observation_id === quote.observation_id;
        const label = compatible ? best ? 'Minim comparabil' : 'Comparabil' : conflict ? 'Altă variantă' : quote.verdict === 'same_variant_candidate' ? quote.price_basis?.quantity_eligible ? 'Cantitate de verificat' : 'Bază de verificat' : 'Detalii insuficiente';
        return <td key={line.line_id}><button className={`matrix-price ${compatible ? 'candidate' : conflict ? 'conflict' : 'unknown'} ${best ? 'best-price' : ''}`} onClick={() => onEvidence(quote.observation_id, quote.reference_item_id ?? quote.source_item_id)} aria-label={`${store.store.name}, ${productName(line)}, ${money(quote.price)}, ${label}`} title={`${quote.commercial_name}. ${quote.price_basis?.label ?? ''}`}><strong>{money(quote.price)}</strong>{compatible ? <Check size={14} /> : conflict ? <TriangleAlert size={14} /> : <Info size={14} />}<small>{label}</small></button></td>;
      })}</tr>)}</tbody></table></div><div className="matrix-footer"><div className="matrix-legend"><span><Check size={14} />Comparabil</span><span><TriangleAlert size={14} />Variantă diferită</span><span><Info size={14} />Necesită verificare</span></div>{filteredStores.length > 8 ? <button className="text-button" onClick={() => setShowAllStores((value) => !value)} aria-expanded={showAllStores}>{showAllStores ? 'Arată primele 8 magazine' : `Toate cele ${filteredStores.length} magazine`}<ChevronDown size={15} /></button> : null}</div></> : <EmptyState icon={Store} title="Nu avem prețuri pentru comparația listei"><p>Adaugă produse cu prețuri din catalog pentru zona aleasă.</p></EmptyState>}
    </section>
    {lines.length ? <section className="panel product-analysis-panel"><div className="section-heading"><div><span className="cmp-eyebrow">03 · Alege informat</span><h2 id="product-comparison-heading" tabIndex={-1}>Oferte și alternative explicate</h2><p>Marca, varianta și ambalajul sunt analizate separat pentru fiecare produs.</p></div></div><div className="product-tabs" role="group" aria-label="Alege produsul de analizat">{lines.map((line) => <button key={line.line_id} className={selected?.line_id === line.line_id ? 'active' : ''} aria-pressed={selected?.line_id === line.line_id} onClick={() => setActiveLine(line.line_id)}>{productName(line)}<strong>{line.price_min ? `De la ${money(line.price_min)}` : 'Necesită verificare'}</strong></button>)}</div>{selected ? <ProductComparison line={selected} onEvidence={onEvidence} onOpenProduct={onOpenProduct} /> : null}</section> : null}
    <div className="comparison-footnote"><Info size={17} /><p>„Aceleași caracteristici” indică potrivirea atributelor declarate. Identitatea exactă prin cod de produs și costul final trebuie confirmate. Data fiecărui preț apare în dovada sa, separat de data importului.</p></div>
    {data.warnings.length ? <details className="disclosure"><summary>Sursele și limitele comparației</summary><ul>{data.warnings.map((value, index) => <li key={index}>{value}</li>)}</ul></details> : null}
  </div>;
}
