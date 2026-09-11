import { HttpErrorResponse, HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { delay, of, throwError } from 'rxjs';

import { API_CONFIG, DOMAIN_ENDPOINTS } from '../config/api.config';
import { Evidence, IsoControl, ManagedUser, SoaEntry, TreatmentPayload, TreatmentTask } from '../models/governance.models';

const DIGITAL_SCOPE = '8f4b8400-e29b-41d4-a716-446655440101';
const DATACENTER_SCOPE = '8f4b8400-e29b-41d4-a716-446655440102';
const members: ManagedUser[] = [
  { id: 'member-001', name: 'Camille Durand', email: 'camille.durand@opensmr.fr', role: 'RISK_OWNER', is_active: true, scope_ids: [DIGITAL_SCOPE, DATACENTER_SCOPE] },
  { id: 'member-002', name: 'Nadia Bernard', email: 'nadia.bernard@opensmr.fr', role: 'RSSI', is_active: true, scope_ids: [DIGITAL_SCOPE] },
  { id: 'member-003', name: 'Thomas Leroy', email: 'thomas.leroy@opensmr.fr', role: 'AUDITOR', is_active: true, scope_ids: [DIGITAL_SCOPE] },
];

const controls: IsoControl[] = Array.from({ length: 93 }, (_, index) => {
  const position = index + 1;
  const theme = position <= 37 ? 'ORGANIZATIONAL' : position <= 45 ? 'PEOPLE' : position <= 59 ? 'PHYSICAL' : 'TECHNOLOGICAL';
  const prefix = theme === 'ORGANIZATIONAL' ? 5 : theme === 'PEOPLE' ? 6 : theme === 'PHYSICAL' ? 7 : 8;
  const offset = theme === 'ORGANIZATIONAL' ? position : theme === 'PEOPLE' ? position - 37 : theme === 'PHYSICAL' ? position - 45 : position - 59;
  const titles: Record<number, string> = { 1: 'Politiques de sécurité de l’information', 2: 'Rôles et responsabilités liés à la sécurité', 6: 'Contacts avec les autorités', 23: 'Sécurité de l’information dans le cloud', 53: 'Protection des enregistrements', 68: 'Gestion des vulnérabilités techniques', 73: 'Sauvegarde des informations', 84: 'Développement sécurisé' };
  return { id: `control-${position.toString().padStart(3, '0')}`, code: `A.${prefix}.${offset}`, title: titles[position] ?? `Mesure de sécurité ${position}`, theme };
});

let treatments: TreatmentTask[] = [
  task('task-001', DIGITAL_SCOPE, 'risk-001', 'RSK-PAY-001', 68, 'member-001', 'Corriger les vulnérabilités exposées', '2026-09-05', 'IN_PROGRESS'),
  task('task-002', DIGITAL_SCOPE, 'risk-002', 'RSK-DAT-002', 53, 'member-002', 'Renforcer la journalisation des accès', '2026-09-18', 'TODO'),
  task('task-003', DIGITAL_SCOPE, 'risk-003', 'RSK-API-003', 23, 'member-001', 'Revoir les clauses de sécurité fournisseurs', '2026-09-22', 'TODO'),
  task('task-004', DATACENTER_SCOPE, 'risk-005', 'RSK-INF-005', 73, 'member-001', 'Tester le plan de restauration', '2026-09-01', 'COMPLETED'),
];

let soaEntries: SoaEntry[] = [DIGITAL_SCOPE, DATACENTER_SCOPE].flatMap((scopeId) => controls.map((control, index) => ({
  id: `${scopeId}-${control.id}`, scope_id: scopeId, control,
  is_applicable: index % 11 !== 0,
  justification: index % 11 === 0 ? 'Mesure non pertinente pour les activités couvertes par ce périmètre.' : 'Mesure retenue dans le plan de sécurité du périmètre.',
  implementation_status: index < 34 ? 'IMPLEMENTED' : index < 67 ? 'IN_PROGRESS' : 'NOT_IMPLEMENTED',
  updated_at: '2026-09-10T09:00:00Z', updated_by_name: 'Nadia Bernard',
}))) as SoaEntry[];

export const mockWorkspaceInterceptor: HttpInterceptorFn = (request, next) => {
  if (!API_CONFIG.useMocks) return next(request);
  const scopeId = request.params.get('scope_id');
  if (request.url === DOMAIN_ENDPOINTS.heatmap && request.method === 'GET') {
    const populated = scopeId === DATACENTER_SCOPE ? [[2, 5, 'risk-005']] : [[4, 5, 'risk-001'], [3, 5, 'risk-002'], [3, 4, 'risk-003'], [4, 3, 'risk-004']];
    const cells = Array.from({ length: 25 }, (_, index) => {
      const likelihood = Math.floor(index / 5) + 1;
      const impact = index % 5 + 1;
      const ids = populated.filter(([v, i]) => v === likelihood && i === impact).map(([, , id]) => String(id));
      return { likelihood, impact, risk_count: ids.length, risk_ids: ids };
    });
    return ok(cells);
  }
  if (request.url === DOMAIN_ENDPOINTS.treatments && request.method === 'GET') return ok(treatments.filter((item) => !scopeId || item.scope_id === scopeId));
  if (request.url === DOMAIN_ENDPOINTS.treatments && request.method === 'POST') {
    const payload = request.body as TreatmentPayload & { scope_id: string; risk_code?: string };
    const created = task(crypto.randomUUID(), payload.scope_id, payload.risk_id, payload.risk_code ?? 'RSK', Number(payload.iso_control_id.replace('control-', '')), payload.assignee_id, payload.title, payload.due_date, 'TODO', payload.description);
    treatments = [created, ...treatments];
    return ok(created, 201);
  }
  const treatmentMatch = request.url.match(/\/treatments\/([^/]+)\/(?:complete\/)?$/);
  if (treatmentMatch && request.method === 'PATCH') {
    const id = treatmentMatch[1];
    const current = treatments.find((item) => item.id === id);
    if (!current) return fail(404, 'Tâche introuvable.');
    const changes = request.url.endsWith('/complete/') ? { status: 'COMPLETED' as const, completed_at: new Date().toISOString() } : request.body as Partial<TreatmentTask>;
    const updated = { ...current, ...changes };
    treatments = treatments.map((item) => item.id === id ? updated : item);
    synchronizeSoa(updated);
    return ok(updated);
  }
  if (request.url === DOMAIN_ENDPOINTS.evidences && request.method === 'POST') {
    const form = request.body as FormData;
    const taskId = String(form.get('task_id'));
    const file = form.get('file') as File;
    const current = treatments.find((item) => item.id === taskId);
    if (!current) return fail(404, 'Tâche introuvable.');
    const evidence: Evidence = { id: crypto.randomUUID(), task_id: taskId, file_name: file.name, file_type: file.type, description: String(form.get('description') ?? ''), uploaded_by_name: 'Camille Durand', uploaded_at: new Date().toISOString() };
    treatments = treatments.map((item) => item.id === taskId ? { ...item, evidences: [...item.evidences, evidence] } : item);
    return ok(evidence, 201);
  }
  if (request.url === DOMAIN_ENDPOINTS.soa && request.method === 'GET') return ok(soaEntries.filter((item) => !scopeId || item.scope_id === scopeId));
  const soaId = collectionId(request.url, DOMAIN_ENDPOINTS.soa);
  if (soaId && request.method === 'PATCH') {
    const current = soaEntries.find((entry) => entry.id === soaId);
    if (!current) return fail(404, 'Entrée SoA introuvable.');
    const updated = { ...current, ...(request.body as Partial<SoaEntry>), updated_at: new Date().toISOString(), updated_by_name: 'Nadia Bernard' };
    soaEntries = soaEntries.map((entry) => entry.id === soaId ? updated : entry);
    return ok(updated);
  }
  if (/\/scopes\/[^/]+\/soa\/export\/$/.test(request.url.split('?')[0]) && request.method === 'GET') {
    const format = request.params.get('format') ?? new URL(request.url).searchParams.get('format') ?? 'csv';
    const content = format === 'pdf' ? 'OpenSMR - Déclaration d’applicabilité\nExport PDF simulé.' : 'controle;applicable;justification;implementation\nA.5.1;Oui;Mesure retenue;Mise en œuvre';
    return ok(new Blob([content], { type: format === 'pdf' ? 'application/pdf' : 'text/csv;charset=utf-8' }));
  }
  if (request.url === DOMAIN_ENDPOINTS.users && request.method === 'GET') return ok(members);
  if (request.url === DOMAIN_ENDPOINTS.users && request.method === 'POST') {
    const created = { ...(request.body as Omit<ManagedUser, 'id'>), id: crypto.randomUUID() };
    members.push(created);
    return ok(created, 201);
  }
  const userId = collectionId(request.url, DOMAIN_ENDPOINTS.users);
  if (userId && request.method === 'PATCH') {
    const index = members.findIndex((member) => member.id === userId);
    if (index < 0) return fail(404, 'Utilisateur introuvable.');
    members[index] = { ...members[index], ...(request.body as Partial<ManagedUser>) };
    return ok(members[index]);
  }
  return next(request);
};

function task(id: string, scopeId: string, riskId: string, riskCode: string, controlNumber: number, assigneeId: string, title: string, dueDate: string, status: TreatmentTask['status'], description = ''): TreatmentTask {
  const control = controls[Math.max(0, controlNumber - 1)] ?? controls[0];
  const assignee = members.find((member) => member.id === assigneeId)!;
  const evidences: Evidence[] = status === 'COMPLETED' ? [{ id: `evidence-${id}`, task_id: id, file_name: 'compte-rendu-controle.pdf', file_type: 'application/pdf', description: 'Compte rendu validé', uploaded_by_name: assignee.name, uploaded_at: '2026-09-02T10:00:00Z' }] : [];
  return { id, scope_id: scopeId, risk_id: riskId, risk_code: riskCode, iso_control_id: control.id, control_code: control.code, assignee_id: assigneeId, assignee_name: assignee.name, title, description, due_date: dueDate, status, completed_at: status === 'COMPLETED' ? '2026-09-02T10:00:00Z' : null, evidences };
}

function synchronizeSoa(taskItem: TreatmentTask): void {
  const implementation_status = taskItem.status === 'COMPLETED' && taskItem.evidences.length ? 'IMPLEMENTED' : 'IN_PROGRESS';
  soaEntries = soaEntries.map((entry) => entry.scope_id === taskItem.scope_id && entry.control.id === taskItem.iso_control_id ? { ...entry, implementation_status, updated_at: new Date().toISOString(), updated_by_name: 'Synchronisation automatique' } : entry);
}

function collectionId(url: string, base: string): string | null {
  const clean = url.split('?')[0];
  return clean.startsWith(base) ? clean.slice(base.length).replace(/\/$/, '') || null : null;
}

function ok<T>(body: T, status = 200) { return of(new HttpResponse({ body, status })).pipe(delay(API_CONFIG.mockDelayMs)); }
function fail(status: number, detail: string) { return throwError(() => new HttpErrorResponse({ status, error: { detail } })); }
