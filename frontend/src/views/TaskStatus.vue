<!-- frontend/src/views/TaskStatus.vue -->
<template>
  <!-- 錯誤訊息提示 -->
  <div class="error-message" v-if="errorMessage" :class="{ show: errorMessage }">
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
    <h1>查詢結果</h1>

    <!-- 分頁切換 -->
    <div class="tab-switch">
      <button
        class="tab-btn"
        :class="{ active: tabType === 'writing' }"
        @click="tabType = 'writing'"
      >
        文案查詢
      </button>
      <button
        class="tab-btn"
        :class="{ active: tabType === 'question' }"
        @click="tabType = 'question'"
      >
        詢問模式
      </button>
    </div>

    <!-- 判斷結果區塊 -->
    <div class="answer-card" :class="{ default: !loading && currentResult === defaultMsg }">
      <template v-if="loading">
        <div class="loading-spinner"></div>
        <p class="loading-text">偵探調查中… 請稍候</p>
      </template>
      <template v-else>
        <div v-html="currentResult"></div>
      </template>
    </div>

    <!-- 對照知識區塊 -->
    <div class="knowledge-wrapper">
      <button class="collapse-btn" @click="knowledgeCollapsed = !knowledgeCollapsed">
        {{ knowledgeCollapsed ? '展開對照知識' : '收起對照知識' }}
        <span class="triangle" :class="{ rotated: !knowledgeCollapsed }">…</span>
      </button>
      <transition name="fade">
        <div
          class="knowledge-card"
          :class="{ default: !loading && currentKnowledge === defaultKnowledgeMsg }"
          v-show="loading || !knowledgeCollapsed"
        >
          <template v-if="loading">
            <div class="loading-spinner"></div>
            <p class="loading-text">偵探調查中… 請稍候</p>
          </template>
          <template v-else>
            <div v-html="currentKnowledge"></div>
          </template>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute }                from 'vue-router'
import { db }                      from '../firebase'
import { doc, onSnapshot }         from 'firebase/firestore'

// 取路由上的 jobId
const route  = useRoute()
const jobId  = route.params.id

// Tab、Loading、折疊、錯誤訊息
const tabType            = ref('writing')
const loading            = ref(true)
const knowledgeCollapsed = ref(true)
const errorMessage       = ref('')
function showError(msg) {
  errorMessage.value = msg
}

// 原始預設文字
const defaultMsg          = '這裡會顯示結果。'
const defaultKnowledgeMsg = '這裡會顯示對照知識。'

// Firestore 的四個欄位
const answerWriting     = ref(defaultMsg)
const knowledgeWriting  = ref(defaultKnowledgeMsg)
const answerQuestion    = ref(defaultMsg)
const knowledgeQuestion = ref(defaultKnowledgeMsg)

// 計算目前要呈現哪個欄位
const currentResult = computed(() =>
  tabType.value === 'writing' ? answerWriting.value : answerQuestion.value
)
const currentKnowledge = computed(() =>
  tabType.value === 'writing' ? knowledgeWriting.value : knowledgeQuestion.value
)

// 一掛載就訂閱 Firestore
onMounted(() => {
  const docRef = doc(db, 'url-results', jobId)
  onSnapshot(
    docRef,
    snap => {
      if (!snap.exists()) {
        loading.value = false
        return
      }
      const data = snap.data()

      // 依照 mode 切分頁
      if (data.mode === 'writing' || data.mode === 'question') {
        tabType.value = data.mode
      }

      // 失敗時顯示通用錯誤
      if (data.status === 'FAILED') {
        loading.value = false
        showError('任務執行失敗，請稍後重試')
        return
      }

      // 還在跑
      if (data.status !== 'DONE') {
        loading.value = true
        return
      }

      // 完成：把結果寫進各自欄位
      loading.value = false
      answerWriting.value     = data.writingAnswer     || defaultMsg
      knowledgeWriting.value  = data.writingKnowledge  || defaultKnowledgeMsg
      answerQuestion.value    = data.questionAnswer    || defaultMsg
      knowledgeQuestion.value = data.questionKnowledge || defaultKnowledgeMsg
    },
    err => {
      console.error('Firestore 監聽失敗：', err)
      loading.value = false
      showError('無法連線到 Firestore')
    }
  )
})
</script>

<style scoped>
@import '../assets/service.css';

.container {
  padding: 1rem;
}
.tab-switch {
  margin-bottom: 1rem;
}
</style>
