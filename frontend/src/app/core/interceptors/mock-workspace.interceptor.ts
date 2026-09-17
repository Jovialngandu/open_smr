import { HttpErrorResponse, HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { delay, of, throwError } from 'rxjs';

import { API_CONFIG, DOMAIN_ENDPOINTS } from '../config/api.config';
import { createMockId } from '../utils/mock-id';
import { Evidence, IsoControl, ManagedUser, SoaEntry, SoaVersion, TreatmentTask } from '../models/governance.models';

const DIGITAL_SCOPE = '8f4b8400-e29b-41d4-a716-446655440101';
const DATACENTER_SCOPE = '8f4b8400-e29b-41d4-a716-446655440102';
const members: ManagedUser[] = [
  { id: '1', role_assignment_id: 'role-001', name: 'Camille Durand', email: 'camille.durand@opensmr.fr', role: 'RISK_OWNER', is_active: true, scope_ids: [DIGITAL_SCOPE, DATACENTER_SCOPE] },
  { id: '2', role_assignment_id: 'role-002', name: 'Nadia Bernard', email: 'nadia.bernard@opensmr.fr', role: 'RSSI', is_active: true, scope_ids: [DIGITAL_SCOPE] },
  { id: '3', role_assignment_id: 'role-003', name: 'Thomas Leroy', email: 'thomas.leroy@opensmr.fr', role: 'AUDITOR', is_active: true, scope_ids: [DIGITAL_SCOPE] },
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
  task('task-001', DIGITAL_SCOPE, 'risk-001', 'RSK-PAY-001', 68, '1', 'Corriger les vulnérabilités exposées', '2026-09-05', 'IN_PROGRESS'),
  task('task-002', DIGITAL_SCOPE, 'risk-002', 'RSK-DAT-002', 53, '2', 'Renforcer la journalisation des accès', '2026-09-18', 'TODO'),
  task('task-003', DIGITAL_SCOPE, 'risk-003', 'RSK-API-003', 23, '1', 'Revoir les clauses de sécurité fournisseurs', '2026-09-22', 'TODO'),
  task('task-004', DATACENTER_SCOPE, 'risk-005', 'RSK-INF-005', 73, '1', 'Tester le plan de restauration', '2026-09-01', 'COMPLETED'),
];

let soaEntries: SoaEntry[] = [DIGITAL_SCOPE, DATACENTER_SCOPE].flatMap((scopeId) => controls.map((control, index) => ({
  id: `${scopeId}-${control.id}`, scope_id: scopeId, iso_control: control,
  is_applicable: index % 11 !== 0,
  justification: index % 11 === 0 ? 'Mesure non pertinente pour les activités couvertes par ce périmètre.' : 'Mesure retenue dans le plan de sécurité du périmètre.',
  implementation_status: index < 34 ? 'IMPLEMENTED' : index < 67 ? 'IN_PROGRESS' : 'NOT_IMPLEMENTED',
  updated_at: '2026-09-10T09:00:00Z', updated_by_name: 'Nadia Bernard',
}))) as SoaEntry[];

let soaVersions: SoaVersion[] = [
  { id: 'version-001', scope_id: DIGITAL_SCOPE, version_number: 'v1.0-2026', title: 'État initial du SMSI', status: 'APPROVED', created_at: '2026-08-20T10:00:00Z', approved_by_name: 'Nadia Bernard' },
  { id: 'version-002', scope_id: DIGITAL_SCOPE, version_number: 'v1.1-2026', title: 'Revue de septembre', status: 'DRAFT', created_at: '2026-09-10T09:00:00Z', approved_by_name: null },
];

export const mockWorkspaceInterceptor: HttpInterceptorFn = (request, next) => {
  if (!API_CONFIG.useMocks) return next(request);
  const scopeId = request.params.get('scope_id');
  const dashboardMatch = request.url.match(/\/scopes\/([^/]+)\/dashboard\/$/);
  if (dashboardMatch && request.method === 'GET') {
    const isDatacenter = dashboardMatch[1] === DATACENTER_SCOPE;
    return ok({ risks_by_level: { high: isDatacenter ? 0 : 2, medium: isDatacenter ? 1 : 2, low: 0 }, soa_completion: { total_applicable: 84, implemented: isDatacenter ? 31 : 30, percentage: isDatacenter ? 36.9 : 35.71 }, overdue_tasks_count: isDatacenter ? 0 : 1 });
  }
  const membersMatch = request.url.match(/\/organizations\/([^/]+)\/members\/$/);
  if (membersMatch && request.method === 'GET') return ok(members.map(toBackendMember));
  if (membersMatch && request.method === 'POST') {
    const body = request.body as { user_id: number; role: ManagedUser['role'] };
    const existing = members.find((member) => member.id === String(body.user_id));
    if (!existing) return fail(400, "Ce compte utilisateur n'existe pas.");
    existing.role = body.role;
    existing.is_active = true;
    return ok(toBackendMember(existing));
  }
  const memberStatusMatch = request.url.match(/\/organizations\/([^/]+)\/members\/([^/]+)\/toggle-status\/$/);
  if (memberStatusMatch && request.method === 'PATCH') {
    const member = members.find((item) => item.role_assignment_id === memberStatusMatch[2]);
    if (!member) return fail(404, 'Affectation introuvable.');
    member.is_active = Boolean((request.body as { is_active: boolean }).is_active);
    return ok(toBackendMember(member));
  }
  const scopeAccessRemovalMatch = request.url.match(/\/scopes\/([^/]+)\/access\/remove\/$/);
  if (scopeAccessRemovalMatch && request.method === 'POST') {
    const body = request.body as { user_id: number };
    const member = members.find((item) => item.id === String(body.user_id));
    if (!member) return fail(400, 'Utilisateur introuvable.');
    member.scope_ids = member.scope_ids.filter((id) => id !== scopeAccessRemovalMatch[1]);
    return ok({ detail: 'Accès retiré avec succès.' });
  }
  const scopeAccessMatch = request.url.match(/\/scopes\/([^/]+)\/access\/$/);
  if (scopeAccessMatch && request.method === 'GET') {
    return ok(members.filter((member) => member.scope_ids.includes(scopeAccessMatch[1])).map((member) => toBackendScopeAccess(member, scopeAccessMatch[1])));
  }
  if (scopeAccessMatch && request.method === 'POST') {
    const body = request.body as { user_id: number };
    const member = members.find((item) => item.id === String(body.user_id));
    if (!member) return fail(400, 'Utilisateur introuvable.');
    member.scope_ids = [...new Set([...member.scope_ids, scopeAccessMatch[1]])];
    return ok(toBackendScopeAccess(member, scopeAccessMatch[1]), 201);
  }
  if (request.url === DOMAIN_ENDPOINTS.heatmap && request.method === 'GET') {
    const populated = scopeId === DATACENTER_SCOPE ? [[2, 5, 'risk-005']] : [[4, 5, 'risk-001'], [3, 5, 'risk-002'], [3, 4, 'risk-003'], [4, 3, 'risk-004']];
    const cells = Array.from({ length: 25 }, (_, index) => {
      const likelihood = Math.floor(index / 5) + 1;
      const impact = index % 5 + 1;
      const ids = populated.filter(([v, i]) => v === likelihood && i === impact).map(([, , id]) => String(id));
      return { likelihood, impact, risk_count: ids.length, risk_ids: ids };
    });
    return ok({ scope_id: scopeId ?? '', total_risks: cells.reduce((sum, cell) => sum + cell.risk_count, 0), matrix: cells.map((cell) => ({ likelihood: cell.likelihood, impact: cell.impact, score: cell.likelihood * cell.impact, count: cell.risk_count })) });
  }
  if (request.url === DOMAIN_ENDPOINTS.treatments && request.method === 'GET') return ok(treatments.filter((item) => !scopeId || item.scope_id === scopeId).map(toBackendTask));
  if (request.url === DOMAIN_ENDPOINTS.treatments && request.method === 'POST') {
    const payload = request.body as { risk: string; iso_control: string; assignee: string; title: string; description: string; due_date: string };
    const created = task(createMockId('task'), request.params.get('scope_id') ?? DIGITAL_SCOPE, payload.risk, request.params.get('risk_code') ?? 'RSK', Number(payload.iso_control.replace('control-', '')), payload.assignee, payload.title, payload.due_date, 'TODO', payload.description);
    treatments = [created, ...treatments];
    return ok(toBackendTask(created), 201);
  }
  const treatmentMatch = request.url.match(/\/treatments\/tasks\/([^/]+)\/(?:status\/)?$/);
  if (treatmentMatch && request.method === 'PATCH') {
    const id = treatmentMatch[1];
    const current = treatments.find((item) => item.id === id);
    if (!current) return fail(404, 'Tâche introuvable.');
    const requested = request.body as Partial<TreatmentTask>;
    const changes = requested.status === 'COMPLETED' ? { ...requested, completed_at: new Date().toISOString() } : requested;
    const updated = { ...current, ...changes };
    treatments = treatments.map((item) => item.id === id ? updated : item);
    synchronizeSoa(updated);
    return ok(toBackendTask(updated));
  }
  if (request.url === DOMAIN_ENDPOINTS.evidences && request.method === 'POST') {
    const form = request.body as FormData;
    const taskId = String(form.get('task_id'));
    const file = form.get('file_path') as File;
    const current = treatments.find((item) => item.id === taskId);
    if (!current) return fail(404, 'Tâche introuvable.');
    const evidence: Evidence = { id: createMockId('evidence'), task_id: taskId, file_name: file.name, file_type: file.type, description: String(form.get('description') ?? ''), uploaded_by_name: 'Camille Durand', uploaded_at: new Date().toISOString() };
    treatments = treatments.map((item) => item.id === taskId ? { ...item, evidences: [...item.evidences, evidence] } : item);
    return ok(toBackendEvidence(evidence), 201);
  }
  if (request.url === DOMAIN_ENDPOINTS.soaVersions && request.method === 'GET') return ok(soaVersions.filter((item) => !scopeId || item.scope_id === scopeId));
  if (request.url === DOMAIN_ENDPOINTS.soaVersions && request.method === 'POST') {
    const body = request.body as { scope_id: string; title: string };
    const created: SoaVersion = { id: createMockId('soa-version'), scope_id: body.scope_id, version_number: `v1.${soaVersions.filter((item) => item.scope_id === body.scope_id).length + 1}-2026`, title: body.title, status: 'DRAFT', created_at: new Date().toISOString(), approved_by_name: null };
    soaVersions = [created, ...soaVersions];
    return ok(created, 201);
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
    const created = { ...(request.body as Omit<ManagedUser, 'id'>), id: createMockId('user') };
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
  soaEntries = soaEntries.map((entry) => entry.scope_id === taskItem.scope_id && entry.iso_control.id === taskItem.iso_control_id ? { ...entry, implementation_status, updated_at: new Date().toISOString(), updated_by_name: 'Synchronisation automatique' } : entry);
}

function toBackendTask(item: TreatmentTask) {
  return {
    id: item.id,
    title: item.title,
    description: item.description,
    status: item.status,
    risk: item.risk_id,
    risk_code: item.risk_code,
    iso_control: item.iso_control_id,
    iso_control_code: item.control_code,
    assignee: item.assignee_id || null,
    assignee_email: members.find((member) => member.id === item.assignee_id)?.email ?? null,
    due_date: item.due_date || null,
    completed_at: item.completed_at,
    evidences: item.evidences.map(toBackendEvidence),
    created_at: '2026-09-01T08:00:00Z',
    updated_at: new Date().toISOString(),
  };
}

function toBackendEvidence(item: Evidence) {
  return {
    id: item.id,
    task: item.task_id,
    uploaded_by: item.uploaded_by_name,
    uploaded_by_email: item.uploaded_by_name,
    file_path: item.download_url ?? `/media/evidences/${item.file_name}`,
    description: item.description,
    created_at: item.uploaded_at,
  };
}

function toBackendMember(member: ManagedUser) {
  const [firstName, ...lastName] = member.name.split(' ');
  return {
    id: member.role_assignment_id,
    user: { id: Number(member.id), username: member.email.split('@')[0], email: member.email, first_name: firstName, last_name: lastName.join(' ') },
    role: member.role,
    is_active: member.is_active,
    joined_at: '2026-09-01T08:00:00Z',
  };
}

function toBackendScopeAccess(member: ManagedUser, scopeId: string) {
  const [firstName, ...lastName] = member.name.split(' ');
  return { id: `access-${scopeId}-${member.id}`, scope: scopeId, user_organization_role: member.role_assignment_id, user: { id: Number(member.id), email: member.email, first_name: firstName, last_name: lastName.join(' ') }, granted_by: 2, granted_at: '2026-09-01T08:00:00Z' };
}

function collectionId(url: string, base: string): string | null {
  const clean = url.split('?')[0];
  return clean.startsWith(base) ? clean.slice(base.length).replace(/\/$/, '') || null : null;
}

function ok<T>(body: T, status = 200) { return of(new HttpResponse({ body, status })).pipe(delay(API_CONFIG.mockDelayMs)); }
function fail(status: number, detail: string) { return throwError(() => new HttpErrorResponse({ status, error: { detail } })); }
