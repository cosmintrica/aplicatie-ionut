import { useEffect, useState, type FormEvent } from 'react';
import { ArrowRight, BarChart3, Building2, Check, ChevronDown, ClipboardList, Database, FileText, FolderOpen, ListPlus, MapPin, Plus, Settings2, ShoppingBasket, Store } from 'lucide-react';
import { errorText, request, setCsrfToken, type Bootstrap, type CatalogItem, type Company, type Comparison as ComparisonData, type ShoppingLine, type ShoppingList } from './api';
import { Catalog } from './Catalog';
import { Comparison } from './Comparison';
import { Badge, Dialog, EmptyState, ErrorNotice, Loading, Notice } from './components';
import { EvidenceDialog, ProductDialog } from './Details';
import { Shopping } from './Shopping';
import { Sources } from './Sources';

type View = 'shopping' | 'catalog' | 'invoices' | 'analysis' | 'sources';
const navigation = [{ id: 'shopping', name: 'Cumpărături', icon: ShoppingBasket }, { id: 'catalog', name: 'Catalog', icon: Store }, { id: 'invoices', name: 'Facturi', icon: FileText }, { id: 'analysis', name: 'Analiză', icon: BarChart3 }] as const;

function CompanyDialog({ company, onSave, onClose }: { company: Company; onSave: (name: string) => Promise<boolean>; onClose: () => void }) {
  const [name, setName] = useState(company.name);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  async function submit(event: FormEvent) { event.preventDefault(); setSaving(true); setError(''); if (await onSave(name.trim())) onClose(); else setError('Numele nu a putut fi salvat. Verifică mesajul aplicației și reîncearcă.'); setSaving(false) }
  return <Dialog title="Firma ta, pe acest calculator" onClose={onClose}><form onSubmit={submit} className="dialog-form"><p className="muted">Un nume intern este suficient pentru liste. Nu ai nevoie de CUI sau date de contact.</p><div className="field"><label htmlFor="company-name">Numele firmei / spațiului de lucru</label><input id="company-name" value={name} onChange={(event) => setName(event.target.value)} required maxLength={120} /></div>{error ? <ErrorNotice message={error} /> : null}<Notice tone="neutral"><p>Listele sunt păstrate local. Numele firmei nu creează un cont sau protecție pentru utilizatori multipli.</p></Notice><div className="dialog-actions"><button className="button secondary" type="button" onClick={onClose}>Anulează</button><button className="button primary" disabled={saving || !name.trim()}>{saving ? 'Se salvează…' : 'Salvează numele'}</button></div></form></Dialog>;
}

