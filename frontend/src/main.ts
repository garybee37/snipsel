import { mount } from 'svelte'
import './app.css'
import App from './App.svelte'
import { initSyncManager } from './lib/sync'

initSyncManager()

const app = mount(App, {
  target: document.getElementById('app')!,
})

export default app
