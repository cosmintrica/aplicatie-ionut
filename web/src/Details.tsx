import { useEffect, useState } from 'react';
import { ArrowUpRight, Package, Plus } from 'lucide-react';
import { dateLabel, errorText, money, request, sourceTime, type CatalogItem, type Category, type Evidence, type OfferResponse, type Quote, type Source } from './api';
import { Badge, CategoryTag, Dialog, EmptyState, ErrorNotice, Loading } from './components';

export function relationLabel(quote: Quote): string {
  return quote.verdict_label ?? (quote.verdict === 'same_variant_candidate' ? 'Aceleași caracteristici' : quote.verdict === 'variant_conflict' || quote.relation === 'INCOMPATIBLE' ? 'Variantă diferită' : 'Detalii de verificat');
}
export function relationTone(quote: Quote): 'green' | 'amber' | 'neutral' {
  return quote.verdict === 'same_variant_candidate' ? 'green' : quote.verdict === 'variant_conflict' || quote.conflicts.length ? 'amber' : 'neutral';
}
export function QuoteCard({ quote, onEvidence, storeName }: { quote: Quote; onEvidence: (id: string, referenceItemId?: string) => void; storeName?: string }) {
  const reasons = quote.match_reasons?.length ? quote.match_reasons : quote.conflicts;
  return <article className={`quote-card ${quote.verdict === 'variant_conflict' ? 'has-conflict' : ''}`}>
    <div className="quote-card-heading"><div><strong>{storeName ?? quote.store?.name ?? quote.source_id}</strong><p>{quote.commercial_name}</p></div><div className="quote-price-block"><strong className="quote-price">{quote.price ? money(quote.price) : 'Fără preț'}</strong><small>{quote.price_basis?.label ?? (quote.raw_unit ? `Unitate sursă: ${quote.raw_unit}` : '')}</small></div></div>
    <div className="quote-card-footer"><Badge tone={relationTone(quote)}>{relationLabel(quote)}</Badge><button className="text-button" onClick={() => onEvidence(quote.observation_id, quote.reference_item_id ?? quote.source_item_id)}>Detalii <ArrowUpRight size={14} /></button></div>
    {reasons.length ? <details className="inline-details"><summary>De ce?</summary><ul>{reasons.map((value, index) => <li key={index}>{value}</li>)}</ul></details> : null}
  </article>;
}

export function ProductDialog({ item, categories, sources, scenarioId, busy, onAdd, onClose, onEvidence, resolving = false, initialQuantity = '1' }: { item: CatalogItem; categories: Category[]; sources: Source[]; scenarioId: string; busy: boolean; onAdd: (item: CatalogItem, quantity: string) => Promise<boolean>; onClose: () => void; onEvidence: (id: string, referenceItemId?: string) => void; resolving?: boolean; initialQuantity?: string }) {
  const [offers, setOffers] = useState<OfferResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [quantity, setQuantity] = useState(initialQuantity);
  const [retry, setRetry] = useState(0);
  const validQuotes = offers?.quotes.filter((quote) => quote.price !== null).sort((a, b) => Number(a.price!.amount) - Number(b.price!.amount)) ?? [];
  const unavailableQuotes = offers?.quotes.filter((quote) => quote.price === null) ?? [];
  const relatedQuotes = offers?.related_offers?.filter((quote) => quote.price) ?? [];
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError('');
    request<OfferResponse>(`/offers?${new URLSearchParams({ item: item.id, scenario: scenarioId })}`, { signal: controller.signal }).then(setOffers).catch((reason: unknown) => { if (!controller.signal.aborted) setError(errorText(reason)) }).finally(() => { if (!controller.signal.aborted) setLoading(false) });
    return () => controller.abort();
  }, [item.id, scenarioId, retry]);
  async function add() {
    if (!quantity.trim()) { setError('Introdu cantitatea.'); return }
    if (await onAdd(item, quantity.replace(',', '.'))) onClose();
    else setError('Produsul nu a putut fi salvat. Cantitatea introdusă a fost păstrată.');
  }
  return <Dialog title="Produs și prețuri" onClose={onClose} wide>
    <div className="product-dialog-summary"><CategoryTag categoryId={item.category_id} categories={categories} /><h3>{item.name}</h3><p>{item.raw_pack ? `${item.raw_pack} · ` : ''}{sources.find((value) => value.id === item.source_id)?.name ?? item.source_id}</p></div>
    <div className="product-add-form"><div className="field"><label htmlFor="product-quantity">Cantitate / ambalaje</label><input id="product-quantity" inputMode="decimal" value={quantity} onChange={(event) => setQuantity(event.target.value)} /></div><button className="button primary" disabled={busy} onClick={add}><Plus size={17} />{busy ? 'Se salvează...' : resolving ? 'Asociază produsul' : 'Adaugă în listă'}</button></div>
    <section className="dialog-quotes" aria-labelledby="product-quotes-heading"><div className="section-heading"><h3 id="product-quotes-heading">Prețuri în magazine</h3>{offers ? <span className="muted">{validQuotes.length} prețuri salvate</span> : null}</div><p className="subtle-note">Prețuri salvate la 05.10.2026. Asocierea probabilă verifică marca, varianta și ambalajul; codul produsului rămâne de confirmat.</p>
      {error ? <ErrorNotice message={error} onRetry={() => setRetry((value) => value + 1)} /> : null}
      {loading ? <Loading /> : validQuotes.length ? <div className="quote-grid">{validQuotes.map((quote) => <QuoteCard key={quote.observation_id} quote={quote} onEvidence={onEvidence} />)}</div> : !error ? <EmptyState icon={Package} title="Nu avem un preț pentru acest produs"><p>Îl poți păstra în listă. În datele zonei nu există o ofertă pentru el.</p></EmptyState> : null}
      {!loading && unavailableQuotes.length ? <details className="disclosure"><summary>{unavailableQuotes.length} magazine fără preț pentru produs</summary><div className="quote-grid">{unavailableQuotes.map((quote) => <QuoteCard key={quote.observation_id} quote={quote} onEvidence={onEvidence} />)}</div></details> : null}
      {!loading && relatedQuotes.length ? <section className="related-offers"><h3>Prețuri găsite pentru înregistrări similare</h3><p className="subtle-note">Aceste oferte provin din alte înregistrări ale catalogului, asociate prin caracteristicile declarate.</p><div className="quote-grid">{relatedQuotes.map((quote) => <QuoteCard key={quote.observation_id} quote={quote} onEvidence={onEvidence} />)}</div></section> : null}
      {offers?.warnings.length ? <details className="disclosure"><summary>Condiții și limite ale datelor</summary><ul>{offers.warnings.map((value, index) => <li key={index}>{value}</li>)}</ul></details> : null}
    </section>
  </Dialog>;
}