function ListsDialog({ list, busy, onSelect, onCreate, onRename, onClose }: { list: ShoppingList; busy: boolean; onSelect: (id: string) => Promise<boolean>; onCreate: (name: string) => Promise<boolean>; onRename: (name: string) => Promise<boolean>; onClose: () => void }) {
  const [lists, setLists] = useState<ShoppingList[] | null>(null);
  const [name, setName] = useState('');
  const [title, setTitle] = useState(list.name);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => { const controller = new AbortController(); request<{ items: ShoppingList[] }>('/lists', { signal: controller.signal }).then((value) => setLists(value.items)).catch((reason: unknown) => { if (!controller.signal.aborted) setError(errorText(reason)) }); return () => controller.abort() }, [retry]);
  async function create(event: FormEvent) { event.preventDefault(); if (await onCreate(name.trim())) onClose(); else setError('Lista nu a putut fi creată. Datele introduse au fost păstrate.') }
  async function rename(event: FormEvent) { event.preventDefault(); if (await onRename(title.trim())) onClose(); else setError('Numele listei nu a putut fi salvat.') }
  return <Dialog title="Listele tale salvate" onClose={onClose}><div className="dialog-form">{error ? <ErrorNotice message={error} onRetry={() => { setError(''); setRetry((value) => value + 1) }} /> : null}<p className="muted">Listele păstrează cerințele și cantitățile. Prețurile sunt întotdeauna cele din sursele încărcate.</p>{lists ? <div className="saved-lists">{lists.map((value) => <button key={value.id} className={`saved-list-button ${value.id === list.id ? 'selected' : ''}`} onClick={async () => { if (await onSelect(value.id)) onClose() }} disabled={busy}><ClipboardList size={21} aria-hidden="true" /><span><strong>{value.name}</strong><small>{value.lines.length} linii · {value.scenario_id === 'slatina_5km' ? 'Slatina' : 'București'}</small></span>{value.id === list.id ? <Check size={18} aria-hidden="true" /> : <ArrowRight size={18} aria-hidden="true" />}</button>)}</div> : !error ? <Loading /> : null}<form onSubmit={rename} className="rename-list"><div className="field"><label htmlFor="list-title">Numele listei curente</label><input id="list-title" value={title} onChange={(event) => setTitle(event.target.value)} required maxLength={120} /></div><button className="button secondary" disabled={busy || !title.trim() || title === list.name}>Salvează numele</button></form><form onSubmit={create} className="create-list"><h3>Începe o listă nouă</h3><div className="field"><label htmlFor="new-list-name">Numele listei</label><input id="new-list-name" value={name} onChange={(event) => setName(event.target.value)} placeholder="De exemplu: Cumpărături pentru birou" required maxLength={120} /></div><button className="button primary" disabled={busy || !name.trim()}><Plus size={18} aria-hidden="true" />Creează lista</button></form></div></Dialog>;
}

function FuturePage({ view, onShopping }: { view: 'invoices' | 'analysis'; onShopping: () => void }) {
  const invoices = view === 'invoices';
  return <><header className="page-heading"><div><h1>{invoices ? 'Facturi' : 'Analiza achizițiilor'}</h1><p>{invoices ? 'Importul și scanarea facturilor sunt planificate în etapa următoare.' : 'Istoricul de achiziții va permite calculul economiilor și evaluarea furnizorilor.'}</p></div><Badge>În pregătire</Badge></header><section className="panel future-surface"><EmptyState icon={invoices ? FileText : BarChart3} title={invoices ? 'Scanarea OCR nu este încă disponibilă' : 'Nu ai încă un istoric de achiziții'}><p>{invoices ? 'Factura va fi citită, apoi vei putea verifica produsele, cantitățile și prețurile înainte de confirmare.' : 'Poți compara acum variantele și prețurile din lista de cumpărături. Evaluarea furnizorilor are nevoie de facturi confirmate.'}</p><button className="button primary" onClick={onShopping}>Lista de cumpărături <ArrowRight size={17} /></button></EmptyState></section></>;
}

