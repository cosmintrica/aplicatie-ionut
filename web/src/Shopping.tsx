import { useEffect, useState } from 'react';
import { ArrowRight, Check, ClipboardList, ListFilter, Plus, RotateCcw, Search, Trash2 } from 'lucide-react';
import { categoryOptions, errorText, money, request, type CatalogItem, type CatalogResponse, type Category, type ShoppingLine, type ShoppingList, type Source } from './api';
import { ProductCard } from './Catalog';
import { CategoryIcon, CategoryTag, EmptyState, ErrorNotice, Loading, Notice, SearchField } from './components';
import { ProductFacts } from './ProductFacts';

function ListLine({ line, quantity, onDraft, categories, busy, onQuantity, onRemove, onResolve, onOpenProduct }: { line: ShoppingLine; quantity: string; onDraft: (value?: string) => void; categories: Category[]; busy: boolean; onQuantity: (id: string, quantity: string) => Promise<boolean>; onRemove: (line: ShoppingLine) => void; onResolve: (line: ShoppingLine) => void; onOpenProduct: (id: string) => Promise<void> }) {
  const [opening, setOpening] = useState(false);
  const category = categories.find((value) => value.id === line.category_id);
  async function open() {
    if (!line.source_product_id) { onResolve(line); return }
    setOpening(true);
    try { await onOpenProduct(line.source_product_id) } finally { setOpening(false) }
  }
  return <article className="list-line"><span className="product-icon"><CategoryIcon name={category?.name ?? line.description} size={20} /></span><div className="list-line-info"><button className="product-name" onClick={open} disabled={opening || busy}>{line.source_product_name || line.description}</button><div className="product-secondary"><CategoryTag categoryId={line.category_id} categories={categories} /><button className="text-button" disabled={busy} onClick={() => onResolve(line)}>{line.source_product_id ? 'Schimbă produsul' : 'Alege un produs'} <Search size={13} /></button></div><ProductFacts profile={line.profile} />{line.source_product_name && line.source_product_name !== line.description ? <p className="original-need">Cerință: {line.description}</p> : null}</div>
    <div className="line-price">{line.price_summary?.minimum ? <><small>Minim raportat</small><strong>{money(line.price_summary.minimum)}</strong><button className="text-button" disabled={opening} onClick={open}>{line.price_summary.offer_count} prețuri</button></> : <><strong className="no-price">Fără preț</strong><small>{line.source_product_id ? 'În datele zonei' : 'Alege un produs'}</small></>}</div>
    <div className="quantity-field"><label htmlFor={`quantity-${line.id}`}>Ambalaje</label><input id={`quantity-${line.id}`} aria-label={`Cantitate pentru ${line.description}`} inputMode="decimal" value={quantity} disabled={busy} onChange={(event) => onDraft(event.target.value)} />{quantity !== line.quantity ? <button className="text-button" disabled={busy || !quantity.trim()} onClick={async () => { if (await onQuantity(line.id, quantity.replace(',', '.'))) onDraft() }}>Salvează</button> : null}</div><button className="icon-button remove-button" aria-label={`Elimină ${line.description}`} disabled={busy} onClick={() => onRemove(line)}><Trash2 size={17} /></button>
  </article>;
}

