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

<div class="space-y-4">
  <h2 class="text-2xl font-semibold">Settings</h2>

  <div class="rounded-lg border bg-white p-5 text-base">
    <div class="text-sm uppercase text-slate-500">Account</div>
    <div class="mt-2 text-lg font-medium">{$currentUser?.username}</div>
    <div class="text-slate-600">{$currentUser?.email}</div>
    <button class="mt-4 rounded-md bg-slate-900 px-4 py-3 text-lg font-medium text-white" type="button" on:click={logout}>
      Logout
    </button>
  </div>

  <div class="rounded-lg border bg-white p-5 text-base text-slate-600">
    More settings coming soon.
  </div>
</div>
