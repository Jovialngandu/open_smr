export interface AssessmentLevel {
  value: number;
  label: string;
  description: string;
}

// Ces échelles suivent les bornes actuellement validées par Django.
export const DIC_LEVELS: readonly AssessmentLevel[] = [
  { value: 1, label: 'Faible / minime', description: 'Impact négligeable sur l’organisation.' },
  { value: 2, label: 'Moyen / modéré', description: 'Perturbation limitée, sans perte financière critique.' },
  { value: 3, label: 'Élevé / critique', description: 'Impact majeur, pouvant aller jusqu’à l’arrêt d’un service critique ou à une non-conformité légale majeure.' },
];

export const LIKELIHOOD_LEVELS: readonly AssessmentLevel[] = [
  { value: 1, label: 'Rare', description: 'Improbable ; moins d’une fois tous les cinq ans.' },
  { value: 2, label: 'Improbable', description: 'Peut se produire sous certaines conditions.' },
  { value: 3, label: 'Probable', description: 'S’est déjà produit ou est susceptible de se produire.' },
  { value: 4, label: 'Très probable', description: 'Attendu régulièrement.' },
  { value: 5, label: 'Quasi certain', description: 'Attendu très fréquemment ou déjà récurrent.' },
];

export const IMPACT_LEVELS: readonly AssessmentLevel[] = [
  { value: 1, label: 'Mineur', description: 'Conséquences limitées, sans interruption notable.' },
  { value: 2, label: 'Modéré', description: 'Perturbation maîtrisable avec les moyens habituels.' },
  { value: 3, label: 'Significatif', description: 'Pertes ou interruption sensibles pour l’activité.' },
  { value: 4, label: 'Grave', description: 'Interruption importante ou pertes financières élevées.' },
  { value: 5, label: 'Critique', description: 'Arrêt d’un service essentiel ou conséquences légales majeures.' },
];

export function assessmentLevel(levels: readonly AssessmentLevel[], value: number | string): AssessmentLevel {
  return levels.find((level) => level.value === Number(value)) ?? levels[0];
}
