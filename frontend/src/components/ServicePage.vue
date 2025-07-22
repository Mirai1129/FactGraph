<!-- frontend/src/components/ServicePage.vue -->
<template>
  <div class="error-message" :class="{ show: errorMessage }" v-if="errorMessage">
    {{ errorMessage }}
  </div>

  <!-- 裝飾圖案 -->
  <img src="/dog hend.png" class="dog-hand dog-hand-1" alt="dog hand" />
  <img src="/dog hend.png" class="dog-hand dog-hand-2" alt="dog hand" />
  <img src="/dog hend.png" class="dog-hand dog-hand-3" alt="dog hand" />

  <!-- Header -->
  <header class="header">
    <div class="header-left">
      <span class="header-icon" role="img" aria-label="camera">
        <img src="/camara icon.png" alt="camera icon" style="width:60px;height:60px;display:block;" />
      </span>
      <span class="header-title">圖破謠言，新聞真偽辨識AI</span>
    </div>
    <div class="header-right">
      <button class="menu-btn" @click="$refs.menu.classList.toggle('show')">
        <span class="menu-bar"></span>
        <span class="menu-bar"></span>
        <span class="menu-bar"></span>
      </button>
      <nav class="menu-dropdown" ref="menu">
        <a href="#">首頁</a>
        <a href="#">服務介紹</a>
        <a href="#">關於我們</a>
      </nav>
    </div>
  </header>

  <img src="/dog icon.png" class="bg-dog" alt="dog icon" />

  <!-- 主體容器 -->
  <div class="container">
    <h1>來找芒狗偵探，幫你了解真相！</h1>

    <!-- 分頁切換 -->
    <div class="tab-switch">
      <button class="tab-btn" :class="{ active: tabType === 'writing' }" @click="switchTab('writing')">
        文案查詢
      </button>
      <button class="tab-btn" :class="{ active: tabType === 'question' }" @click="switchTab('question')">
        詢問模式
      </button>
    </div>

    <!-- 輸入區域 -->
    <div class="input-area">
      <div class="input-group">
        <input
          type="text"
          v-model="input"
          :placeholder="tabType === 'writing' ? '請輸入文案內容...' : '請輸入你的問題...'"
        />
        <input
          class="date-input"
          inputmode="none"
          :placeholder="datePlaceholder"
          style="background:#fff8f0; cursor:pointer;"
        />
        <button
          id="query-btn"
          :class="{ bounce: isBouncing }"
          @click="validateAndQuery"
        >
          開始查核
        </button>
      </div>
    </div>

    <!-- 查核結果區塊 -->
    <div class="answer-card" :class="{ default: !loading && result === defaultMsg }">
      <template v-if="loading">
        <div class="loading-spinner"></div>
        <p class="loading-text">調查中… 請等候30~60秒…</p>
      </template>
      <template v-else>
        <div v-html="result"></div>
      </template>
    </div>

    <!-- 對照知識區塊 -->
    <div class="knowledge-wrapper">
      <button class="collapse-btn" @click="knowledgeCollapsed = !knowledgeCollapsed">
        {{ knowledgeCollapsed ? '展開對照知識' : '收起對照知識' }}
        <span class="triangle" :class="{ rotated: !knowledgeCollapsed }">
          <svg width="18" height="18" viewBox="0 0 18 18"><polygon points="4,7 9,12 14,7" fill="#fff" /></svg>
        </span>
      </button>
      <transition name="fade">
        <div
          class="knowledge-card"
          :class="{ default: !loading && knowledgeResult === defaultKnowledgeMsg }"
          v-show="loading || !knowledgeCollapsed"
        >
          <template v-if="loading">
            <div class="loading-spinner"></div>
            <p class="loading-text">調查中… 請等候30~60秒…</p>
          </template>
          <template v-else>
            <div v-html="knowledgeResult"></div>
          </template>
        </div>
      </transition>
    </div>
  </div>

  <!-- 臨時網址彈窗 -->
  <transition name="fade">
    <div v-if="showUrlModal" class="modal-overlay">
      <div class="modal-box">
        <h3>臨時查詢網址</h3>
        <p class="url-text" @click="copyUrl" title="點擊複製">{{ tempUrl }}</p>
        <small>稍後可由此網址查看調查結果</small>
        <button class="modal-ok" @click="showUrlModal = false">確定</button>
      </div>
    </div>
  </transition>
</template>

<script setup>
import axios from 'axios'
import { ref, onMounted, computed } from 'vue'
import flatpickr from 'flatpickr'
import 'flatpickr/dist/flatpickr.min.css'

