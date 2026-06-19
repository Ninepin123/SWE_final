const STORAGE_KEY = 'nuksams_mock_state_v4'
const CURRENT_USER_KEY = 'nuksams_current_user_id'

export const ROLE_LABELS = {
  STUDENT: '學生',
  TEACHER: '教師',
  SPONSOR: '獎助單位人員',
  REVIEWER: '審查人員',
  ADMIN: '系統管理員',
}

export const APPLICATION_STATUS = {
  SUBMITTED: '已送出',
  UNDER_REVIEW: '審查中',
  NEEDS_SUPPLEMENT: '需補件',
  APPROVED: '已通過',
  REJECTED: '未通過',
}

export const RECOMMENDATION_STATUS = {
  PENDING: '等待填寫',
  SUBMITTED: '已送出',
  REMINDED: '已提醒',
}

export const SCHOLARSHIP_STATUS = {
  OPEN: '開放申請',
  CLOSED: '已截止',
  DRAFT: '草稿',
}

const reviewerId = 'u-reviewer'

function clone(value) {
  return JSON.parse(JSON.stringify(value))
}

function createId(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`
}

function todayIso() {
  return new Date().toISOString()
}

function getSeedState() {
  return {
    users: [
      {
        id: 'u-student',
        account: 'S1125501',
        name: '林映辰',
        email: 'student@nuk.edu.tw',
        role: 'STUDENT',
        unit: '資訊管理學系',
        status: 'ACTIVE',
        phone: '0912-345-678',
        createdAt: '2026-06-01T08:00:00+08:00',
      },
      {
        id: 'u-reviewer',
        account: 'R10001',
        name: '張雅婷',
        email: 'reviewer@nuk.edu.tw',
        role: 'REVIEWER',
        unit: '學務處生活輔導組',
        status: 'ACTIVE',
        phone: '07-5919000#1201',
        createdAt: '2026-06-01T08:10:00+08:00',
      },
      {
        id: 'u-admin',
        account: 'admin',
        name: '系統管理員',
        email: 'admin@nuk.edu.tw',
        role: 'ADMIN',
        unit: '資訊處',
        status: 'ACTIVE',
        phone: '07-5919000#1100',
        createdAt: '2026-06-01T08:20:00+08:00',
      },
      {
        id: 'u-recommender',
        account: 'teacher',
        name: '陳明哲',
        email: 'mchen@nuk.edu.tw',
        role: 'TEACHER',
        unit: '資訊管理學系',
        status: 'ACTIVE',
        phone: '07-5919000#3302',
        createdAt: '2026-06-01T08:30:00+08:00',
      },
      {
        id: 'u-student-2',
        account: 'S1125518',
        name: '王品安',
        email: 'pinan@nuk.edu.tw',
        role: 'STUDENT',
        unit: '亞太工商管理學系',
        status: 'ACTIVE',
        phone: '0922-111-888',
        createdAt: '2026-06-02T09:00:00+08:00',
      },
    ],
    profiles: {
      'u-student': {
        studentId: 'S1125501',
        name: '林映辰',
        department: '資訊管理學系',
        grade: '三年級',
        email: 'student@nuk.edu.tw',
        phone: '0912-345-678',
        address: '高雄市楠梓區大學南路700號',
        gpa: 3.82,
        credits: 112,
        familyStatus: '中低收入戶，需自付住宿與生活費',
        bankAccount: '808-123456789012',
        emergencyContact: '林先生 0910-000-111',
        updatedAt: '2026-06-12T12:00:00+08:00',
      },
      'u-student-2': {
        studentId: 'S1125518',
        name: '王品安',
        department: '亞太工商管理學系',
        grade: '二年級',
        email: 'pinan@nuk.edu.tw',
        phone: '0922-111-888',
        address: '高雄市左營區博愛路',
        gpa: 3.55,
        credits: 76,
        familyStatus: '一般戶',
        bankAccount: '812-987654321000',
        emergencyContact: '王小姐 0933-222-777',
        updatedAt: '2026-06-10T13:00:00+08:00',
      },
    },
    scholarships: [
      {
        id: 'sch-excellence',
        title: '高雄大學卓越學習獎學金',
        category: '校內獎學金',
        sponsor: '學務處',
        amount: 30000,
        quota: 12,
        usedQuota: 4,
        deadline: '2026-07-30',
        status: 'OPEN',
        tags: ['成績優良', '校內'],
        description: '鼓勵學生維持優良學習表現，並參與校內公共服務。',
        criteria: {
          minGpa: 3.5,
          departments: ['不限科系'],
          note: '前一學年操行成績需達 80 分以上。',
        },
        requiredDocs: ['成績單', '自傳與讀書計畫', '服務證明'],
        requireRecommendation: true,
      },
      {
        id: 'sch-relief',
        title: '資訊學院清寒助學金',
        category: '院級助學金',
        sponsor: '資訊學院',
        amount: 20000,
        quota: 8,
        usedQuota: 2,
        deadline: '2026-07-10',
        status: 'OPEN',
        tags: ['清寒', '資訊學院'],
        description: '提供資訊學院經濟弱勢學生生活與學習支持。',
        criteria: {
          minGpa: 2.8,
          departments: ['資訊管理學系', '資訊工程學系'],
          note: '需檢附家庭經濟狀況說明。',
        },
        requiredDocs: ['成績單', '戶籍謄本', '家庭經濟證明'],
        requireRecommendation: true,
      },
      {
        id: 'sch-industry',
        title: '企業培力獎助金',
        category: '企業贊助',
        sponsor: '南部科技產業聯盟',
        amount: 50000,
        quota: 5,
        usedQuota: 5,
        deadline: '2026-06-30',
        status: 'CLOSED',
        tags: ['企業', '實習'],
        description: '支持具產業實作潛力的學生，需提交作品集或專題成果。',
        criteria: {
          minGpa: 3.2,
          departments: ['不限科系'],
          note: '需附專題或作品連結。',
        },
        requiredDocs: ['成績單', '作品集', '履歷'],
        requireRecommendation: false,
      },
    ],
    applications: [
      {
        id: 'app-relief-001',
        scholarshipId: 'sch-relief',
        studentId: 'u-student',
        status: 'UNDER_REVIEW',
        submittedAt: '2026-06-14T10:20:00+08:00',
        updatedAt: '2026-06-15T09:00:00+08:00',
        form: {
          personal: {
            phone: '0912-345-678',
            address: '高雄市楠梓區大學南路700號',
          },
          academics: {
            gpa: 3.82,
            credits: 112,
            achievements: '完成資料視覺化專題，並擔任課程助教。',
          },
          finance: {
            familyStatus: '中低收入戶，需自付住宿與生活費',
            monthlyExpense: 9500,
          },
          statement: '希望能減輕家庭負擔，專注完成畢業專題與實習。',
          documents: ['成績單', '戶籍謄本', '家庭經濟證明'],
        },
        recommendationIds: ['rec-relief-001'],
        auditLogs: [
          {
            id: 'log-001',
            actorId: 'u-student',
            actorName: '林映辰',
            actorRole: '學生',
            action: '送出申請',
            fromStatus: null,
            toStatus: 'UNDER_REVIEW',
            result: '申請成立',
            comment: '學生完成申請表與推薦人資料。',
            createdAt: '2026-06-14T10:20:00+08:00',
          },
          {
            id: 'log-002',
            actorId: 'u-reviewer',
            actorName: '張雅婷',
            actorRole: '審查人員',
            action: '初步檢核',
            fromStatus: 'SUBMITTED',
            toStatus: 'UNDER_REVIEW',
            result: '進入審查',
            comment: '文件完整，等待推薦信送出。',
            createdAt: '2026-06-15T09:00:00+08:00',
          },
        ],
      },
      {
        id: 'app-industry-001',
        scholarshipId: 'sch-industry',
        studentId: 'u-student',
        status: 'NEEDS_SUPPLEMENT',
        submittedAt: '2026-06-08T15:35:00+08:00',
        updatedAt: '2026-06-16T11:10:00+08:00',
        form: {
          personal: {
            phone: '0912-345-678',
            address: '高雄市楠梓區大學南路700號',
          },
          academics: {
            gpa: 3.82,
            credits: 112,
            achievements: '專題作品：校園獎學金資料分析平台。',
          },
          finance: {
            familyStatus: '中低收入戶',
            monthlyExpense: 9500,
          },
          statement: '希望透過企業培力計畫銜接實習與研究。',
          documents: ['成績單', '履歷'],
        },
        recommendationIds: [],
        auditLogs: [
          {
            id: 'log-003',
            actorId: 'u-student',
            actorName: '林映辰',
            actorRole: '學生',
            action: '送出申請',
            fromStatus: null,
            toStatus: 'UNDER_REVIEW',
            result: '申請成立',
            comment: '學生完成申請。',
            createdAt: '2026-06-08T15:35:00+08:00',
          },
          {
            id: 'log-004',
            actorId: 'u-reviewer',
            actorName: '張雅婷',
            actorRole: '審查人員',
            action: '要求補件',
            fromStatus: 'UNDER_REVIEW',
            toStatus: 'NEEDS_SUPPLEMENT',
            result: '需補件',
            comment: '請補上完整作品集連結與服務證明。',
            createdAt: '2026-06-16T11:10:00+08:00',
          },
        ],
      },
    ],
    recommendations: [
      {
        id: 'rec-relief-001',
        applicationId: 'app-relief-001',
        studentId: 'u-student',
        recommenderUserId: 'u-recommender',
        recommenderName: '陳明哲',
        recommenderEmail: 'mchen@nuk.edu.tw',
        recommenderTitle: '資訊管理學系副教授',
        relationship: '導師',
        status: 'PENDING',
        inviteToken: 'INV-RELIEF-001',
        invitedAt: '2026-06-14T10:21:00+08:00',
        submittedAt: null,
        content: '',
      },
    ],
    notifications: [
      {
        id: 'noti-001',
        userId: 'u-student',
        type: 'success',
        title: '申請已送出',
        message: '資訊學院清寒助學金已建立申請，請追蹤推薦信狀態。',
        read: false,
        createdAt: '2026-06-14T10:21:00+08:00',
      },
      {
        id: 'noti-002',
        userId: 'u-student',
        type: 'warning',
        title: '補件通知',
        message: '企業培力獎助金需補上完整作品集連結與服務證明。',
        read: false,
        createdAt: '2026-06-16T11:10:00+08:00',
      },
      {
        id: 'noti-003',
        userId: 'u-recommender',
        type: 'info',
        title: '推薦信邀請',
        message: '林映辰邀請你為資訊學院清寒助學金撰寫推薦信。',
        read: false,
        createdAt: '2026-06-14T10:21:00+08:00',
      },
      {
        id: 'noti-004',
        userId: 'u-reviewer',
        type: 'info',
        title: '新申請案待審',
        message: '資訊學院清寒助學金有新的申請案等待審查。',
        read: true,
        createdAt: '2026-06-14T10:22:00+08:00',
      },
    ],
  }
}

function normalizeState(state) {
  const seed = getSeedState()
  return {
    users: Array.isArray(state?.users) ? state.users : seed.users,
    profiles: state?.profiles ?? seed.profiles,
    scholarships: Array.isArray(state?.scholarships) ? state.scholarships : seed.scholarships,
    applications: Array.isArray(state?.applications) ? state.applications : seed.applications,
    recommendations: Array.isArray(state?.recommendations)
      ? state.recommendations
      : seed.recommendations,
    notifications: Array.isArray(state?.notifications) ? state.notifications : seed.notifications,
  }
}

function getState() {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) {
    const seed = getSeedState()
    localStorage.setItem(STORAGE_KEY, JSON.stringify(seed))
    return seed
  }

  try {
    const state = normalizeState(JSON.parse(raw))
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    return state
  } catch {
    const seed = getSeedState()
    localStorage.setItem(STORAGE_KEY, JSON.stringify(seed))
    return seed
  }
}

function saveState(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

function delay(value, ms = 120) {
  return new Promise((resolve) => {
    window.setTimeout(() => resolve(clone(value)), ms)
  })
}

function getUserById(state, userId) {
  return state.users.find((user) => user.id === userId)
}

function hydrateApplication(state, application) {
  const scholarship = state.scholarships.find((item) => item.id === application.scholarshipId) ?? {
    id: application.scholarshipId,
    title: '已刪除獎學金',
    category: '已封存',
    sponsor: '-',
    amount: 0,
  }
  const student = getUserById(state, application.studentId)
  const profile = state.profiles[application.studentId]
  const recommendations = state.recommendations.filter((item) =>
    application.recommendationIds?.includes(item.id),
  )

  return {
    ...application,
    scholarship,
    student,
    profile,
    recommendations,
  }
}

function pushNotification(state, notification) {
  state.notifications.unshift({
    id: createId('noti'),
    read: false,
    createdAt: todayIso(),
    ...notification,
  })
}

function createAuditLog({ actor, action, fromStatus, toStatus, result, comment }) {
  return {
    id: createId('log'),
    actorId: actor.id,
    actorName: actor.name,
    actorRole: ROLE_LABELS[actor.role] ?? actor.role,
    action,
    fromStatus,
    toStatus,
    result,
    comment,
    createdAt: todayIso(),
  }
}

export function resetMockState() {
  const seed = getSeedState()
  localStorage.setItem(STORAGE_KEY, JSON.stringify(seed))
  localStorage.setItem(CURRENT_USER_KEY, 'u-student')
  localStorage.setItem('token', 'mock-token-u-student')
  return clone(seed)
}

export async function fetchMe() {
  const state = getState()
  const currentUserId = localStorage.getItem(CURRENT_USER_KEY) || 'u-student'
  const user = getUserById(state, currentUserId) ?? state.users[0]
  return delay(user)
}

export async function loginAs(role) {
  const state = getState()
  const user = state.users.find((item) => item.role === role && item.status === 'ACTIVE')
  if (!user) {
    throw new Error('找不到可登入的角色帳號')
  }
  localStorage.setItem(CURRENT_USER_KEY, user.id)
  localStorage.setItem('token', `mock-token-${user.id}`)
  return delay(user)
}

export async function logout() {
  localStorage.removeItem(CURRENT_USER_KEY)
  localStorage.removeItem('token')
  return delay(true)
}

export async function listUsers(params = {}) {
  const state = getState()
  const keyword = params.keyword?.trim().toLowerCase()
  const role = params.role
  const users = state.users.filter((user) => {
    const matchedKeyword =
      !keyword ||
      [user.account, user.name, user.email, user.unit].some((field) =>
        String(field ?? '').toLowerCase().includes(keyword),
      )
    const matchedRole = !role || user.role === role
    return matchedKeyword && matchedRole
  })
  return delay(users)
}

export async function createUser(data) {
  const state = getState()
  const exists = state.users.some((user) => user.account === data.account || user.email === data.email)
  if (exists) {
    throw new Error('帳號或 Email 已存在')
  }
  const user = {
    id: createId('user'),
    status: 'ACTIVE',
    createdAt: todayIso(),
    ...data,
  }
  state.users.unshift(user)
  if (user.role === 'STUDENT') {
    state.profiles[user.id] = {
      studentId: user.account,
      name: user.name,
      department: user.unit || '',
      grade: '',
      email: user.email,
      phone: user.phone || '',
      address: '',
      gpa: 0,
      credits: 0,
      familyStatus: '',
      bankAccount: '',
      emergencyContact: '',
      updatedAt: todayIso(),
    }
  }
  saveState(state)
  return delay(user)
}

export async function updateUser(userId, data) {
  const state = getState()
  const index = state.users.findIndex((user) => user.id === userId)
  if (index === -1) {
    throw new Error('找不到帳號')
  }
  state.users[index] = { ...state.users[index], ...data }
  if (state.profiles[userId]) {
    state.profiles[userId] = {
      ...state.profiles[userId],
      name: state.users[index].name,
      email: state.users[index].email,
      phone: state.users[index].phone,
      department: state.users[index].unit,
      updatedAt: todayIso(),
    }
  }
  saveState(state)
  return delay(state.users[index])
}

export async function deleteUser(userId) {
  const state = getState()
  state.users = state.users.filter((user) => user.id !== userId)
  delete state.profiles[userId]
  saveState(state)
  return delay(true)
}

export async function listScholarships(params = {}) {
  const state = getState()
  const keyword = params.keyword?.trim().toLowerCase()
  const category = params.category
  const status = params.status
  const items = state.scholarships.filter((scholarship) => {
    const matchedKeyword =
      !keyword ||
      [scholarship.title, scholarship.category, scholarship.sponsor, scholarship.description]
        .filter(Boolean)
        .some((field) => field.toLowerCase().includes(keyword))
    const matchedCategory = !category || scholarship.category === category
    const matchedStatus = !status || scholarship.status === status
    return matchedKeyword && matchedCategory && matchedStatus
  })
  return delay(items)
}

export async function getScholarship(scholarshipId) {
  const state = getState()
  const scholarship = state.scholarships.find((item) => item.id === scholarshipId)
  if (!scholarship) {
    throw new Error('找不到獎學金')
  }
  return delay(scholarship)
}

export async function createScholarship(data) {
  const state = getState()
  const scholarship = {
    id: createId('sch'),
    usedQuota: 0,
    status: 'OPEN',
    tags: [],
    criteria: {
      minGpa: 0,
      departments: ['不限科系'],
      note: '',
    },
    requiredDocs: [],
    requireRecommendation: false,
    ...data,
    amount: Number(data.amount || 0),
    quota: Number(data.quota || 0),
  }
  state.scholarships.unshift(scholarship)
  saveState(state)
  return delay(scholarship)
}

export async function updateScholarship(scholarshipId, data) {
  const state = getState()
  const index = state.scholarships.findIndex((item) => item.id === scholarshipId)
  if (index === -1) {
    throw new Error('找不到獎學金')
  }
  state.scholarships[index] = {
    ...state.scholarships[index],
    ...data,
    amount: Number(data.amount || state.scholarships[index].amount),
    quota: Number(data.quota || state.scholarships[index].quota),
  }
  saveState(state)
  return delay(state.scholarships[index])
}

export async function deleteScholarship(scholarshipId) {
  const state = getState()
  state.scholarships = state.scholarships.filter((item) => item.id !== scholarshipId)
  saveState(state)
  return delay(true)
}

export async function listAvailableScholarships(studentId) {
  const state = getState()
  const appliedScholarshipIds = new Set(
    state.applications
      .filter((application) => application.studentId === studentId)
      .map((application) => application.scholarshipId),
  )

  const items = state.scholarships.map((scholarship) => ({
    ...scholarship,
    alreadyApplied: appliedScholarshipIds.has(scholarship.id),
    seatsLeft: Math.max(Number(scholarship.quota) - Number(scholarship.usedQuota), 0),
  }))

  return delay(items)
}

export async function getProfile(userId) {
  const state = getState()
  const profile = state.profiles[userId]
  if (!profile) {
    throw new Error('找不到學生個人資料')
  }
  return delay(profile)
}

export async function updateProfile(userId, data) {
  const state = getState()
  if (!state.profiles[userId]) {
    throw new Error('找不到學生個人資料')
  }
  state.profiles[userId] = {
    ...state.profiles[userId],
    ...data,
    studentId: state.profiles[userId].studentId,
    name: state.profiles[userId].name,
    department: state.profiles[userId].department,
    updatedAt: todayIso(),
  }
  saveState(state)
  return delay(state.profiles[userId])
}

export async function listApplicationsByStudent(studentId) {
  const state = getState()
  const items = state.applications
    .filter((application) => application.studentId === studentId)
    .map((application) => hydrateApplication(state, application))
  return delay(items)
}

export async function getApplication(applicationId) {
  const state = getState()
  const application = state.applications.find((item) => item.id === applicationId)
  if (!application) {
    throw new Error('找不到申請案')
  }
  return delay(hydrateApplication(state, application))
}

export async function createApplication(studentId, payload) {
  const state = getState()
  const student = getUserById(state, studentId)
  const scholarship = state.scholarships.find((item) => item.id === payload.scholarshipId)
  if (!student || !scholarship) {
    throw new Error('申請資料不完整')
  }

  const alreadyApplied = state.applications.some(
    (application) =>
      application.studentId === studentId && application.scholarshipId === payload.scholarshipId,
  )
  if (alreadyApplied) {
    throw new Error('你已經申請過此獎學金，不能重複申請')
  }
  if (scholarship.status !== 'OPEN' || scholarship.usedQuota >= scholarship.quota) {
    throw new Error('此獎學金目前不可申請')
  }

  const appId = createId('app')
  const recommendationIds = []
  if (payload.recommender?.email) {
    let recommender = state.users.find(
      (user) => user.email?.toLowerCase() === payload.recommender.email.toLowerCase(),
    )
    if (!recommender) {
      recommender = {
        id: createId('user'),
        account: payload.recommender.email.split('@')[0],
        name: payload.recommender.name,
        email: payload.recommender.email,
        role: 'TEACHER',
        unit: payload.recommender.title || '校外推薦人',
        status: 'ACTIVE',
        phone: '',
        createdAt: todayIso(),
      }
      state.users.push(recommender)
    }

    const recommendation = {
      id: createId('rec'),
      applicationId: appId,
      studentId,
      recommenderUserId: recommender.id,
      recommenderName: payload.recommender.name,
      recommenderEmail: payload.recommender.email,
      recommenderTitle: payload.recommender.title,
      relationship: payload.recommender.relationship,
      status: 'PENDING',
      inviteToken: createId('INV'),
      invitedAt: todayIso(),
      submittedAt: null,
      content: '',
    }
    state.recommendations.unshift(recommendation)
    recommendationIds.push(recommendation.id)
    pushNotification(state, {
      userId: recommender.id,
      type: 'info',
      title: '推薦信邀請',
      message: `${student.name} 邀請你為「${scholarship.title}」填寫推薦內容。`,
    })
  }

  const application = {
    id: appId,
    scholarshipId: scholarship.id,
    studentId,
    status: 'UNDER_REVIEW',
    submittedAt: todayIso(),
    updatedAt: todayIso(),
    form: payload.form,
    recommendationIds,
    auditLogs: [
      createAuditLog({
        actor: student,
        action: '送出申請',
        fromStatus: null,
        toStatus: 'UNDER_REVIEW',
        result: '申請成立',
        comment: recommendationIds.length ? '申請已送出，推薦信邀請同步建立。' : '申請已送出。',
      }),
    ],
  }
  state.applications.unshift(application)
  const schIndex = state.scholarships.findIndex((item) => item.id === scholarship.id)
  state.scholarships[schIndex] = {
    ...state.scholarships[schIndex],
    usedQuota: Number(state.scholarships[schIndex].usedQuota) + 1,
  }

  pushNotification(state, {
    userId: studentId,
    type: 'success',
    title: '申請成功',
    message: `你已成功送出「${scholarship.title}」申請。`,
  })
  pushNotification(state, {
    userId: reviewerId,
    type: 'info',
    title: '新申請案待審',
    message: `${student.name} 送出「${scholarship.title}」申請。`,
  })

  saveState(state)
  return delay(hydrateApplication(state, application), 180)
}

export async function listReviewApplications(params = {}) {
  const state = getState()
  const status = params.status
  const keyword = params.keyword?.trim().toLowerCase()
  const items = state.applications
    .map((application) => hydrateApplication(state, application))
    .filter((application) => {
      const matchedStatus = !status || application.status === status
      const matchedKeyword =
        !keyword ||
        [application.student?.name, application.scholarship?.title, application.profile?.department]
          .filter(Boolean)
          .some((field) => field.toLowerCase().includes(keyword))
      return matchedStatus && matchedKeyword
    })
  return delay(items)
}

export async function submitReviewDecision(reviewerUserId, applicationId, decision) {
  const state = getState()
  const actor = getUserById(state, reviewerUserId)
  if (actor?.role !== 'REVIEWER') {
    throw new Error('只有審查人員可以審查申請案')
  }
  const application = state.applications.find((item) => item.id === applicationId)
  if (!application) {
    throw new Error('找不到申請案')
  }
  const fromStatus = application.status
  const toStatus = decision.result
  application.status = toStatus
  application.updatedAt = todayIso()
  application.auditLogs.unshift(
    createAuditLog({
      actor,
      action: '審查決議',
      fromStatus,
      toStatus,
      result: APPLICATION_STATUS[toStatus] ?? toStatus,
      comment: decision.comment,
    }),
  )
  const scholarship = state.scholarships.find((item) => item.id === application.scholarshipId)
  pushNotification(state, {
    userId: application.studentId,
    type: toStatus === 'APPROVED' ? 'success' : 'danger',
    title: '審查結果通知',
    message: `「${scholarship?.title ?? '獎學金'}」審查結果：${APPLICATION_STATUS[toStatus]}`,
  })
  saveState(state)
  return delay(hydrateApplication(state, application), 180)
}

export async function requestSupplement(reviewerUserId, applicationId, comment) {
  const state = getState()
  const actor = getUserById(state, reviewerUserId)
  if (actor?.role !== 'REVIEWER') {
    throw new Error('只有審查人員可以要求補件')
  }
  const application = state.applications.find((item) => item.id === applicationId)
  if (!application) {
    throw new Error('找不到申請案')
  }
  const fromStatus = application.status
  application.status = 'NEEDS_SUPPLEMENT'
  application.updatedAt = todayIso()
  application.auditLogs.unshift(
    createAuditLog({
      actor,
      action: '要求補件',
      fromStatus,
      toStatus: 'NEEDS_SUPPLEMENT',
      result: '需補件',
      comment,
    }),
  )
  const scholarship = state.scholarships.find((item) => item.id === application.scholarshipId)
  pushNotification(state, {
    userId: application.studentId,
    type: 'warning',
    title: '補件通知',
    message: `「${scholarship?.title ?? '獎學金'}」需要補件：${comment}`,
  })
  saveState(state)
  return delay(hydrateApplication(state, application), 180)
}

export async function listRecommendationRequests(recommenderUserId) {
  const state = getState()
  const items = state.recommendations
    .filter((item) => item.recommenderUserId === recommenderUserId)
    .map((request) => {
      const application = state.applications.find((item) => item.id === request.applicationId)
      return {
        ...request,
        application: application ? hydrateApplication(state, application) : null,
      }
    })
  return delay(items)
}

export async function submitRecommendation(recommenderUserId, requestId, content) {
  const state = getState()
  const actor = getUserById(state, recommenderUserId)
  const request = state.recommendations.find((item) => item.id === requestId)
  if (!request || request.recommenderUserId !== recommenderUserId) {
    throw new Error('找不到推薦邀請')
  }
  request.status = 'SUBMITTED'
  request.content = content
  request.submittedAt = todayIso()
  const application = state.applications.find((item) => item.id === request.applicationId)
  if (application) {
    application.updatedAt = todayIso()
    application.auditLogs.unshift(
      createAuditLog({
        actor,
        action: '推薦信送出',
        fromStatus: application.status,
        toStatus: application.status,
        result: '推薦信已完成',
        comment: `${request.recommenderName} 已送出推薦內容。`,
      }),
    )
    const scholarship = state.scholarships.find((item) => item.id === application.scholarshipId)
    pushNotification(state, {
      userId: application.studentId,
      type: 'success',
      title: '推薦信已送出',
      message: `${request.recommenderName} 已完成「${scholarship?.title ?? '獎學金'}」推薦信。`,
    })
    pushNotification(state, {
      userId: reviewerId,
      type: 'info',
      title: '推薦信完成',
      message: `${request.recommenderName} 已送出 ${scholarship?.title ?? '獎學金'} 的推薦信。`,
    })
  }
  saveState(state)
  return delay({
    ...request,
    application: application ? hydrateApplication(state, application) : null,
  })
}

export async function sendRecommendationReminder(studentId, requestId) {
  const state = getState()
  const student = getUserById(state, studentId)
  const request = state.recommendations.find((item) => item.id === requestId)
  if (!request || request.studentId !== studentId) {
    throw new Error('找不到推薦邀請')
  }
  request.status = request.status === 'SUBMITTED' ? 'SUBMITTED' : 'REMINDED'
  pushNotification(state, {
    userId: request.recommenderUserId,
    type: 'warning',
    title: '推薦信提醒',
    message: `${student?.name ?? '學生'} 提醒你完成推薦信。`,
  })
  saveState(state)
  return delay(request)
}

export async function listNotifications(userId) {
  const state = getState()
  const items = state.notifications.filter((notification) => notification.userId === userId)
  return delay(items)
}

export async function markNotificationRead(userId, notificationId) {
  const state = getState()
  const notification = state.notifications.find(
    (item) => item.id === notificationId && item.userId === userId,
  )
  if (notification) {
    notification.read = true
  }
  saveState(state)
  return delay(notification ?? null)
}

export async function getDashboardSummary(user) {
  const state = getState()
  const unread = state.notifications.filter((item) => item.userId === user.id && !item.read).length
  if (user.role === 'STUDENT') {
    const applications = state.applications.filter((item) => item.studentId === user.id)
    return delay({
      applications: applications.length,
      underReview: applications.filter((item) => item.status === 'UNDER_REVIEW').length,
      needsSupplement: applications.filter((item) => item.status === 'NEEDS_SUPPLEMENT').length,
      availableScholarships: state.scholarships.filter((item) => item.status === 'OPEN').length,
      unread,
    })
  }
  if (user.role === 'REVIEWER') {
    return delay({
      pending: state.applications.filter((item) =>
        ['UNDER_REVIEW', 'NEEDS_SUPPLEMENT'].includes(item.status),
      ).length,
      approved: state.applications.filter((item) => item.status === 'APPROVED').length,
      rejected: state.applications.filter((item) => item.status === 'REJECTED').length,
      unread,
    })
  }
  if (user.role === 'ADMIN') {
    return delay({
      users: state.users.length,
      scholarships: state.scholarships.length,
      openScholarships: state.scholarships.filter((item) => item.status === 'OPEN').length,
      unread,
    })
  }
  return delay({
    pendingRecommendations: state.recommendations.filter(
      (item) => item.recommenderUserId === user.id && item.status !== 'SUBMITTED',
    ).length,
    submittedRecommendations: state.recommendations.filter(
      (item) => item.recommenderUserId === user.id && item.status === 'SUBMITTED',
    ).length,
    unread,
  })
}
