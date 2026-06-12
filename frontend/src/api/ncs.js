// NCS 通知與溝通 — API 呼叫（負責人：填上姓名）
// 對應後端 backend/app/modules/ncs/router.py，路徑前綴 /api/ncs
import http from './http'

// 範例（骨架測試用，開發開始後可移除）：
export function ping() {
  return http.get('/ncs/ping')
}

// TODO(NCS): 依 router.py 規劃的端點逐一補上，例如：
// export function listXxx(params) {
//   return http.get('/ncs/xxx', { params })
// }
