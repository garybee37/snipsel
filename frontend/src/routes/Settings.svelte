<script lang="ts">
  import { api, type Collection } from '../lib/api';
  import { currentUser } from '../lib/session';
  import { collectionAnchor, currentView } from '../lib/stores';

  const DEFAULT_ACCENT = '#4f46e5';
  type Rgb = { r: number; g: number; b: number };

  let defaultHeaderColor = $state('');
  let templateCollections = $state<Collection[]>([]);
  let dayTemplateId = $state<string>('');
  let isBusy = $state(false);
  let showPasscodeForm = $state(false);
  let passcode = $state('');
  let passwordConfirm = $state('');
  let passcodeError = $state('');

  function clampByte(n: number): number {
    return Math.max(0, Math.min(255, Math.round(n)));
  }

  function hexToRgb(hex: string): Rgb | null {
    const h = hex.trim();
    const m = /^#([0-9a-fA-F]{6})$/.exec(h);
    if (!m) return null;
    const v = m[1];
    return {
      r: parseInt(v.slice(0, 2), 16),
      g: parseInt(v.slice(2, 4), 16),
      b: parseInt(v.slice(4, 6), 16),
    };
  }

  function mixRgb(a: Rgb, b: Rgb, t: number): Rgb {
    const tt = Math.max(0, Math.min(1, t));
    return {
      r: clampByte(a.r + (b.r - a.r) * tt),
      g: clampByte(a.g + (b.g - a.g) * tt),
      b: clampByte(a.b + (b.b - a.b) * tt),
    };
  }

  function rgba(c: Rgb, alpha: number): string {
    const a = Math.max(0, Math.min(1, alpha));
    return `rgba(${c.r}, ${c.g}, ${c.b}, ${a})`;
  }

  function getAccent(): string {
    const raw = ($currentUser?.default_collection_header_color || '').trim() || DEFAULT_ACCENT;
    return /^#[0-9a-fA-F]{6}$/.test(raw) ? raw : DEFAULT_ACCENT;
  }

  function getAccentTint(): string {
    const base = { r: 255, g: 255, b: 255 };
    const accent = hexToRgb(getAccent());
    const mixed = accent ? mixRgb(base, accent, 0.14) : base;
    return rgba(mixed, 0.96);
  }

  async function logout() {
    await api.logout();
    currentUser.set(null);
    collectionAnchor.set(null);
    currentView.set({ type: 'loading' });
  }

  async function saveDefaultHeaderColor() {
    isBusy = true;
    try {
      const v = defaultHeaderColor.trim() || null;
      const res = await api.updateMe({ default_collection_header_color: v });
      currentUser.set(res.user);
    } finally {
      isBusy = false;
    }
  }

  async function toggleCarryOver() {
    isBusy = true;
    try {
      const next = !Boolean($currentUser?.carry_over_open_tasks ?? true);
      const res = await api.updateMe({ carry_over_open_tasks: next });
      currentUser.set(res.user);
    } finally {
      isBusy = false;
    }
  }

  async function loadTemplates() {
    const res = await api.collections.list();
    templateCollections = res.collections.filter((c) => Boolean(c.is_template));
  }

  async function saveDayTemplate() {
    isBusy = true;
    try {
      const id = dayTemplateId.trim() || null;
      const res = await api.updateMe({ day_collection_template_id: id });
      currentUser.set(res.user);
    } finally {
      isBusy = false;
    }
  }

  async function savePasscode() {
    if (passcode.length < 4) {
      passcodeError = 'Passcode must be at least 4 digits';
      return;
    }
    isBusy = true;
    passcodeError = '';
    try {
      await api.passcode.set({ passcode, password_confirm: passwordConfirm });
      const res = await api.me();
      currentUser.set(res.user);
      showPasscodeForm = false;
      passcode = '';
      passwordConfirm = '';
    } catch (e: any) {
      passcodeError = e.error?.message || 'Failed to set passcode';
    } finally {
      isBusy = false;
    }
  }

  $effect(() => {
    defaultHeaderColor = $currentUser?.default_collection_header_color ?? DEFAULT_ACCENT;
    dayTemplateId = $currentUser?.day_collection_template_id ?? '';
  });

  $effect(() => {
    loadTemplates();
  });
</script>

