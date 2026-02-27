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

<div class="mx-auto w-full max-w-sm pt-8 pb-12">
  <div class="flex flex-col items-center mb-8">
    <div class="grid h-16 w-16 place-items-center rounded-full bg-[#4f46e5]/10 mb-4 shadow-sm ring-1 ring-[#4f46e5]/20 dark:bg-indigo-900/30 dark:ring-indigo-500/30">
      <img src="/logo.svg" alt="snipsel logo" class="h-8 w-8 dark:brightness-110" />
    </div>
    <h1 class="text-3xl font-semibold tracking-tight text-slate-800 dark:text-slate-100">{mode === 'login' ? 'Welcome back' : 'Create account'}</h1>
    <p class="mt-2 text-slate-500 dark:text-slate-400">{mode === 'login' ? 'Sign in to continue' : 'Sign up to get started'}</p>
  </div>

  <form class="space-y-5" onsubmit|preventDefault={submit}>
    <div class="space-y-4 rounded-3xl border border-slate-200 bg-white/80 p-6 shadow-xl ring-1 ring-black/5 backdrop-blur-md dark:border-white/10 dark:bg-slate-900/80 dark:ring-white/10">
      <label class="block">
        <span class="mb-1.5 ml-1 block text-sm font-medium text-slate-600 dark:text-slate-400">Username</span>
        <input 
          class="w-full rounded-full border border-slate-200 bg-white px-5 py-3 text-lg shadow-sm outline-none ring-1 ring-black/5 transition-all focus:border-[#4f46e5] focus:ring-2 focus:ring-[#4f46e5]/20 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:border-indigo-500 dark:focus:ring-indigo-500/20" 
          bind:value={username} 
          autocomplete="username" 
        />
      </label>

      {#if mode === 'register'}
        <label class="block">
          <span class="mb-1.5 ml-1 block text-sm font-medium text-slate-600 dark:text-slate-400">Email</span>
          <input
            class="w-full rounded-full border border-slate-200 bg-white px-5 py-3 text-lg shadow-sm outline-none ring-1 ring-black/5 transition-all focus:border-[#4f46e5] focus:ring-2 focus:ring-[#4f46e5]/20 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:border-indigo-500 dark:focus:ring-indigo-500/20"
            bind:value={email}
            autocomplete="email"
            type="email"
          />
        </label>
      {/if}

      <label class="block">
        <span class="mb-1.5 ml-1 block text-sm font-medium text-slate-600 dark:text-slate-400">Password</span>
        <input
          class="w-full rounded-full border border-slate-200 bg-white px-5 py-3 text-lg shadow-sm outline-none ring-1 ring-black/5 transition-all focus:border-[#4f46e5] focus:ring-2 focus:ring-[#4f46e5]/20 dark:border-white/10 dark:bg-slate-800 dark:text-white dark:focus:border-indigo-500 dark:focus:ring-indigo-500/20"
          bind:value={password}
          autocomplete={mode === 'login' ? 'current-password' : 'new-password'}
          type="password"
        />
      </label>

      {#if errorMessage}
        <div class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-base text-red-700 dark:border-red-900/30 dark:bg-red-950/20 dark:text-red-400">
          {errorMessage}
        </div>
      {/if}
    </div>

    <button
      class="w-full rounded-full bg-[#4f46e5] px-4 py-3.5 text-lg font-semibold text-white shadow-lg transition-all hover:-translate-y-0.5 hover:bg-[#4338ca] hover:shadow-xl disabled:pointer-events-none disabled:opacity-50 dark:bg-indigo-500 dark:hover:bg-indigo-400"
      type="submit"
      disabled={busy}
    >
      {busy ? 'Please wait...' : mode === 'login' ? 'Login' : 'Register'}
    </button>
  </form>

  <button 
    class="mt-6 w-full rounded-full bg-[#4f46e5]/10 px-4 py-3.5 text-base font-semibold text-[#4f46e5] transition-all hover:bg-[#4f46e5]/20 dark:bg-indigo-500/20 dark:text-indigo-400 dark:hover:bg-indigo-500/30" 
    type="button" 
    onclick={toggleMode}
  >
    {mode === 'login' ? 'Need an account? Register' : 'Already have an account? Login'}
  </button>
</div>