export default function App() {
  const [data, setData] = useState<Bootstrap | null>(null);
  const [view, setView] = useState<View>('shopping');
  const [comparison, setComparison] = useState<ComparisonData | null>(null);
  const [showComparison, setShowComparison] = useState(false);
  const [selected, setSelected] = useState<CatalogItem | null>(null);
  const [evidenceId, setEvidenceId] = useState<string | null>(null);
  const [evidenceReference, setEvidenceReference] = useState<string | undefined>();
  const [showCompany, setShowCompany] = useState(false);
  const [showLists, setShowLists] = useState(false);
  const [busy, setBusy] = useState(false);
  const [comparing, setComparing] = useState(false);
  const [removed, setRemoved] = useState<ShoppingLine | null>(null);
  const [resolvingLine, setResolvingLine] = useState<ShoppingLine | null>(null);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setError('');
    request<Bootstrap>('/bootstrap', { signal: controller.signal }).then((value) => { setCsrfToken(value.csrf_token); setData(value) }).catch((reason: unknown) => { if (!controller.signal.aborted) setError(errorText(reason)) });
    return () => controller.abort();
  }, [retry]);

  function replaceList(list: ShoppingList) {
    setData((previous) => previous ? { ...previous, current_list: list } : previous);
    setComparison(null); setShowComparison(false);
  }
  async function mutateList(path: string, method: string, body?: unknown, successMessage = 'Lista a fost salvată local.'): Promise<boolean> {
    setBusy(true); setError(''); setStatus('');
    try { replaceList(await request<ShoppingList>(path, { method, body })); setStatus(successMessage); return true }
    catch (reason) { setError(errorText(reason)); return false }
    finally { setBusy(false) }
  }
  async function addItem(item: CatalogItem, quantity: string) {
    if (!data) return false;
    if (resolvingLine) {
      const resolved = await mutateList(`/lists/${data.current_list.id}/lines/${resolvingLine.id}`, 'PATCH', { expected_revision: data.current_list.revision, source_product_id: item.id, description: resolvingLine.description, category_id: item.category_id, quantity }, 'Produsul a fost asociat cerinței.');
      if (resolved) setResolvingLine(null);
      return resolved;
    }
    return mutateList(`/lists/${data.current_list.id}/lines`, 'POST', { expected_revision: data.current_list.revision, source_product_id: item.id, description: item.name, quantity, unit: 'item', category_id: item.category_id }, 'Produsul a fost adăugat în lista salvată.');
  }
  async function freeLine(description: string, categoryId: string) {
    if (!data) return false;
    return mutateList(`/lists/${data.current_list.id}/lines`, 'POST', { expected_revision: data.current_list.revision, description, quantity: '1', unit: 'item', category_id: categoryId || null }, 'Cerința a fost păstrată în listă; produsul rămâne de identificat.');
  }
  async function changeQuantity(id: string, quantity: string) {
    if (!data) return false;
    return mutateList(`/lists/${data.current_list.id}/lines/${id}`, 'PATCH', { expected_revision: data.current_list.revision, quantity }, 'Cantitatea a fost salvată. Compară din nou lista pentru un rezultat actualizat.');
  }
  async function removeLine(line: ShoppingLine) {
    if (!data) return;
    if (await mutateList(`/lists/${data.current_list.id}/lines/${line.id}?expected_revision=${data.current_list.revision}`, 'DELETE', undefined, 'Linia a fost eliminată. Poți anula eliminarea.')) setRemoved(line);
  }
  async function undoRemove() {
    if (!data || !removed) return;
    if (await mutateList(`/lists/${data.current_list.id}/lines`, 'POST', { expected_revision: data.current_list.revision, source_product_id: removed.source_product_id, description: removed.description, quantity: removed.quantity, unit: removed.unit, category_id: removed.category_id }, 'Linia a fost restaurată în listă.')) setRemoved(null);
  }
  async function updateScenario(scenarioId: string) {
    if (!data) return;
    await mutateList(`/lists/${data.current_list.id}`, 'PATCH', { expected_revision: data.current_list.revision, scenario_id: scenarioId }, 'Zona a fost schimbată. Compară din nou lista în noua probă.');
  }
  async function compare() {
    if (!data) return;
    setComparing(true); setError(''); setStatus('');
    try { const result = await request<ComparisonData>('/comparisons', { method: 'POST', body: { list_id: data.current_list.id, expected_revision: data.current_list.revision, scenario_id: data.current_list.scenario_id } }); setComparison(result); setShowComparison(true); setView('shopping'); window.scrollTo({ top: 0, behavior: 'instant' }); }
    catch (reason) { setError(errorText(reason)) } finally { setComparing(false) }
  }
  async function example() {
    if (!data) return;
    setBusy(true); setError(''); setStatus('');
    let workingList: ShoppingList | null = null;
    try {
      const items = await Promise.all(['monitor:1012187', 'monitor:1019036', 'monitor:1361463'].map((id) => request<CatalogItem>(`/catalog/${encodeURIComponent(id)}`)));
      workingList = await request<ShoppingList>('/lists', { method: 'POST', body: { name: 'Exemplu Slatina · lapte, cafea 500 g și apă', scenario_id: 'slatina_5km' } });
      for (const item of items) workingList = await request<ShoppingList>(`/lists/${workingList.id}/lines`, { method: 'POST', body: { expected_revision: workingList.revision, source_product_id: item.id, description: item.name, quantity: '1', unit: 'item', category_id: item.category_id } });
      replaceList(workingList); setRemoved(null); setStatus('Exemplul din Slatina a fost salvat ca listă separată. Nu a fost înregistrată o achiziție.');
    } catch (reason) { if (workingList) replaceList(workingList); setError(errorText(reason)) }
    finally { setBusy(false) }
  }
  async function saveCompany(name: string) {
    if (!data) return false;
    setBusy(true); setError('');
    try { const company = await request<Company>('/company', { method: 'PATCH', body: { expected_revision: data.company.revision, name } }); setData((previous) => previous ? { ...previous, company } : previous); setStatus('Numele firmei a fost salvat local.'); return true }
    catch (reason) { setError(errorText(reason)); return false } finally { setBusy(false) }
  }
  async function selectList(id: string) {
    setBusy(true); setError('');
    try { replaceList(await request<ShoppingList>(`/lists/${encodeURIComponent(id)}`)); setRemoved(null); setView('shopping'); setStatus('Lista salvată a fost deschisă.'); return true }
    catch (reason) { setError(errorText(reason)); return false } finally { setBusy(false) }
  }
  async function createList(name: string) { if (!data) return false; const ok = await mutateList('/lists', 'POST', { name, scenario_id: data.current_list.scenario_id }, 'Lista nouă a fost creată și salvată local.'); if (ok) { setRemoved(null); setView('shopping') } return ok }
  async function renameList(name: string) { if (!data) return false; return mutateList(`/lists/${data.current_list.id}`, 'PATCH', { expected_revision: data.current_list.revision, name }, 'Numele listei a fost salvat.') }
  function navigate(next: View) { setView(next); setShowComparison(false); setResolvingLine(null); window.scrollTo({ top: 0, behavior: 'instant' }) }
  function openEvidence(id: string, referenceItemId?: string) { setEvidenceId(id); setEvidenceReference(referenceItemId) }

  if (!data) return <div className="startup"><div className="brand"><span className="brand-icon"><ShoppingBasket size={24} /></span><strong>Achiziții</strong></div>{error ? <ErrorNotice message={error} onRetry={() => setRetry((value) => value + 1)} /> : <Loading label="Se deschide spațiul local al firmei…" />}</div>;
  const list = data.current_list;
  const activeScenario = data.scenarios.find((value) => value.id === list.scenario_id);
  return <div className="app-shell">
    <a className="skip-link" href="#main">Sari la conținut</a>
    <aside className="sidebar"><div className="brand"><span className="brand-icon"><ShoppingBasket size={24} aria-hidden="true" /></span><div><strong>Achiziții</strong><span>Comparații pentru firmă</span></div></div><nav aria-label="Navigare principală">{navigation.map(({ id, name, icon: Icon }) => <button key={id} className={`nav-item ${view === id ? 'active' : ''}`} aria-current={view === id ? 'page' : undefined} onClick={() => navigate(id)}><Icon size={21} aria-hidden="true" />{name}{id === 'shopping' && list.lines.length ? <span className="nav-count">{list.lines.length}</span> : null}</button>)}</nav><div className="sidebar-secondary"><button className="nav-item" onClick={() => setShowLists(true)}><FolderOpen size={20} aria-hidden="true" />Liste salvate</button><button className={`nav-item ${view === 'sources' ? 'active' : ''}`} aria-current={view === 'sources' ? 'page' : undefined} onClick={() => navigate('sources')}><Database size={20} aria-hidden="true" />Surse de date</button></div><div className="sidebar-bottom"><div className="local-dot"><span />Mod local</div><p>Fără actualizare automată.<br />Datele firmei rămân pe calculator.</p><button className="company-sidebar" onClick={() => setShowCompany(true)}><span className="company-avatar"><Building2 size={19} aria-hidden="true" /></span><span><strong>{data.company.name}</strong><small>Spațiu local</small></span><Settings2 size={17} aria-hidden="true" /></button></div></aside>
    <div className="workspace"><header className="topbar"><div className="mobile-brand"><span className="brand-icon"><ShoppingBasket size={20} aria-hidden="true" /></span><strong>Achiziții</strong></div><div className="desktop-context"><Building2 size={17} aria-hidden="true" /><button className="text-button" onClick={() => setShowCompany(true)}>{data.company.name}<ChevronDown size={15} aria-hidden="true" /></button><span className="context-divider" /><span>Achiziții pentru firmă</span></div><div className="topbar-actions"><div className="scenario-picker"><MapPin size={17} aria-hidden="true" /><label className="sr-only" htmlFor="scenario">Zona probelor salvate</label><select id="scenario" value={list.scenario_id} disabled={busy || comparing} onChange={(event) => updateScenario(event.target.value)}>{data.scenarios.map((value) => <option key={value.id} value={value.id}>{value.name}</option>)}</select></div><button className="icon-button mobile-settings" aria-label="Setările firmei locale" onClick={() => setShowCompany(true)}><Settings2 size={20} /></button></div></header>
      <div className="local-mode-bar"><span className="local-dot"><span />Prețuri salvate la 05.10.2026</span><button className="text-button" onClick={() => navigate('sources')}>Surse de date <ArrowRight size={14} aria-hidden="true" /></button></div>
      <main id="main" className="main-content" tabIndex={-1}>{error ? <ErrorNotice message={error} onRetry={() => setRetry((value) => value + 1)} /> : null}{status ? <div className="action-status" role="status"><Check size={17} aria-hidden="true" />{status}</div> : null}
        {view === 'shopping' ? showComparison && comparison ? <Comparison data={comparison} onBack={() => setShowComparison(false)} onEvidence={openEvidence} /> : <Shopping list={list} categories={data.categories} sources={data.capabilities.sources} busy={busy} comparing={comparing} removed={removed} resolvingLine={resolvingLine} onResolve={setResolvingLine} onCancelResolve={() => setResolvingLine(null)} onUndo={undoRemove} onSelect={setSelected} onFreeLine={freeLine} onQuantity={changeQuantity} onRemove={removeLine} onCompare={compare} onExample={example} onCatalog={() => navigate('catalog')} onNewList={() => setShowLists(true)} /> : view === 'catalog' ? <Catalog categories={data.categories} sources={data.capabilities.sources} scenarioId={list.scenario_id} onSelect={setSelected} /> : view === 'sources' ? <Sources data={data} /> : <FuturePage view={view} onShopping={() => navigate('shopping')} />}
        <footer className="page-footer"><span>Achiziții · versiune locală</span><span>{activeScenario?.name} · probe din 05.10.2026</span><button className="text-button mobile-lists" onClick={() => setShowLists(true)}><ListPlus size={16} aria-hidden="true" />Liste salvate</button></footer>
      </main>
    </div>
    <nav className="bottom-nav" aria-label="Navigare principală pe telefon">{navigation.map(({ id, name, icon: Icon }) => <button key={id} className={view === id ? 'active' : ''} aria-current={view === id ? 'page' : undefined} onClick={() => navigate(id)}><Icon size={22} aria-hidden="true" /><span>{name}</span></button>)}</nav>
    {selected ? <ProductDialog item={selected} categories={data.categories} sources={data.capabilities.sources} scenarioId={list.scenario_id} busy={busy} resolving={!!resolvingLine} initialQuantity={resolvingLine?.quantity ?? '1'} onAdd={addItem} onClose={() => setSelected(null)} onEvidence={openEvidence} /> : null}
    {evidenceId ? <EvidenceDialog id={evidenceId} referenceItemId={evidenceReference} onClose={() => setEvidenceId(null)} /> : null}
    {showCompany ? <CompanyDialog company={data.company} onSave={saveCompany} onClose={() => setShowCompany(false)} /> : null}
    {showLists ? <ListsDialog list={list} busy={busy} onSelect={selectList} onCreate={createList} onRename={renameList} onClose={() => setShowLists(false)} /> : null}
  </div>;
}
