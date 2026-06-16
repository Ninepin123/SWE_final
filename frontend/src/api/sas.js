// SAS 學生申請 — API 呼叫
// 對應後端 backend/app/modules/sas/router.py，路徑前綴 /api/sas
import http from './http'

export function apply(payload) {
  return http.post('/sas/applications', payload)
}

export function listMyApplications() {
  return http.get('/sas/applications/me')
}