// 後端 API 根網址（如需跨域部署，可填入 https://your-domain.com）
const BASE_URL = ''

// -------------------------
// 狀態管理
// -------------------------
const loading = ref(false)
const tabType = ref('writing')
const input = ref('')
const date = ref('')
const defaultMsg = '這裡會顯示結果。'
const defaultKnowledgeMsg = '這裡會顯示對照知識。'
const result = ref(defaultMsg)
const knowledgeResult = ref(defaultKnowledgeMsg)
const errorMessage = ref('')
const isBouncing = ref(false)
const knowledgeCollapsed = ref(true)
let errorTimeout = null

// 臨時網址 & 複製功能
const showUrlModal = ref(false)
const tempUrl      = ref('')

function copyUrl() {
  navigator.clipboard.writeText(tempUrl.value)
    .then(() => alert('已複製臨時網址'))
    .catch(() => alert('複製失敗，請手動複製'))
}

// 日期選擇器提示文字
const datePlaceholder = computed(() =>
  tabType.value === 'question' ? '選擇事件詢問日期' : '選擇新聞發布日期'
)

// 初始化 flatpickr
onMounted(() => {
  flatpickr(document.querySelector('.date-input'), {
    dateFormat: 'Y/m/d',
    defaultDate: date.value,
    clickOpens: true,
    allowInput: false,
    disableMobile: true,
    onChange: (_, dateStr) => (date.value = dateStr)
  })
})

// 分頁切換
function switchTab (type) {
  tabType.value = type
  input.value = ''
  date.value = ''
  result.value = defaultMsg
  knowledgeResult.value = defaultKnowledgeMsg
}

// 顯示錯誤
function showError (msg) {
  errorMessage.value = msg
  clearTimeout(errorTimeout)
  errorTimeout = setTimeout(() => (errorMessage.value = ''), 2000)
}

// 驗證並呼叫 API
async function validateAndQuery () {
  isBouncing.value = true
  setTimeout(() => (isBouncing.value = false), 300)

  if (!input.value) {
    return showError(tabType.value === 'writing' ? '請輸入內容！' : '請輸入你的問題！')
  }
  if (!date.value) {
    return showError('請選擇日期！')
  }

  loading.value = true
  result.value = ''
  knowledgeResult.value = ''

  // —— 1. 呼叫 /api/tasks，帶入 url、mode、date —— 
  try {
    const { data: task } = await axios.post(
      `${BASE_URL}/api/tasks`,
      {
        url: input.value,
        mode: tabType.value,     // "writing" 或 "question"
        date: date.value         // "YYYY/MM/DD"
      }
    )
    tempUrl.value    = `${window.location.origin}/tasks/${task.id}`
    showUrlModal.value = true
  } catch (e) {
    console.error('建立臨時任務失敗', e)
    showError('無法建立查詢任務')
    loading.value = false
    return
  }

  // —— 2. 原有上傳 form & 查詢流程 —— 
  const form = new FormData()
  form.append('file', new Blob([input.value], { type: 'text/plain' }), 'user.txt')
  form.append('date', date.value)

  const endpoint =
    tabType.value === 'question' ? '/api/answerer/query' : '/api/verifier/query'

  try {
    const { data } = await axios.post(`${BASE_URL}${endpoint}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (tabType.value === 'question') {
      result.value = data.user_judge_result || '沒有取得答案'
      knowledgeResult.value = data.user_news_kg || '沒有查到知識內容'
    } else {
      result.value = data.judge_result || '沒有取得答案'
      knowledgeResult.value = data.news_kg || '沒有查到知識內容'
    }
  } catch (err) {
    console.error(err)
    showError('查詢失敗：' + (err.response?.data.detail || err.message))
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" src="../assets/service.css"></style>

<style scoped>
.date-input {
  -webkit-appearance: none;
  appearance: none;
  border-radius: 12px !important;
}
.date-input::placeholder {
  color: #666;
  opacity: 1;
}

/* 彈窗遮罩 */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

/* 彈窗內容 */
.modal-box {
  background: #fff;
  padding: 1.5rem;
  border-radius: 0.5rem;
  width: 90%;
  max-width: 360px;
  text-align: center;
  box-shadow: 0 2px 10px rgba(0,0,0,0.2);
}

.url-text {
  word-break: break-all;
  background: #f7f7f7;
  padding: 0.5rem;
  border-radius: 0.25rem;
  margin: 0.5rem 0;
  cursor: pointer;
}

.modal-ok {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  background: #409eff;
  color: #fff;
  cursor: pointer;
}

/* 淡入淡出動畫 */
.fade-enter-active, .fade-leave-active {
  transition: opacity .2s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
