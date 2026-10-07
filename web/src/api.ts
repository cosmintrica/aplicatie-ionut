export interface Money { amount: string; currency: string }
export interface Category { id: string; name: string; parent_id: string | null; product_count: number; quote_count: number }
export interface Scenario { id: string; name: string; latitude: string; longitude: string; radius_m: number; store_count: number }
export interface Company { id: string; name: string; revision: number }
export interface Source { id: string; name: string; product_count: number; quote_count: number }
export interface Snapshot {
  id: string; source_id: string; filename: string; sha256: string; row_count: number; quote_count: number;
  query_scope: string; source_priced_at: string | null; retrieved_at: string | null; missing_fields: string[]; notes: string[];
}
export interface CatalogItem {
  id: string; source_id: string; source_product_id: string; name: string; raw_category: string | null;
  category_id: string; category_reason: string; record_kind: 'source_only'; identity_status: 'unverified';
  quote_count: number; raw_pack: string | null; price: Money | null;
  price_summary?: { minimum: Money | null; maximum: Money | null; spread?: Money | null; offer_count: number; candidate_count: number; conflict_count: number; needs_details_count: number; scope: string; label: string };
  profile?: ProductProfile;
}
export interface ProductProfile { kind?: string | null; brand?: string | null; pack?: { dimension: string; amount: string; unit: string; count?: number; label?: string } | null; fat_percent?: string | null; form?: string | null; variant?: string | null; processing?: string | null; purpose?: string | null; range?: string | null; water_type?: string | null; concentration?: string | null }
export interface UnitPrice extends Money { unit: 'kg' | 'l'; label: string; basis: string }
export interface ShoppingLine { id: string; source_product_id: string | null; source_product_name?: string | null; description: string; quantity: string; unit: 'item'; category_id: string | null; price_summary?: CatalogItem['price_summary']; profile?: ProductProfile }
export interface ShoppingList { id: string; name: string; scenario_id: string; revision: number; lines: ShoppingLine[] }
export interface Capabilities {
  mode: 'offline_snapshot'; network_mode: 'offline'; catalog_count: number; sources: Source[]; limitations: string[];
  features: { ocr: boolean; invoices: boolean; savings: boolean; supplier_recommendations: boolean };
}
export interface Bootstrap { capabilities: Capabilities; csrf_token: string; company: Company; categories: Category[]; scenarios: Scenario[]; snapshots: Snapshot[]; current_list: ShoppingList }
export interface CatalogResponse { items: CatalogItem[]; next_cursor: string | null; total: number }
export interface Quote {
  source_item_id?: string; reference_item_id?: string;
  observation_id: string; line_id: string | null; source_id: string; commercial_name: string; source_catalog_name?: string; raw_brand: string | null;
  raw_unit: string | null; raw_promo: string | null; price: Money | null; source_priced_at: string | null; retrieved_at: string | null;
  relation: 'SOURCE_ASSOCIATION' | 'INCOMPATIBLE' | 'UNRESOLVED'; conflicts: string[]; unknowns: string[];
  verdict?: 'same_variant_candidate' | 'variant_conflict' | 'needs_details'; verdict_label?: string; match_reasons?: string[]; profile?: ProductProfile;
  price_basis?: { status: 'declared_pack' | 'structured_pack' | 'equivalent_one_litre' | 'declared_mass_unit' | 'ambiguous'; label: string; quantity_eligible: boolean };
  estimated_item_total?: Money;
  unit_price?: UnitPrice | null;
  alternative?: { kind: 'different_pack'; status: 'compatible_characteristics' | 'needs_details'; label: string; changes: string[]; reasons: string[] };
  store?: { id: string; name: string; network_name: string | null; address: string | null } | null;
}
export interface OfferResponse { item: CatalogItem; scenario: Scenario; quotes: Quote[]; related_offers?: Quote[]; pack_alternatives?: Quote[]; warnings: string[] }
export interface Evidence extends Quote { snapshot: Snapshot; source_catalog_id: string; source_product_id: string; raw_category: string | null; locator: string; raw_record: unknown }
export interface QuoteSum {
  source_scope: 'geographic_store' | 'network_list';
  store: { id: string; name: string; network_name: string | null; address: string | null };
  quote_coverage_count: number; semantic_coverage_count: number; quantity_coverage_count: number; total_line_count: number;
  reported_quote_sum: Money | null; unadjusted_quote_sum: Money | null; quotes: Quote[];
  missing_lines: { line_id: string; description: string; reason: string }[]; reasons: string[];
}
export interface Comparison {
  id: string; data_mode: 'offline_snapshot'; network_mode: 'offline'; list_id: string; list_revision: number;
  scenario: Scenario; source_snapshot_ids: string[]; algorithm_version: string; currency: string;
  source_quote_sums: QuoteSum[]; payable_total: null; savings: null; rank_basis: 'reported_quotes_only'; warnings: string[];
  line_comparisons?: LineComparison[];
  estimated_baskets?: { store: QuoteSum['store']; estimated_total: Money; difference_from_best: Money; eligible_line_count: number; total_line_count: number; assumptions: string[]; quotes: Quote[] }[];
  estimated_range?: { minimum: Money | null; maximum: Money | null; spread: Money | null };
  estimated_savings?: Money | null;
}
export interface LineComparison {
  source_product_name?: string | null; source_product_id?: string | null;
  line_id: string; description: string; quantity: string; reference_profile: ProductProfile; options: Quote[]; comparable_options: Quote[]; conflicting_options: Quote[]; needs_details_options: Quote[];
  price_min: Money | null; price_max: Money | null; price_spread: Money | null; best_option: Quote | null;
  pack_alternatives?: Quote[];
  unit_price_groups?: { id: string; label: string; unit: 'kg' | 'l'; options: Quote[]; minimum: UnitPrice; maximum: UnitPrice; spread: UnitPrice; best_option: Quote; explanation: string }[];
  groups: { id: string; label: string; profile: ProductProfile; options: Quote[]; minimum: Money | null; maximum: Money | null; spread: Money | null; basis_label: string; estimate_eligible: boolean }[]; warnings: string[];
}

