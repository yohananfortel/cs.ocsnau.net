import { createRouter, createWebHistory } from 'vue-router'
import TheWelcome from '../components/TheWelcome.vue'
import LecturesView from '../components/LecturesView.vue'
import LectureView from '../components/LectureView.vue'
import AdminView from '../components/AdminView.vue'
import EditLectureView from '../components/EditLectureView.vue'
import { useAuthStore } from '@/stores/auth'
import Course from '@/components/course/Course.vue'
import ActionView from '@/components/course/action/ActionView.vue'
import knowlegeMap from '@/components/knowlegemap/knowlegeMap.vue'
import QuizGame from '@/components/course/action/QuizGame.vue'  
import DuneGame from '@/components/course/action/DuneGame.vue'




// ... ваші імпорти

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: TheWelcome },
    { path: '/course/:slug', name: 'course', component: Course, props: true },
    { path: '/action/:id', name: 'action', component: ActionView, props: true },
    { path: '/lectures/:slug', name: 'lectures', component: LecturesView, props: true },
    { path: '/knowledge-map', name: 'knowledge-map', component: knowlegeMap },  
    { path: '/quiz', name: 'quiz', component: QuizGame },
    { path: '/dune', name: 'dune', component: DuneGame},

    // ДОДАЙТЕ ЦЕЙ МАРШРУТ:
    { 
      path: '/login', 
      name: 'login', 
      component: () => import('../components/LoginView.vue') 
    },
    // АДМІН-ПАНЕЛЬ (приклад):
    // АДМІН-ПАНЕЛЬ:
    { path: '/admin', name: 'admin', component: AdminView, meta: { requiresAuth: true }},
    { path: '/edit-lecture/:slug', name: 'edit-lecture', component: EditLectureView, meta: { requiresAuth: true }, props: true}
  ],
})


router.beforeEach((to, from, next) => {
  // Викликаємо стор ВСЕРЕДИНІ функції
  const auth = useAuthStore()
  
  if (to.meta.requiresAuth && !auth.token) {
    next({ name: 'login' })
  } else {
    next()
  }
})



export default router