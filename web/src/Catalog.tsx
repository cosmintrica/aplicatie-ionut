import { useEffect, useRef, useState } from 'react';
import { ArrowUpRight, Plus, Search } from 'lucide-react';
import { categoryOptions, count, errorText, money, request, type CatalogItem, type CatalogResponse, type Category, type Source } from './api';
import { CategoryIcon, CategoryTag, EmptyState, ErrorNotice, Loading, SearchField } from './components';

export function ProductCard({ item, categories, sources, onSelect }: { item: CatalogItem; categories: Category[]; sources: Source[]; onSelect: (item: CatalogItem) => void }) {
  const category = categories.find((value) => value.id === item.category_id);
  const summary = item.price_summary;
  const price = summary?.minimum ?? item.price;
  const offers = summary?.offer_count ?? item.quote_count;
  return <article className="product-row">
    <span className="product-icon"><CategoryIcon name={category?.name ?? item.name} size={20} /></span>
    <div className="product-row-info"><button className="product-name" onClick={() => onSelect(item)}>{item.name}</button><div className="product-secondary"><CategoryTag categoryId={item.category_id} categories={categories} /><span>{item.raw_pack || sources.find((value) => value.id === item.source_id)?.name || item.source_id}</span></div></div>
    <div className="product-row-price">{price ? <><small>Minim raportat</small><strong>{money(price)}</strong><span>{offers} {offers === 1 ? 'preț salvat' : 'prețuri salvate'}</span></> : <><strong className="no-price">Fără preț</strong><span>În datele acestei zone</span></>}</div>
    <button className="icon-button row-add" type="button" aria-label={`Vezi și adaugă ${item.name}`} onClick={() => onSelect(item)}><Plus size={20} /></button>
  </article>;
}

export function Catalog({ categories, sources, scenarioId, onSelect, initialCategory = '' }: { categories: Category[]; sources: Source[]; scenarioId: string; onSelect: (item: CatalogItem) => void; initialCategory?: string }) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState(initialCategory);
  const [source, setSource] = useState('');
  const [pricedOnly, setPricedOnly] = useState(true);
  const [sort, setSort] = useState('recommended');
  const [data, setData] = useState<CatalogResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [moreLoading, setMoreLoading] = useState(false);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const generation = useRef(0);
  function params(cursor?: string) {
    const value = new URLSearchParams({ q: query, scenario: scenarioId, limit: '30', availability: pricedOnly ? 'priced' : 'all', sort });
    if (category) value.set('category', category);
    if (source) value.set('source', source);
    if (cursor) value.set('cursor', cursor);
    return value;
  }
  useEffect(() => {
    const controller = new AbortController();
    const current = ++generation.current;
    const timer = setTimeout(() => {
      setLoading(true); setError('');
      const value = new URLSearchParams({ q: query, scenario: scenarioId, limit: '30', availability: pricedOnly ? 'priced' : 'all', sort });
      if (category) value.set('category', category);
      if (source) value.set('source', source);
      request<CatalogResponse>(`/catalog?${value}`, { signal: controller.signal }).then((result) => { if (current === generation.current) setData(result) }).catch((reason: unknown) => { if (!controller.signal.aborted) setError(errorText(reason)) }).finally(() => { if (!controller.signal.aborted) setLoading(false) });
    }, query ? 180 : 0);
    return () => { clearTimeout(timer); controller.abort() };
  }, [query, category, source, scenarioId, pricedOnly, sort, retry]);
  async function loadMore() {
    if (!data?.next_cursor) return;
    const current = generation.current;
    setMoreLoading(true); setError('');
    try { const next = await request<CatalogResponse>(`/catalog?${params(data.next_cursor)}`); if (current === generation.current) setData((previous) => previous ? { ...next, items: [...previous.items, ...next.items] } : next) }
    catch (reason) { setError(errorText(reason)) } finally { setMoreLoading(false) }
  }
  return <>
    <header className="page-heading"><div><h1>Catalog de produse</h1><p>Caută produsul, verifică prețurile și adaugă-l în lista de cumpărături.</p></div></header>
    <section className="panel catalog-panel" aria-labelledby="catalog-results-title">
      <div className="catalog-toolbar"><SearchField id="catalog-search" value={query} onChange={setQuery} label="Caută în catalog" placeholder="Produs, marcă, gramaj..." /><div className="field"><label htmlFor="catalog-category">Categorie</label><select id="catalog-category" value={category} onChange={(event) => setCategory(event.target.value)}><option value="">Toate categoriile</option>{categoryOptions(categories).map(({ category: value, label }) => <option key={value.id} value={value.id}>{label}</option>)}</select></div><div className="field"><label htmlFor="catalog-source">Sursă</label><select id="catalog-source" value={source} onChange={(event) => setSource(event.target.value)}><option value="">Toate sursele</option>{sources.map((value) => <option key={value.id} value={value.id}>{value.name}</option>)}</select></div></div>
      <div className="result-toolbar"><h2 id="catalog-results-title">{data && !loading ? `${count(data.total)} produse` : 'Produse'}</h2><label className="checkbox-label"><input type="checkbox" checked={pricedOnly} onChange={(event) => setPricedOnly(event.target.checked)} />Doar produse cu preț</label><div className="sort-picker"><label htmlFor="catalog-sort">Ordine</label><select id="catalog-sort" value={sort} onChange={(event) => setSort(event.target.value)}><option value="recommended">Relevanță</option><option value="price">Preț crescător</option><option value="name">Denumire</option></select></div></div>
      {error ? <ErrorNotice message={error} onRetry={() => setRetry((value) => value + 1)} /> : null}
      {loading ? <Loading label="Căutăm produse..." /> : data?.items.length ? <><div className="product-rows">{data.items.map((item) => <ProductCard key={item.id} item={item} categories={categories} sources={sources} onSelect={onSelect} />)}</div>{data.next_cursor ? <div className="load-more"><button className="button secondary" onClick={loadMore} disabled={moreLoading}>{moreLoading ? 'Se încarcă...' : 'Arată mai multe produse'}<ArrowUpRight size={16} /></button></div> : null}</> : !error ? <EmptyState icon={Search} title={pricedOnly ? 'Nu avem prețuri pentru această căutare' : 'Nu am găsit produsul'}><p>{pricedOnly ? 'Debifează „Doar produse cu preț” pentru a căuta în catalogul complet, sau încearcă o altă marcă.' : 'Încearcă o altă denumire. Poți păstra cerința ca text în lista ta.'}</p></EmptyState> : null}
    </section>
  </>;
}
