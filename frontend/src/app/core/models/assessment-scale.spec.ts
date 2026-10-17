import { DIC_LEVELS, IMPACT_LEVELS, LIKELIHOOD_LEVELS, assessmentLevel } from './assessment-scale';

describe('échelles d’évaluation', () => {
  it('couvre exactement les valeurs acceptées par les formulaires et Django', () => {
    expect(DIC_LEVELS.map((level) => level.value)).toEqual([1, 2, 3]);
    expect(LIKELIHOOD_LEVELS.map((level) => level.value)).toEqual([1, 2, 3, 4, 5]);
    expect(IMPACT_LEVELS.map((level) => level.value)).toEqual([1, 2, 3, 4, 5]);
  });

  it('associe une explication au niveau sélectionné dans un contrôle HTML', () => {
    expect(assessmentLevel(LIKELIHOOD_LEVELS, '4')).toMatchObject({ label: 'Très probable' });
    expect(assessmentLevel(IMPACT_LEVELS, 5).description).toContain('service essentiel');
  });
});
