import { useEffect, useState } from 'react';
import { ArrowUpRight, Package, Plus } from 'lucide-react';
import { dateLabel, errorText, money, quoteSourceLabel, request, sourceTime, type CatalogItem, type Category, type Evidence, type OfferResponse, type Quote, type Source } from './api';
import { Badge, CategoryTag, Dialog, ErrorNotice, Loading } from './components';
import { ProductFacts } from './ProductFacts';

export function relationLabel(quote: Quote): string {
  return quote.verdict_label ?? (quote.verdict === 'same_variant_candidate' ? 'Aceleași caracteristici' : quote.verdict === 'variant_conflict' || quote.relation === 'INCOMPATIBLE' ? 'Variantă diferită' : 'Detalii de verificat');
}
export function relationTone(quote: Quote): 'green' | 'amber' | 'neutral' {
  return quote.verdict === 'same_variant_candidate' ? 'green' : quote.verdict === 'variant_conflict' || quote.conflicts.length ? 'amber' : 'neutral';
}
export function QuoteCard({ quote, onEvidence, storeName }: { quote: Quote; onEvidence: (id: string, referenceItemId?: string) => void; storeName?: string }) {
  const reasons = quote.match_reasons?.length ? quote.match_reasons : quote.conflicts;
  return <article className={`quote-card ${quote.verdict === 'variant_conflict' ? 'has-conflict' : ''}`}>
    <div className="quote-card-heading"><div><strong>{storeName ?? quoteSourceLabel(quote)}</strong><p>{quote.commercial_name}</p></div><div className="quote-price-block"><strong className="quote-price">{quote.price ? money(quote.price) : 'Fără preț'}</strong>{quote.unit_price ? <span className="unit-price" title={quote.unit_price.basis}>{quote.unit_price.label}</span> : null}<small>{quote.price_basis?.label ?? (quote.raw_unit ? `Unitate sursă: ${quote.raw_unit}` : '')}</small></div></div>
    <div className="quote-card-footer"><Badge tone={relationTone(quote)}>{relationLabel(quote)}</Badge><button className="text-button" onClick={() => onEvidence(quote.observation_id, quote.reference_item_id ?? quote.source_item_id)}>Detalii <ArrowUpRight size={14} /></button></div>
    {reasons.length ? <details className="inline-details"><summary>De ce?</summary><ul>{reasons.map((value, index) => <li key={index}>{value}</li>)}</ul></details> : null}
  </article>;
}

