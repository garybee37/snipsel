<script lang="ts">
  import { api } from '../lib/api';
  import { currentUser } from '../lib/session';

  let mode: 'login' | 'register' = 'login';
  let username = '';
  let email = '';
  let password = '';
  let errorMessage: string | null = null;
  let busy = false;

  async function submit() {
    errorMessage = null;
    busy = true;
    try {
      if (mode === 'login') {
        await api.login({ username, password });
      } else {
        await api.register({ username, email, password });
      }

      const res = await api.me();
      currentUser.set(res.user);
    } catch (e) {
      if (typeof e === 'object' && e && 'error' in e) {
        const err = e as { error: { message?: string } };
        errorMessage = err.error.message ?? 'Request failed';
      } else {
        errorMessage = 'Request failed';
      }
    } finally {
      busy = false;
    }
  }

  function toggleMode() {
    mode = mode === 'login' ? 'register' : 'login';
    errorMessage = null;
  }
</script>

<div class="mx-auto w-full max-w-sm">
  <h1 class="mb-4 text-xl font-semibold">{mode === 'login' ? 'Login' : 'Register'}</h1>

  <form class="space-y-3" on:submit|preventDefault={submit}>
    <label class="block">
      <span class="mb-1 block text-xs font-medium text-slate-600">Username</span>
      <input class="w-full rounded-md border px-3 py-2 text-sm" bind:value={username} autocomplete="username" />
    </label>

    {#if mode === 'register'}
      <label class="block">
        <span class="mb-1 block text-xs font-medium text-slate-600">Email</span>
        <input
          class="w-full rounded-md border px-3 py-2 text-sm"
          bind:value={email}
          autocomplete="email"
          type="email"
        />
      </label>
    {/if}

    <label class="block">
      <span class="mb-1 block text-xs font-medium text-slate-600">Password</span>
      <input
        class="w-full rounded-md border px-3 py-2 text-sm"
        bind:value={password}
        autocomplete={mode === 'login' ? 'current-password' : 'new-password'}
        type="password"
      />
    </label>

    {#if errorMessage}
      <div class="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
        {errorMessage}
      </div>
    {/if}

    <button
      class="w-full rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
      type="submit"
      disabled={busy}
    >
      {busy ? '...' : mode === 'login' ? 'Login' : 'Register'}
    </button>
  </form>

  <button class="mt-4 text-sm text-slate-600 underline" type="button" on:click={toggleMode}>
    {mode === 'login' ? 'Create account' : 'I have an account'}
  </button>
</div>
