<script setup>
import axios from 'axios'
import { ref, onMounted, computed } from 'vue'
import flatpickr from 'flatpickr'
import 'flatpickr/dist/flatpickr.min.css'

// 狀態管理
const loading = ref(false)            // 是否正在載入狀態
const tabType = ref('link')
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

// 日期選擇器提示文字
const datePlaceholder = computed(() => {
  return tabType.value === 'question'
    ? '選擇事件詢問日期'
    : '選擇新聞發布日期'
})

// 初始化 flatpickr
onMounted(() => {
  flatpickr(document.querySelector('.date-input'), {
    dateFormat: 'Y/m/d',
    defaultDate: date.value,
    onChange: (_, dateStr) => (date.value = dateStr)
  })
})

// 切換分頁
function switchTab(type) {
  tabType.value = type
  input.value = ''
  date.value = ''
  result.value = defaultMsg
  knowledgeResult.value = defaultKnowledgeMsg
}

// 顯示錯誤訊息
function showError(msg) {
  errorMessage.value = msg
  clearTimeout(errorTimeout)
  errorTimeout = setTimeout(() => (errorMessage.value = ''), 2000)
}

// 驗證並呼叫 API
async function validateAndQuery() {
  isBouncing.value = true
  setTimeout(() => (isBouncing.value = false), 300)

  loading.value = true               // 開始載入狀態
  result.value = ''                  // 清空上次結果
  knowledgeResult.value = ''         // 清空對照知識

  if (!input.value) {
    loading.value = false
    return showError(
      tabType.value === 'link' ? '請輸入網址！' : '請輸入內容！'
    )
  }
  if (!date.value) {
    loading.value = false
    return showError('請選擇日期！')
  }
  if (
    tabType.value === 'link' &&
    !/^https?:\/\/.+\..+/.test(input.value)
  ) {
    loading.value = false
    return showError('請輸入正確的網址！')
  }

  // 準備 FormData
  const form = new FormData()
  form.append('file', new Blob([input.value], { type: 'text/plain' }), 'user.txt')
  form.append('date', date.value)

  // 選擇對應的路由
  const endpoint =
    tabType.value === 'question'
      ? '/api/answerer/query'
      : '/api/verifier/query'

  try {
    const { data } = await axios.post(endpoint, form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    // 填入結果
    if (tabType.value === 'question') {
      result.value = data.user_judge_result || '沒有取得答案'
      knowledgeResult.value = data.user_news_kg || '沒有查到知識內容'
    } else {
      result.value = data.judge_result || '沒有取得答案'
      knowledgeResult.value = data.news_kg || '沒有查到知識內容'
    }
    loading.value = false
  } catch (err) {
    console.error(err)
    showError('查詢失敗：' + (err.response?.data.detail || err.message))
    loading.value = false
  }
}
</script>

<template>
  <div
    class="error-message"
    :class="{ show: errorMessage }"
    v-if="errorMessage"
  >
    {{ errorMessage }}
  </div>

  <img src="/dog hend.png" class="dog-hand dog-hand-1" alt="dog hand" />
  <img src="/dog hend.png" class="dog-hand dog-hand-2" alt="dog hand" />
  <img src="/dog hend.png" class="dog-hand dog-hand-3" alt="dog hand" />

  <header class="header">
    <div class="header-left">
      <span class="header-icon" role="img" aria-label="camera">
        <img
          src="/camara icon.png"
          alt="camera icon"
          style="width:60px;height:60px;display:block;"
        />
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
        <a href="#">軟體服務</a>
        <a href="#">產品介紹</a>
        <a href="#">關於我們</a>
        <a href="#">聯絡我們</a>
      </nav>
    </div>
  </header>

  <img src="/dog icon.png" class="bg-dog" alt="dog icon" />

  <div class="container">
    <h1>來找芒狗偵探，幫你了解真相！</h1>

    <div class="tab-switch">
      <button
        class="tab-btn"
        :class="{ active: tabType === 'link' }"
        @click="switchTab('link')"
      >
        連結查詢
      </button>
      <button
        class="tab-btn"
        :class="{ active: tabType === 'writing' }"
        @click="switchTab('writing')"
      >
        文案查詢
      </button>
      <button
        class="tab-btn"
        :class="{ active: tabType === 'question' }"
        @click="switchTab('question')"
      >
        詢問模式
      </button>
    </div>

    <div class="input-area">
      <div class="input-group">
        <input
          type="text"
          v-model="input"
          :placeholder="
            tabType === 'link'
              ? '請輸入新聞連結...'
              : tabType === 'writing'
              ? '請輸入文案內容...'
              : '請輸入你的問題...'
          "
        />
        <input
          class="date-input"
          readonly
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
    <div
      class="answer-card"
      :class="{ default: !loading && result === defaultMsg }"
    >
      <template v-if="loading">
        <div class="loading-spinner"></div>
        <p class="loading-text">偵探調查中，請稍後...</p>
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
          <svg width="18" height="18" viewBox="0 0 18 18">
            <polygon points="4,7 9,12 14,7" fill="#fff" />
          </svg>
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
            <p class="loading-text">偵探調查中，請稍後...</p>
          </template>
          <template v-else>
            <div v-html="knowledgeResult"></div>
          </template>
        </div>
      </transition>
    </div>
  </div>
</template>

<style lang="scss" src="../assets/service.css"></style>