export function ProductDialog({ item, categories, sources, scenarioId, busy, onAdd, onClose, onEvidence, onOpenProduct, resolving = false, initialQuantity = '1' }: { item: CatalogItem; categories: Category[]; sources: Source[]; scenarioId: string; busy: boolean; onAdd: (item: CatalogItem, quantity: string) => Promise<boolean>; onClose: () => void; onEvidence: (id: string, referenceItemId?: string) => void; onOpenProduct: (id: string) => void; resolving?: boolean; initialQuantity?: string }) {
  const [offers, setOffers] = useState<OfferResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [quantity, setQuantity] = useState(initialQuantity);
  const [retry, setRetry] = useState(0);
  const validQuotes = [...new Map([...(offers?.quotes ?? []), ...(offers?.related_offers ?? [])].filter((quote) => quote.price !== null).map((quote) => [quote.observation_id, quote])).values()].sort((a, b) => Number(a.price!.amount) - Number(b.price!.amount));
  const matchingQuotes = validQuotes.filter((quote) => quote.verdict === 'same_variant_candidate');
  const differentQuotes = validQuotes.filter((quote) => quote.verdict === 'variant_conflict');
  const uncertainQuotes = validQuotes.filter((quote) => quote.verdict !== 'same_variant_candidate' && quote.verdict !== 'variant_conflict');
  const unavailableQuotes = offers?.quotes.filter((quote) => quote.price === null) ?? [];
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setOffers(null); setError('');
    request<OfferResponse>(`/offers?${new URLSearchParams({ item: item.id, scenario: scenarioId })}`, { signal: controller.signal }).then(setOffers).catch((reason: unknown) => { if (!controller.signal.aborted) setError(errorText(reason)) }).finally(() => { if (!controller.signal.aborted) setLoading(false) });
    return () => controller.abort();
  }, [item.id, scenarioId, retry]);
  async function add() {
    if (!quantity.trim()) { setError('Introdu cantitatea.'); return }
    if (await onAdd(item, quantity.replace(',', '.'))) onClose();
    else setError('Produsul nu a putut fi salvat. Cantitatea introdusă a fost păstrată.');
  }
  return <Dialog title="Produs și prețuri" onClose={onClose} wide>
    <div className="product-dialog-summary"><CategoryTag categoryId={item.category_id} categories={categories} /><h3>{item.name}</h3><ProductFacts profile={item.profile} /><p>{sources.find((value) => value.id === item.source_id)?.name ?? item.source_id}</p></div>
    <div className="product-add-form"><div className="field"><label htmlFor="product-quantity">Cantitate / ambalaje</label><input id="product-quantity" inputMode="decimal" value={quantity} onChange={(event) => setQuantity(event.target.value)} /></div><button className="button primary" disabled={busy} onClick={add}><Plus size={17} />{busy ? 'Se salvează...' : resolving ? 'Asociază produsul' : 'Adaugă în listă'}</button></div>
    <section className="dialog-quotes" aria-labelledby="product-quotes-heading"><div className="section-heading"><h3 id="product-quotes-heading">Aceleași caracteristici</h3>{offers ? <span className="muted">{matchingQuotes.length} {matchingQuotes.length === 1 ? 'ofertă candidată' : 'oferte candidate'}</span> : null}</div><p className="subtle-note">Marca, varianta și ambalajul corespund datelor disponibile. Identitatea exactă și stocul se verifică la cumpărare. Prețuri salvate la 05.10.2026.</p>
      {error ? <ErrorNotice message={error} onRetry={() => setRetry((value) => value + 1)} /> : null}
      {loading ? <Loading /> : matchingQuotes.length ? <div className="quote-grid">{matchingQuotes.map((quote) => <QuoteCard key={quote.observation_id} quote={quote} onEvidence={onEvidence} />)}</div> : !error ? <div className="match-empty"><Package size={21} /><p>{validQuotes.length ? 'Avem prețuri raportate, dar caracteristicile necesită verificare. Vezi grupurile de mai jos.' : 'Nu avem un preț pentru acest produs în datele zonei. Îl poți păstra în listă.'}</p></div> : null}
      {!loading && uncertainQuotes.length ? <details className="disclosure" open={!matchingQuotes.length}><summary>{uncertainQuotes.length} {uncertainQuotes.length === 1 ? 'ofertă cu detalii de verificat' : 'oferte cu detalii de verificat'}</summary><div className="quote-grid">{uncertainQuotes.map((quote) => <QuoteCard key={quote.observation_id} quote={quote} onEvidence={onEvidence} />)}</div></details> : null}
      {!loading && differentQuotes.length ? <details className="disclosure"><summary>{differentQuotes.length} oferte cu alte caracteristici</summary><p className="subtle-note">Aceste variante nu intră în estimarea coșului pentru produsul ales.</p><div className="quote-grid">{differentQuotes.map((quote) => <QuoteCard key={quote.observation_id} quote={quote} onEvidence={onEvidence} />)}</div></details> : null}
      {!loading && unavailableQuotes.length ? <details className="disclosure"><summary>{unavailableQuotes.length} magazine fără preț pentru produs</summary><div className="quote-grid">{unavailableQuotes.map((quote) => <QuoteCard key={quote.observation_id} quote={quote} onEvidence={onEvidence} />)}</div></details> : null}
      {!loading && offers?.pack_alternatives?.length ? <section className="pack-discovery"><div className="section-heading"><div><span className="eyebrow">ALTERNATIVE DE AMBALAJ</span><h3>Merită un alt gramaj?</h3></div><Package size={24} /></div><p className="subtle-note">Compară costul pe kilogram sau litru. Deschide alternativa și verifică numărul de ambalaje înainte să o alegi.</p><div className="alternative-grid">{offers.pack_alternatives.map((quote) => <article className="alternative-card" key={quote.observation_id}><Badge tone={quote.alternative?.status === 'compatible_characteristics' ? 'green' : 'amber'}>{quote.alternative?.label ?? 'Alt ambalaj'}</Badge><h4>{quote.commercial_name}</h4><span className="source-name">{quoteSourceLabel(quote)}</span><ProductFacts profile={quote.profile} /><div className="alternative-prices"><strong>{money(quote.price)}</strong>{quote.unit_price ? <span className="unit-price" title={quote.unit_price.basis}>{quote.unit_price.label}</span> : <span>Baza prețului necesită verificare</span>}</div><ul>{quote.alternative?.changes.map((value) => <li key={value}>{value}</li>)}</ul>{quote.alternative?.reasons.length ? <details className="inline-details"><summary>Ce a verificat comparația?</summary><ul>{quote.alternative.reasons.map((value) => <li key={value}>{value}</li>)}</ul></details> : null}<div className="alternative-actions">{quote.source_item_id ? <button className="button secondary" disabled={busy} onClick={() => onOpenProduct(quote.source_item_id!)}>Vezi produsul <ArrowUpRight size={16} /></button> : null}<button className="text-button" onClick={() => onEvidence(quote.observation_id, quote.reference_item_id)}>Sursa prețului</button></div></article>)}</div></section> : null}
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
      <div className="evidence-heading"><span className="source-name">{quoteSourceLabel(data)}</span><h3>{data.commercial_name}</h3><strong className="evidence-price">{money(data.price)}</strong><Badge tone={relationTone(data)}>{relationLabel(data)}</Badge></div>
      {data.match_reasons?.length || data.conflicts.length ? <div className="match-explanation"><h3>Verificarea variantei</h3><ul>{(data.match_reasons?.length ? data.match_reasons : data.conflicts).map((value, index) => <li key={index}>{value}</li>)}</ul></div> : null}
      <dl className="detail-grid"><div><dt>Denumirea catalogului</dt><dd>{data.source_catalog_name || 'Nespecificată'}</dd></div><div><dt>Unitatea sursei</dt><dd>{data.raw_unit || 'Nespecificată'}</dd></div><div><dt>Marca sursei</dt><dd>{data.raw_brand || 'Nespecificată'}</dd></div><div><dt>Ambalaj / baza prețului</dt><dd>{data.price_basis?.label ?? 'De verificat'}</dd></div><div><dt>Data prețului</dt><dd>{dateLabel(data.source_priced_at)}{sourceTime(data.source_priced_at) ? <small>Ora {sourceTime(data.source_priced_at)}</small> : null}</dd></div><div><dt>Colectat la</dt><dd>{dateLabel(data.retrieved_at)}</dd></div><div><dt>Promoție</dt><dd>{data.raw_promo || 'Nespecificată'}</dd></div><div><dt>Stoc</dt><dd>De verificat în magazin</dd></div></dl>
      {data.unknowns.length ? <details className="disclosure"><summary>Informații care lipsesc</summary><ul>{data.unknowns.map((value, index) => <li key={index}>{value}</li>)}</ul></details> : null}
      <details className="disclosure"><summary>Sursa și înregistrarea originală</summary><dl className="detail-grid"><div><dt>Fișier</dt><dd>{data.snapshot.filename}</dd></div><div><dt>Poziție</dt><dd>{data.locator}</dd></div><div><dt>ID catalog</dt><dd>{data.source_catalog_id}</dd></div><div><dt>ID produs</dt><dd>{data.source_product_id}</dd></div><div><dt>Categorie originală</dt><dd>{data.raw_category || 'Nespecificată'}</dd></div></dl><p className="hash-text">SHA-256: {data.snapshot.sha256}</p><pre>{typeof data.raw_record === 'string' ? data.raw_record : JSON.stringify(data.raw_record, null, 2)}</pre></details>
    </> : <Loading label="Se deschid detaliile..." />}
  </Dialog>;
}
