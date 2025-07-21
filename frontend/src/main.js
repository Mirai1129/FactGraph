import { createApp } from 'vue'
import './assets/service.css'
import App from './App.vue'
// % cd ~/dev/FactGraph/frontend
// % yarn install
// $ yarn run dev
createApp(App).mount('#app')

// 前端更新時，需要重新部署到 Firebase Hosting
// % cd ~/dev/FactGraph/frontend
// % yarn run build
// % firebase deploy --only hosting