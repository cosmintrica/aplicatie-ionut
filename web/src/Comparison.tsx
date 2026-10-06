import { useState } from 'react';
import { ArrowLeft, ArrowUpRight, Check, ChevronDown, Info, Store, TriangleAlert } from 'lucide-react';
import { money, type Comparison as ComparisonData, type LineComparison, type Quote } from './api';
import { Badge, EmptyState } from './components';
import { relationLabel, relationTone } from './Details';

function OptionTable({ options, onEvidence }: { options: Quote[]; onEvidence: (id: string, referenceItemId?: string) => void }) {
  return <div className="table-scroll"><table className="option-table"><thead><tr><th>Magazin și variantă</th><th>Preț</th><th>Asociere</th><th><span className="sr-only">Detalii</span></th></tr></thead><tbody>{options.map((quote) => <tr key={quote.observation_id}><td><strong>{quote.store?.name ?? quote.source_id}</strong><span>{quote.commercial_name}</span></td><td className="numeric"><strong>{money(quote.price)}</strong><small>{quote.price_basis?.label ?? ''}</small></td><td><Badge tone={relationTone(quote)}>{relationLabel(quote)}</Badge>{quote.match_reasons?.[0] ? <small className="match-reason">{quote.match_reasons[0]}</small> : null}</td><td><button className="icon-button" aria-label={`Detalii ${quote.store?.name ?? quote.source_id}: ${quote.commercial_name}`} onClick={() => onEvidence(quote.observation_id, quote.reference_item_id ?? quote.source_item_id)}><ArrowUpRight size={17} /></button></td></tr>)}</tbody></table></div>;
}
function ProductComparison({ line, onEvidence }: { line: LineComparison; onEvidence: (id: string, referenceItemId?: string) => void }) {
  return <section className="product-comparison" aria-label={`Comparație ${line.description}`}>
    <div className="section-heading"><div><h3>{line.description}</h3><p>{line.quantity} {line.quantity === '1' ? 'articol cerut' : 'articole cerute'} · {line.options.length} prețuri găsite</p></div>{line.price_spread ? <div className="price-spread"><span>Diferență între variante comparabile</span><strong>{money(line.price_spread)}</strong></div> : null}</div>
    {line.comparable_options.length ? <><div className="comparison-section-label"><Check size={17} /><strong>Variante care corespund produsului ales</strong><span>{line.comparable_options.length} prețuri</span></div><OptionTable options={line.comparable_options} onEvidence={onEvidence} /></> : <p className="inline-message"><Info size={17} />Nu am găsit încă variante cu suficiente detalii pentru produsul ales.</p>}
    {line.groups.filter((group) => group.options.length > 1 && !group.options.every((quote) => line.comparable_options.some((option) => option.observation_id === quote.observation_id))).map((group) => <details className="disclosure variant-group" key={group.id}><summary><span>{group.label}</span><span>{money(group.minimum)}{group.spread ? ` · diferență ${money(group.spread)}` : ''}</span></summary><p className="subtle-note">Caracteristici declarate similare, unitate raportată identică. {group.basis_label}</p><OptionTable options={group.options} onEvidence={onEvidence} /></details>)}
    {line.conflicting_options.length ? <details className="disclosure"><summary><span><TriangleAlert size={15} />{line.conflicting_options.length} variante diferite</span><span>Excluse din comparația produsului ales</span></summary><OptionTable options={line.conflicting_options} onEvidence={onEvidence} /></details> : null}
    {line.needs_details_options.length ? <details className="disclosure"><summary><span>{line.needs_details_options.length} prețuri cu detalii insuficiente</span><span>Vezi ce trebuie verificat</span></summary><OptionTable options={line.needs_details_options} onEvidence={onEvidence} /></details> : null}
    {line.warnings.length ? <details className="disclosure"><summary>Condiții pentru calcul</summary><ul>{line.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul></details> : null}
  </section>;
}

export function Comparison({ data, onBack, onEvidence }: { data: ComparisonData; onBack: () => void; onEvidence: (id: string, referenceItemId?: string) => void }) {
  const [activeLine, setActiveLine] = useState<string | null>(null);
  const [showAllStores, setShowAllStores] = useState(false);
  const [showAllBaskets, setShowAllBaskets] = useState(false);
  const lines = data.line_comparisons ?? [];
  const baskets = data.estimated_baskets ?? [];
  const basketOrder = new Map(baskets.map((basket, index) => [basket.store.id, index]));
  const bestStoreIds = new Set(lines.map((line) => line.best_option?.store?.id).filter(Boolean));
  const stores = data.source_quote_sums.filter((value) => value.quotes.some((quote) => quote.price)).sort((a, b) => {
    const basketA = basketOrder.get(a.store.id);
    const basketB = basketOrder.get(b.store.id);
    if (basketA !== undefined || basketB !== undefined) return (basketA ?? Number.MAX_SAFE_INTEGER) - (basketB ?? Number.MAX_SAFE_INTEGER);
    const bestA = bestStoreIds.has(a.store.id);
    const bestB = bestStoreIds.has(b.store.id);
    if (bestA !== bestB) return bestA ? -1 : 1;
    return a.store.name.localeCompare(b.store.name, 'ro');
  });
  const visibleStores = showAllStores ? stores : stores.slice(0, 8);
  const candidateLines = lines.filter((line) => line.comparable_options.length > 0);
  const conflicted = lines.reduce((sum, line) => sum + line.conflicting_options.length, 0);
  const selected = lines.find((line) => line.line_id === activeLine) ?? lines[0];
  return <>
    <button className="text-button back-link" onClick={onBack}><ArrowLeft size={17} />Lista de cumpărături</button>
    <header className="page-heading"><div><h1>Comparație de prețuri</h1><p>{lines.length || stores[0]?.total_line_count || 0} produse · {stores.length} magazine cu prețuri · {data.scenario.name}</p></div><Badge tone="green">{candidateLines.length} produse cu variante comparabile</Badge></header>
    <div className="comparison-overview">
      <div><span>Produse comparabile</span><strong>{candidateLines.length} / {lines.length}</strong><small>Caracteristici declarate comparate din denumiri</small></div>
      <div><span>Variante diferite detectate</span><strong>{conflicted}</strong><small>Separate de produsul ales, fără amestecarea prețurilor</small></div>
      <div><span>Coșuri estimate complete</span><strong>{baskets.length}</strong><small>{baskets.length ? 'Pe bazele de preț explicate mai jos' : 'Lipsesc detalii pentru un cost complet'}</small></div>
    </div>
    {baskets.length ? <section className="panel basket-panel"><div className="section-heading"><div><h2>Lista într-un singur magazin</h2><p>Estimări pentru cantitățile cerute, pe caracteristicile declarate.</p></div>{data.estimated_range?.spread ? <div className="price-spread"><span>Diferență între coșurile estimate</span><strong>{money(data.estimated_range.spread)}</strong></div> : null}</div><div className="basket-options" id="basket-options">{(showAllBaskets ? baskets : baskets.slice(0, 4)).map((basket, index) => <article className={`basket-option ${index === 0 ? 'best' : ''}`} key={basket.store.id}><div><span>{index === 0 ? 'Cel mai mic cost estimat' : 'Alternativă'}</span><h3>{basket.store.name}</h3><small>{basket.eligible_line_count} / {basket.total_line_count} produse</small></div><div className="basket-total"><strong>{money(basket.estimated_total)}</strong>{index > 0 ? <small>+{money(basket.difference_from_best)} față de prima opțiune</small> : null}</div>{basket.assumptions.length ? <details><summary>Ipoteze folosite</summary><ul>{basket.assumptions.map((value, i) => <li key={i}>{value}</li>)}</ul></details> : null}</article>)}</div>{baskets.length > 4 ? <div className="load-more"><button className="button secondary" aria-expanded={showAllBaskets} aria-controls="basket-options" onClick={() => setShowAllBaskets((value) => !value)}>{showAllBaskets ? 'Arată primele 4' : 'Toate cele ' + baskets.length + ' coșuri'}<ChevronDown size={16} /></button></div> : null}<p className="subtle-note">Estimarea nu include costuri necunoscute de transport, SGR sau condiții pentru firme. Verifică oferta înainte de cumpărare.</p></section> : null}
    <section className="panel matrix-panel" aria-labelledby="matrix-heading"><div className="section-heading"><div><h2 id="matrix-heading">Prețuri pe produs și magazin</h2><p>Prețurile din tabel sunt cele raportate pentru produs; coșurile estimate includ cantitățile cerute. Apasă pe un preț pentru detalii.</p></div></div>
      {stores.length && lines.length ? <><div className="table-scroll matrix-scroll" tabIndex={0} role="region" aria-label="Tabel comparativ, derulabil orizontal"><table className="price-matrix"><thead><tr><th>Magazin</th>{lines.map((line) => <th key={line.line_id}><button onClick={() => { setActiveLine(line.line_id); document.getElementById('product-comparison-heading')?.scrollIntoView({ block: 'start', behavior: 'smooth' }) }}>{line.description}</button><small>{line.quantity} articole</small>{line.price_min ? <span className="matrix-header-price">Preț comparabil de la {money(line.price_min)}{line.price_spread ? <small>diferență {money(line.price_spread)}</small> : null}</span> : null}</th>)}</tr></thead><tbody>{visibleStores.map((store) => <tr key={store.store.id}><th scope="row"><strong>{store.store.name}</strong><small>{store.store.network_name}</small></th>{lines.map((line) => {
        const quote = store.quotes.find((value) => value.line_id === line.line_id && value.price);
        if (!quote) return <td key={line.line_id}><span className="no-price-cell">Fără preț</span></td>;
        const attributesMatch = quote.verdict === 'same_variant_candidate';
        const compatible = attributesMatch && quote.price_basis?.quantity_eligible === true;
        const basisUnknown = attributesMatch && !compatible;
        const conflict = quote.verdict === 'variant_conflict' || quote.conflicts.length > 0;
        const best = compatible && line.best_option?.observation_id === quote.observation_id;
        return <td key={line.line_id}><button className={`matrix-price ${compatible ? 'candidate' : conflict ? 'conflict' : 'unknown'} ${best ? 'best-price' : ''} ${basisUnknown ? 'basis-unknown' : ''}`} onClick={() => onEvidence(quote.observation_id, quote.reference_item_id ?? quote.source_item_id)} aria-label={`${store.store.name}, ${line.description}, ${money(quote.price)}, ${basisUnknown ? 'Bază de preț de verificat' : relationLabel(quote)}`} title={`${relationLabel(quote)}: ${quote.commercial_name}. ${quote.price_basis?.label ?? ''}`}><strong>{money(quote.price)}</strong>{compatible ? <Check size={14} /> : conflict ? <TriangleAlert size={14} /> : <Info size={14} />}{best ? <small>minim pe ambalaj</small> : basisUnknown ? <small>Bază de verificat</small> : null}</button></td>;
      })}</tr>)}</tbody></table></div><div className="matrix-footer"><div className="matrix-legend"><span><Check size={14} />Comparabil pe ambalaj</span><span><TriangleAlert size={14} />Variantă diferită</span><span><Info size={14} />Detalii insuficiente</span></div>{stores.length > 8 ? <button className="text-button" onClick={() => setShowAllStores((value) => !value)}>{showAllStores ? 'Arată primele 8 magazine' : `Toate cele ${stores.length} magazine`}<ChevronDown size={15} /></button> : null}</div></> : <EmptyState icon={Store} title="Nu avem prețuri pentru comparația listei"><p>Adaugă produse cu prețuri din catalog pentru zona aleasă.</p></EmptyState>}
    </section>
    {lines.length ? <section className="panel product-analysis-panel"><div className="section-heading"><div><h2 id="product-comparison-heading">Variante și diferențe de preț</h2><p>Grupurile țin separat marca, ambalajul și diferențele de variantă.</p></div></div><div className="product-tabs" role="group" aria-label="Alege produsul de analizat">{lines.map((line) => <button key={line.line_id} className={selected?.line_id === line.line_id ? 'active' : ''} aria-pressed={selected?.line_id === line.line_id} onClick={() => setActiveLine(line.line_id)}>{line.description}{line.price_min ? <strong>{money(line.price_min)}</strong> : null}</button>)}</div>{selected ? <ProductComparison line={selected} onEvidence={onEvidence} /> : null}</section> : null}
    <div className="comparison-footnote"><Info size={17} /><p>„Aceleași caracteristici” înseamnă că marca, ambalajul și varianta declarate în denumiri se potrivesc. Verificarea prin cod de produs și costul final la cumpărare rămân necesare.</p></div>
    {data.warnings.length ? <details className="disclosure"><summary>Sursele și limitele comparației</summary><ul>{data.warnings.map((value, index) => <li key={index}>{value}</li>)}</ul></details> : null}
  </>;
}
