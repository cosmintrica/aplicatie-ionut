import { useEffect, useId, useRef, type ReactNode } from 'react';
import { AlertCircle, ArrowRight, Check, Coffee, Droplets, FileText, Layers3, Laptop, Milk, Package, Printer, Search, ShieldCheck, Sparkles, X, type LucideIcon } from 'lucide-react';
import type { Category } from './api';

export function CategoryIcon({ name, size = 22 }: { name: string; size?: number }) {
  const value = name.toLocaleLowerCase('ro');
  const Icon: LucideIcon = /cafea|ceai/.test(value) ? Coffee : /lapte|lactat/.test(value) ? Milk
    : /apă|băut/.test(value) ? Droplets : /electronic|laptop|telefon/.test(value) ? Laptop
      : /imprim|toner|cartuș/.test(value) ? Printer : /birotic|hârtie|igien/.test(value) ? FileText
        : /curăț/.test(value) ? Sparkles : /alimente/.test(value) ? Milk : Package;
  return <Icon size={size} aria-hidden="true" />;
}
export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'green' | 'amber' }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}
export function SnapshotNotice({ compact = false }: { compact?: boolean }) {
  return <div className={`snapshot-notice ${compact ? 'compact' : ''}`}>
    <Layers3 size={18} aria-hidden="true" />
    <div><strong>Prețuri din datele salvate la 05.10.2026</strong>{!compact ? <p>Verifică prețul și stocul înainte de cumpărare.</p> : null}</div>
  </div>;
}
export function Notice({ children, title, tone = 'amber' }: { children: ReactNode; title?: string; tone?: 'amber' | 'neutral' }) {
  return <div className={`notice notice-${tone}`}><AlertCircle size={20} aria-hidden="true" /><div>{title ? <strong>{title}</strong> : null}<div>{children}</div></div></div>;
}
export function ErrorNotice({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return <div className="error-notice" role="alert"><AlertCircle size={20} aria-hidden="true" /><div><strong>Acțiunea nu a fost finalizată</strong><p>{message}</p>{onRetry ? <button className="text-button" onClick={onRetry}>Reîncearcă <ArrowRight size={16} /></button> : null}</div></div>;
}
export function EmptyState({ icon: Icon = Package, title, children, action }: { icon?: LucideIcon; title: string; children: ReactNode; action?: ReactNode }) {
  return <div className="empty-state"><span className="empty-icon"><Icon size={28} aria-hidden="true" /></span><h3>{title}</h3><div className="empty-copy">{children}</div>{action}</div>;
}
export function Loading({ label = 'Se încarcă datele locale…' }: { label?: string }) {
  return <div className="loading" role="status"><span className="spinner" aria-hidden="true" />{label}</div>;
}
export function Dialog({ title, children, onClose, wide = false }: { title: string; children: ReactNode; onClose: () => void; wide?: boolean }) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => { const dialog = ref.current; dialog?.showModal(); return () => dialog?.close() }, []);
  return <dialog ref={ref} aria-labelledby={titleId} className={`dialog ${wide ? 'dialog-wide' : ''}`} onCancel={onClose} onClick={(event) => { if (event.target === event.currentTarget) onClose() }}>
    <div className="dialog-surface"><div className="dialog-header"><h2 id={titleId}>{title}</h2><button type="button" className="icon-button" aria-label="Închide" onClick={onClose}><X size={22} /></button></div>{children}</div>
  </dialog>;
}
export function SearchField({ value, onChange, label, placeholder = 'Caută după produs, marcă sau variantă…', id }: { value: string; onChange: (value: string) => void; label: string; placeholder?: string; id: string }) {
  return <div className="search-field"><label htmlFor={id}>{label}</label><div className="search-input"><Search size={21} aria-hidden="true" /><input id={id} type="search" value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} autoComplete="off" /></div></div>;
}
export function CategoryTag({ categoryId, categories }: { categoryId: string | null; categories: Category[] }) {
  return <span className="category-tag">{categories.find((category) => category.id === categoryId)?.name ?? 'De clasificat'}</span>;
}
export function CoverageMetric({ label, value, total, confirmed = false }: { label: string; value: number; total: number; confirmed?: boolean }) {
  return <div className="coverage-metric"><span className={`metric-icon ${confirmed ? 'confirmed' : ''}`}>{confirmed ? <Check size={15} aria-hidden="true" /> : <ShieldCheck size={16} aria-hidden="true" />}</span><div><strong>{value} / {total}</strong><span>{label}</span></div></div>;
}