let csrfToken = '';
export function setCsrfToken(token: string) { csrfToken = token }
export class ApiError extends Error {
  constructor(message: string, public readonly code: string, public readonly status: number) { super(message); this.name = 'ApiError' }
}

export async function request<T>(path: string, options: { method?: string; body?: unknown; signal?: AbortSignal } = {}): Promise<T> {
  const method = options.method ?? 'GET';
  const response = await fetch(`/api/v1${path}`, {
    method, signal: options.signal, credentials: 'same-origin',
    headers: { ...(options.body !== undefined ? { 'Content-Type': 'application/json' } : {}), ...(method !== 'GET' ? { 'X-CSRF-Token': csrfToken } : {}) },
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null) as { message?: string; code?: string; detail?: unknown } | null;
    const message = typeof error?.message === 'string' ? error.message : response.status === 409
      ? 'Lista s-a schimbat. Reîncarcă datele și încearcă din nou.'
      : 'Nu am putut finaliza acțiunea. Datele introduse au fost păstrate.';
    throw new ApiError(message, error?.code ?? 'REQUEST_FAILED', response.status);
  }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>;
}

export function errorText(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Aplicația locală nu răspunde. Verifică serverul și reîncearcă; lista salvată rămâne în baza locală.';
}
export function money(value: Money | null | undefined): string {
  if (!value) return 'Nu poate fi calculat';
  const [whole, fraction = ''] = value.amount.split('.');
  const digits = fraction.padEnd(2, '0');
  return `${BigInt(whole || '0').toLocaleString('ro-RO')},${digits} ${value.currency === 'RON' ? 'lei' : value.currency}`;
}
export function dateLabel(value: string | null | undefined): string {
  if (!value) return 'Nespecificată de sursă';
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  if (match) return `${match[3]}.${match[2]}.${match[1]}`;
  return /^(\d{2}\.\d{2}\.\d{4})/.exec(value)?.[1] ?? value;
}
export function sourceTime(value: string | null | undefined): string | null { return value ? /[T ](\d{2}:\d{2})/.exec(value)?.[1] ?? null : null }
export function scopeLabel(value: string): string { return value === 'network_list' ? 'Listă la nivel de rețea' : value === 'slatina_5km' ? 'Slatina · proba cu raza de 5 km' : value === 'bucharest_1km' ? 'București · proba cu raza de 1 km' : value === 'catalog' ? 'Catalogul sursei' : value }
export function missingFieldLabel(value: string): string {
  const labels: Record<string, string> = { GTIN: 'cod de identificare produs', stock: 'stoc', VAT: 'TVA', price_basis: 'baza prețului', shipping: 'transport', business_eligibility: 'condiții pentru firme', source_priced_at: 'data prețului', retrieved_at: 'momentul colectării', validity: 'valabilitate', SGR: 'garanția SGR', pack_size: 'ambalaj' };
  return labels[value] ?? value;
}
export function count(value: number): string { return value.toLocaleString('ro-RO') }
export function categoryOptions(categories: Category[]): { category: Category; label: string }[] {
  const children = new Map<string | null, Category[]>();
  for (const category of categories) {
    const siblings = children.get(category.parent_id) ?? [];
    siblings.push(category);
    children.set(category.parent_id, siblings);
  }
  const result: { category: Category; label: string }[] = [];
  const visited = new Set<string>();
  function visit(category: Category, depth: number) {
    if (visited.has(category.id)) return;
    visited.add(category.id);
    result.push({ category, label: `${depth ? `${'\u00a0\u00a0'.repeat(depth)}- ` : ''}${category.name}` });
    for (const child of children.get(category.id) ?? []) visit(child, depth + 1);
  }
  for (const category of children.get(null) ?? []) visit(category, 0);
  for (const category of categories) if (!visited.has(category.id)) visit(category, 0);
  return result;
}

export function quoteSourceLabel(quote: Quote): string {
  return quote.store?.name ?? (quote.source_id === 'lidl' ? 'Lidl · listă națională' : quote.source_id === 'monitor' ? 'Monitorul Prețurilor' : quote.source_id);
}