export function Shopping({ list, categories, sources, busy, comparing, removed, resolvingLine, onResolve, onCancelResolve, onUndo, onSelect, onOpenProduct, onFreeLine, onQuantity, onRemove, onCompare, onExample, onCatalog, onNewList }: {
  list: ShoppingList; categories: Category[]; sources: Source[]; busy: boolean; comparing: boolean; removed: ShoppingLine | null;
  onOpenProduct: (id: string) => Promise<void>;
  onUndo: () => void; onSelect: (item: CatalogItem) => void; onFreeLine: (description: string, categoryId: string) => Promise<boolean>;
  onQuantity: (id: string, quantity: string) => Promise<boolean>; onRemove: (line: ShoppingLine) => void; onCompare: () => void;
  onExample: () => void; onCatalog: () => void; onNewList: () => void;
  resolvingLine: ShoppingLine | null; onResolve: (line: ShoppingLine) => void; onCancelResolve: () => void;
}) {
  const [query, setQuery] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [results, setResults] = useState<CatalogResponse | null>(null);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState('');
  const [attentionOnly, setAttentionOnly] = useState(false);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const pendingQuantity = list.lines.some((line) => drafts[line.id] !== undefined && drafts[line.id] !== line.quantity);
  useEffect(() => {
    if (!query.trim()) { setResults(null); setError(''); setSearching(false); return }
    const controller = new AbortController();
    setSearching(true); setResults(null); setError('');
    const timer = setTimeout(() => {
      request<CatalogResponse>(`/catalog?${new URLSearchParams({ q: query, scenario: list.scenario_id, limit: '6', sort: 'recommended' })}`, { signal: controller.signal }).then(setResults).catch((reason: unknown) => { if (!controller.signal.aborted) setError(errorText(reason)) }).finally(() => { if (!controller.signal.aborted) setSearching(false) });
    }, 180);
    return () => { controller.abort(); clearTimeout(timer) };
  }, [query, list.scenario_id]);
  async function addFree() { if (await onFreeLine(query.trim(), categoryId)) { setQuery(''); setResults(null) } }
  function resolve(line: ShoppingLine) { setQuery(line.source_product_name || line.description); onResolve(line); const input = document.getElementById('shopping-search'); input?.scrollIntoView({ block: 'center', behavior: 'instant' }); input?.focus() }
  const priced = list.lines.filter((line) => line.price_summary?.minimum).length;
  const unresolved = list.lines.filter((line) => !line.source_product_id).length;
  const visibleLines = attentionOnly ? list.lines.filter((line) => !line.source_product_id || !line.price_summary?.minimum) : list.lines;
  const comparisonDisabled = busy || comparing || pendingQuantity;
  return <>
    <header className="page-heading"><div><span className="eyebrow">SPAȚIUL TĂU DE ACHIZIȚII</span><h1>Cumpără mai bine, informat.</h1><p>Construiește lista. Verifică alternativele. Alege magazinul.</p></div><button className="button secondary" onClick={onNewList} disabled={busy}><ClipboardList size={17} />Listele mele</button></header>
    <div className="shopping-overview" aria-label="Situația listei"><button className={!attentionOnly ? 'selected' : ''} onClick={() => setAttentionOnly(false)} aria-pressed={!attentionOnly}><ClipboardList size={21} /><span><small>În lista ta</small><strong>{list.lines.length} produse</strong></span></button><div><Check size={21} /><span><small>Cu preț raportat</small><strong>{priced} din {list.lines.length}</strong></span></div><button className={attentionOnly ? 'selected' : ''} onClick={() => setAttentionOnly(!attentionOnly)} aria-pressed={attentionOnly}><ListFilter size={21} /><span><small>{unresolved ? `${unresolved} fără produs ales` : 'Produs sau preț lipsă'}</small><strong>{list.lines.length - priced} de verificat</strong></span><ArrowRight size={17} /></button></div>
    <section className="panel shopping-composer" aria-labelledby="add-product-heading"><div className="composer-heading"><span className="step-number">01</span><div><h2 id="add-product-heading">Ce ai nevoie să cumperi?</h2><p>Caută după denumire, marcă sau ambalaj.</p></div></div>{resolvingLine ? <Notice title={`Alege produsul pentru „${resolvingLine.description}”`} tone="neutral"><button className="text-button" onClick={() => { onCancelResolve(); setQuery('') }}>Anulează asocierea</button></Notice> : null}<SearchField id="shopping-search" label="Produs, marcă sau cerință" value={query} onChange={setQuery} placeholder="De exemplu: lapte Zuzu, cafea Jacobs, hârtie A4" />
      {query.trim() ? <div className="composer-results">
        {error ? <ErrorNotice message={error} /> : null}
        {searching ? <Loading label="Căutăm produse..." /> : results?.items.length ? <><div className="search-results-label"><span>{resolvingLine ? 'Alege produsul pentru linia existentă' : 'Produse găsite'}</span><span>{results.total > 6 ? 'Primele 6 rezultate' : `${results.items.length} rezultate`}</span></div><div className="product-rows">{results.items.map((item) => <ProductCard key={item.id} item={item} categories={categories} sources={sources} onSelect={onSelect} />)}</div></> : results ? <p className="muted">Nu am găsit un produs. Încearcă o altă denumire sau păstrează cerința în listă.</p> : null}
        {!resolvingLine ? <details className="free-need"><summary>Adaugă „{query}” fără a alege încă produsul</summary><div className="free-need-controls"><label className="sr-only" htmlFor="free-category">Categoria cerinței</label><select id="free-category" value={categoryId} onChange={(event) => setCategoryId(event.target.value)}><option value="">De clasificat</option>{categoryOptions(categories).filter(({ category: value }) => value.name.toLocaleLowerCase('ro') !== 'de clasificat').map(({ category: value, label }) => <option key={value.id} value={value.id}>{label}</option>)}</select><button className="button secondary" onClick={addFree} disabled={busy}><Plus size={16} />Adaugă cerința</button></div></details> : null}
      </div> : <div className="composer-suggestions"><span>Căutări rapide:</span>{['Lapte', 'Cafea', 'Apă', 'Hârtie A4'].map((value) => <button key={value} className="suggestion-chip" onClick={() => setQuery(value)}>{value}</button>)}<button className="text-button" onClick={onCatalog}>Catalog <ArrowRight size={14} /></button></div>}
    </section>
    <section className="panel shopping-list" aria-labelledby="list-heading"><div className="section-heading"><div className="list-title"><span className="step-number">02</span><div><h2 id="list-heading">{list.name}</h2><p>{list.lines.length} produse{list.lines.length ? ` · ${priced} cu prețuri disponibile` : ''}</p></div></div>{list.lines.length ? <button className="button primary" onClick={onCompare} disabled={comparisonDisabled}>{comparing ? 'Se compară...' : 'Compară prețurile'}<ArrowRight size={17} /></button> : null}</div>
      {pendingQuantity ? <p className="draft-notice" role="status">Salvează cantitățile modificate înainte de comparație.</p> : null}
      {attentionOnly ? <div className="active-filters"><span>Produse fără asociere sau fără preț în zona aleasă</span><button className="text-button" onClick={() => setAttentionOnly(false)}>Arată toate produsele</button></div> : null}
      {removed ? <div className="undo-notice" role="status"><span>„{removed.description}” a fost eliminat.</span><button className="text-button" onClick={onUndo} disabled={busy}><RotateCcw size={15} />Anulează</button></div> : null}
      {list.lines.length ? <><div className="list-table-head"><span>Produs și caracteristici</span><span>Preț raportat*</span><span>Ambalaje</span></div><div className="list-lines">{visibleLines.map((line) => <ListLine key={line.id} line={line} quantity={drafts[line.id] ?? line.quantity} onDraft={(value) => setDrafts((previous) => { const next = { ...previous }; if (value === undefined) delete next[line.id]; else next[line.id] = value; return next })} categories={categories} busy={busy || comparing} onQuantity={onQuantity} onRemove={onRemove} onResolve={resolve} onOpenProduct={onOpenProduct} />)}</div>{!visibleLines.length ? <div className="list-filter-empty"><Check size={22} /><p>Fiecare poziție are un produs și cel puțin un preț raportat. Comparația verifică dacă ofertele sunt compatibile.</p></div> : null}<div className="list-bottom"><p>*Minime raportate. Comparația verifică separat varianta și baza prețului; cantitățile nu sunt incluse în prețurile afișate mai sus.</p><button className="button primary" onClick={onCompare} disabled={comparisonDisabled}>{comparing ? 'Se compară...' : 'Compară prețurile'}<ArrowRight size={17} /></button></div></> : <EmptyState icon={ClipboardList} title="Lista este goală"><p>Caută un produs mai sus sau încearcă lista cu lapte, cafea și apă.</p><button className="button primary" onClick={onExample} disabled={busy}>Deschide exemplul din Slatina <ArrowRight size={17} /></button></EmptyState>}
    </section>
  </>;
}
