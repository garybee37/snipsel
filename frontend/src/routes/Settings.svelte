<script lang="ts">
  import { api } from '../lib/api';
  import { currentUser } from '../lib/session';
  import { currentView } from '../lib/stores';

  async function logout() {
    await api.logout();
    currentUser.set(null);
    currentView.set({ type: 'loading' });
  }
</script>

<div class="space-y-3">
  <h2 class="text-lg font-semibold">Settings</h2>

  <div class="rounded-lg border bg-white p-3 text-sm">
    <div class="text-xs uppercase text-slate-500">Account</div>
    <div class="mt-1 font-medium">{$currentUser?.username}</div>
    <div class="text-slate-600">{$currentUser?.email}</div>
    <button class="mt-3 rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white" type="button" on:click={logout}>
      Logout
    </button>
  </div>

  <div class="rounded-lg border bg-white p-3 text-sm text-slate-600">
    More settings coming soon.
  </div>
</div>
