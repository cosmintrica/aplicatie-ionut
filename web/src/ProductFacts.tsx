import type { ProductProfile } from './api';

const labels: Record<string, string> = {
  ground: 'Măcinată', beans: 'Boabe', instant: 'Solubilă', capsules: 'Capsule',
  still: 'Plată', sparkling: 'Carbogazoasă', decaf: 'Decofeinizată',
  fresh: 'Proaspăt', uht: 'UHT', esl: 'ESL',
};

export function ProductFacts({ profile }: { profile?: ProductProfile | null }) {
  if (!profile) return null;
  const facts = [profile.brand, profile.pack?.label,
    profile.fat_percent ? `${profile.fat_percent}% grăsime` : null,
    profile.form, profile.range, profile.variant, profile.processing, profile.water_type, profile.purpose, profile.concentration].filter((value): value is string => !!value);
  if (!facts.length) return null;
  return <div className="product-facts" aria-label="Caracteristici extrase din sursă">{[...new Set(facts)].map((value) => <span key={value}>{labels[value] ?? value}</span>)}</div>;
}