<div class="space-y-4">
  <h2 class="flex items-center gap-2 text-2xl font-semibold">
    <svg class="h-6 w-6 text-slate-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.72V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.17a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
    <span>Settings</span>
  </h2>

  <div class="space-y-3">
    <!-- Account -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md">
      <div class="text-xs uppercase text-slate-500">Account</div>
      <div class="mt-3 flex items-center justify-between gap-4">
        <div class="min-w-0 flex-1">
          <div class="truncate text-lg font-medium text-slate-900">{$currentUser?.username}</div>
          <div class="truncate text-sm text-slate-500">{$currentUser?.email}</div>
        </div>
        <button 
          class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-red-600 shadow-sm ring-1 ring-black/5 hover:bg-red-50 disabled:opacity-50" 
          type="button" 
          onclick={logout}
          disabled={isBusy}
        >
          Logout
        </button>
      </div>
    </div>

    <!-- Appearance -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md">
      <div class="text-xs uppercase text-slate-500">Appearance</div>
      <div class="mt-3">
        <label for="accent-color-picker" class="block text-sm font-medium text-slate-700">Default collection header color</label>
        <div class="mt-2 flex items-center gap-2">
          <div class="flex flex-1 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm ring-1 ring-black/5">
            <input id="accent-color-picker" class="h-8 w-8 cursor-pointer overflow-hidden rounded border-none bg-transparent" type="color" bind:value={defaultHeaderColor} />
            <input class="min-w-0 flex-1 border-none bg-transparent text-sm font-mono text-slate-700 focus:outline-none focus:ring-0" bind:value={defaultHeaderColor} />
          </div>
          <button
            class="rounded-full border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50"
            style={`color: ${getAccent()}`}
            type="button"
            onclick={saveDefaultHeaderColor}
            disabled={isBusy}
          >
            Save
          </button>
        </div>
      </div>
    </div>

    <!-- Day Template -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md">
      <div class="text-xs uppercase text-slate-500">Day template</div>
      <div class="mt-3">
        <label for="day-template-select" class="block text-sm font-medium text-slate-700">Template for new daily collections</label>
        <div class="mt-2 flex items-center gap-2">
          <select 
            id="day-template-select"
            class="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5" 
            bind:value={dayTemplateId}
          >
            <option value="">No template</option>
            {#each templateCollections as c (c.id)}
              <option value={c.id}>
                {c.icon} {c.title}
              </option>
            {/each}
          </select>
          <button
            class="rounded-full border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50"
            style={`color: ${getAccent()}`}
            type="button"
            onclick={saveDayTemplate}
            disabled={isBusy}
          >
            Save
          </button>
        </div>
      </div>
    </div>

    <!-- Tasks -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md">
      <div class="text-xs uppercase text-slate-500">Tasks</div>
      <div class="mt-3 flex items-center justify-between gap-4">
        <div>
          <div class="text-sm font-medium text-slate-900">Carry over open tasks</div>
          <div class="text-xs text-slate-500">Move unfinished tasks from the last 30 days into today.</div>
        </div>
        <button
          class="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold transition-all hover:bg-slate-50 disabled:opacity-40"
          type="button"
          onclick={toggleCarryOver}
          disabled={isBusy}
          style={Boolean($currentUser?.carry_over_open_tasks ?? true) ? `border-color: ${getAccent()}; color: ${getAccent()}; background-color: ${getAccentTint()}` : undefined}
        >
          {Boolean($currentUser?.carry_over_open_tasks ?? true) ? 'On' : 'Off'}
        </button>
      </div>
    </div>

    <!-- Security -->
    <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md">
      <div class="flex items-center gap-2 text-xs uppercase text-slate-500">
        <svg 
          class="h-3 w-3 transition-colors" 
          viewBox="0 0 24 24" 
          fill={$currentUser?.passcode_set ? 'currentColor' : 'none'} 
          stroke="currentColor" 
          stroke-width="2.5" 
          stroke-linecap="round" 
          stroke-linejoin="round"
          style={$currentUser?.passcode_set ? `color: ${getAccent()}` : 'color: #94a3b8'}
        >
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
          <path d="M7 11V7a5 5 0 0 1 10 0v4" />
        </svg>
        <span>Security</span>
      </div>
      
      {#if !showPasscodeForm}
        <div class="mt-3 flex items-center justify-between gap-4">
          <div>
            <div class="text-sm font-medium text-slate-900">Personal Passcode</div>
            <div class="text-xs text-slate-500">
              {$currentUser?.passcode_set ? 'Passcode is active.' : 'Set a passcode to protect sensitive collections.'}
            </div>
          </div>
          <button
            class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 transition-all"
            style={`color: ${getAccent()}`}
            type="button"
            onclick={() => { showPasscodeForm = true; passcodeError = ''; }}
            disabled={isBusy}
          >
            {$currentUser?.passcode_set ? 'Change' : 'Set Passcode'}
          </button>
        </div>
      {:else}
        <div class="mt-4 space-y-4 transition-all">
          <div>
            <label for="new-passcode" class="block text-sm font-medium text-slate-700">New 4-digit passcode</label>
            <input
              id="new-passcode"
              type="password"
              inputmode="numeric"
              maxlength="12"
              class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5"
              bind:value={passcode}
              oninput={(e) => passcode = e.currentTarget.value.replace(/\D/g, '')}
              placeholder="••••"
            />
          </div>
          <div>
            <label for="password-confirm" class="block text-sm font-medium text-slate-700">Confirm account password</label>
            <input
              id="password-confirm"
              type="password"
              class="mt-1 block w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5"
              bind:value={passwordConfirm}
              placeholder="Your account password"
            />
          </div>
          
          {#if passcodeError}
            <div class="text-xs font-medium text-red-600">{passcodeError}</div>
          {/if}
          
          <div class="flex items-center gap-2 pt-2">
            <button
              class="flex-1 rounded-full px-4 py-2.5 text-sm font-semibold text-white shadow-sm disabled:opacity-50 transition-all"
              style={`background-color: ${getAccent()}`}
              type="button"
              onclick={savePasscode}
              disabled={isBusy || passcode.length < 4 || !passwordConfirm}
            >
              Save Passcode
            </button>
            <button
              class="flex-1 rounded-full border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50 transition-all"
              type="button"
              onclick={() => { showPasscodeForm = false; passcode = ''; passwordConfirm = ''; }}
              disabled={isBusy}
            >
              Cancel
            </button>
          </div>
        </div>
      {/if}
    </div>

    <div class="mt-4 border-t border-slate-200 pt-4">
      <button
        class="flex w-full items-center gap-3 rounded-lg p-3 text-left hover:bg-slate-50"
        onclick={() => currentView.set({ type: 'importer' })}
        type="button"
      >
        <svg class="h-5 w-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
        <div>
          <div class="font-medium text-slate-800">Import from TwoS</div>
          <div class="text-sm text-slate-500">Import lists and things from TwoS</div>
        </div>
      </button>
    </div>

    <div class="py-4 text-center text-xs text-slate-400">
      More settings coming soon.
    </div>
  </div>
</div>
