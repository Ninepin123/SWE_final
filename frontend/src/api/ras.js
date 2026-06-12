// RAS 審查與核發 — API 呼叫（負責人：填上姓名）
// 對應後端 backend/app/modules/ras/router.py，路徑前綴 /api/ras
import http from './http'

// 範例（骨架測試用，開發開始後可移除）：
export function ping() {
  return http.get('/ras/ping')
}

// TODO(RAS): 依 router.py 規劃的端點逐一補上，例如：
// export function listXxx(params) {
//   return http.get('/ras/xxx', { params })
// }