export function EvidenceDialog({ id, referenceItemId, onClose }: { id: string; referenceItemId?: string; onClose: () => void }) {
  const [data, setData] = useState<Evidence | null>(null);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setError(''); setData(null);
    request<Evidence>(`/evidence/${encodeURIComponent(id)}${referenceItemId ? `?reference_item_id=${encodeURIComponent(referenceItemId)}` : ''}`, { signal: controller.signal }).then(setData).catch((reason: unknown) => { if (!controller.signal.aborted) setError(errorText(reason)) });
    return () => controller.abort();
  }, [id, referenceItemId, retry]);
  return <Dialog title="Detalii despre preț" onClose={onClose} wide>
    {error ? <ErrorNotice message={error} onRetry={() => setRetry((value) => value + 1)} /> : data ? <>
      <div className="evidence-heading"><span className="source-name">{data.store?.name ?? data.source_id}</span><h3>{data.commercial_name}</h3><strong className="evidence-price">{money(data.price)}</strong><Badge tone={relationTone(data)}>{relationLabel(data)}</Badge></div>
      {data.match_reasons?.length || data.conflicts.length ? <div className="match-explanation"><h3>Verificarea variantei</h3><ul>{(data.match_reasons?.length ? data.match_reasons : data.conflicts).map((value, index) => <li key={index}>{value}</li>)}</ul></div> : null}
      <dl className="detail-grid"><div><dt>Denumirea catalogului</dt><dd>{data.source_catalog_name || 'Nespecificată'}</dd></div><div><dt>Unitatea sursei</dt><dd>{data.raw_unit || 'Nespecificată'}</dd></div><div><dt>Marca sursei</dt><dd>{data.raw_brand || 'Nespecificată'}</dd></div><div><dt>Ambalaj / baza prețului</dt><dd>{data.price_basis?.label ?? 'De verificat'}</dd></div><div><dt>Data prețului</dt><dd>{dateLabel(data.source_priced_at)}{sourceTime(data.source_priced_at) ? <small>Ora {sourceTime(data.source_priced_at)}</small> : null}</dd></div><div><dt>Colectat la</dt><dd>{dateLabel(data.retrieved_at)}</dd></div><div><dt>Promoție</dt><dd>{data.raw_promo || 'Nespecificată'}</dd></div><div><dt>Stoc</dt><dd>De verificat în magazin</dd></div></dl>
      {data.unknowns.length ? <details className="disclosure"><summary>Informații care lipsesc</summary><ul>{data.unknowns.map((value, index) => <li key={index}>{value}</li>)}</ul></details> : null}
      <details className="disclosure"><summary>Sursa și înregistrarea originală</summary><dl className="detail-grid"><div><dt>Fișier</dt><dd>{data.snapshot.filename}</dd></div><div><dt>Poziție</dt><dd>{data.locator}</dd></div><div><dt>ID catalog</dt><dd>{data.source_catalog_id}</dd></div><div><dt>ID produs</dt><dd>{data.source_product_id}</dd></div><div><dt>Categorie originală</dt><dd>{data.raw_category || 'Nespecificată'}</dd></div></dl><p className="hash-text">SHA-256: {data.snapshot.sha256}</p><pre>{typeof data.raw_record === 'string' ? data.raw_record : JSON.stringify(data.raw_record, null, 2)}</pre></details>
    </> : <Loading label="Se deschid detaliile..." />}
  </Dialog>;
}
