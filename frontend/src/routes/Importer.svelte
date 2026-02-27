<script lang="ts">
  import { currentView } from '../lib/stores';
  import { api } from '../lib/api';
  import { currentUser } from '../lib/session';

  let username = $state('');
  let password = $state('');
  let isLoading = $state(false);
  let error = $state<string | null>(null);
  let isLoggedIn = $state(false);
  let twoSToken = $state('');
  let twoSUserId = $state('');
  
  // Lists from TwoS
  let lists = $state<any[]>([]);
  let selectedLists = $state<Set<string>>(new Set());
  let isLoadingLists = $state(false);
  
  // Import options
  let overwrite = $state(false);
  let directListId = $state('');
  let isImporting = $state(false);
  let importProgress = $state('');
  let importResult = $state<{ imported: number; skipped: number; errors: string[] } | null>(null);
  
  // TwoS sync
  let lastSync = $state('');

  const DEFAULT_ACCENT = '#4f46e5';
  type Rgb = { r: number; g: number; b: number };

  function clampByte(n: number): number {
    return Math.max(0, Math.min(255, Math.round(n)));
  }

  function hexToRgb(hex: string): Rgb | null {
    const h = (hex || '').trim();
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

  async function handleLogin() {
    if (!username || !password) {
      error = 'Please enter username and password';
      return;
    }
    
    isLoading = true;
    error = null;
    
    try {
      const res = await api.importer.twosLogin(username, password);
      twoSToken = res.user.token;
      twoSUserId = res.user.id;
      isLoggedIn = true;
      
      // Load lists after login
      await loadLists();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Login failed';
    } finally {
      isLoading = false;
    }
  }
  
  async function loadLists() {
    isLoadingLists = true;
    error = null;
    try {
      // Use '0' to get everything if no lastSync, or a very old date
      const syncTime = lastSync || "0";
      const res = await api.importer.twosLists(syncTime, twoSUserId, twoSToken);
      lists = res.lists;
      searchQuery = ''; // Clear search when reloading full list
    } catch (e) {
      error = 'Failed to load lists';
    } finally {
      isLoadingLists = false;
    }
  }

  let searchQuery = $state('');
  let isSearching = $state(false);

  async function handleSearch() {
    if (!searchQuery.trim()) {
      await loadLists();
      return;
    }

    isSearching = true;
    error = null;
    try {
      const res = await api.importer.twosSearch(searchQuery, twoSUserId, twoSToken);
      lists = res.lists;
    } catch (e) {
      error = 'Search failed';
    } finally {
      isSearching = false;
    }
  }
  
  function toggleList(listId: string) {
    if (selectedLists.has(listId)) {
      selectedLists.delete(listId);
    } else {
      selectedLists.add(listId);
    }
    selectedLists = new Set(selectedLists);
  }
  
  function selectAll() {
    selectedLists = new Set(lists.map(l => l.id));
  }
  
  function deselectAll() {
    selectedLists = new Set();
  }
  
  
  async function importDirectList() {
    if (!directListId) {
      error = 'Please enter a list ID';
      return;
    }
    
    isImporting = true;
    importProgress = '';
    importResult = null;
    error = null;
    
    try {
      const result = await api.importer.importFromTwoS({
        listIds: [directListId],
        overwrite: overwrite,
        token: twoSToken,
        userId: twoSUserId,
      });
      
      importResult = result;
      directListId = '';
    } catch (e) {
      error = e instanceof Error ? e.message : 'Import failed';
    } finally {
      isImporting = false;
    }
  }

async function startImport() {
    if (selectedLists.size === 0) {
      error = 'Please select at least one list to import';
      return;
    }
    
    isImporting = true;
    importProgress = '';
    importResult = null;
    error = null;
    
    try {
      const result = await api.importer.importFromTwoS({
        listIds: Array.from(selectedLists),
        overwrite: overwrite,
        token: twoSToken,
        userId: twoSUserId,
      });
      importResult = result;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Import failed';
    } finally {
      isImporting = false;
    }
  }
  
  function goBack() {
    currentView.set({ type: 'settings' });
  }
</script>

<div class="space-y-4">
  <div class="flex items-center gap-3">
    <button
      class="grid h-10 w-10 place-items-center rounded-full text-slate-600 transition-colors hover:bg-black/5 hover:text-slate-900"
      onclick={goBack}
      type="button"
      aria-label="Back to settings"
    >
      <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
    </button>
    <h2 class="text-2xl font-semibold text-slate-900">Import from TwoS</h2>
  </div>

  <div class="space-y-3">
    {#if !isLoggedIn}
      <!-- Login Form -->
      <div class="rounded-xl border border-slate-200 bg-white/80 p-6 shadow-sm ring-1 ring-black/5 backdrop-blur-md">
        <div class="mb-6 flex flex-col items-center text-center">
          <div class="mb-4 grid h-16 w-16 place-items-center rounded-2xl bg-slate-50 text-slate-900 shadow-inner ring-1 ring-black/5">
            <svg class="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-slate-900">Connect TwoS Account</h3>
          <p class="mt-1 text-sm text-slate-500">
            Enter your TwoS credentials to access your lists.
          </p>
        </div>
        
        <div class="space-y-4">
          <div>
            <label class="mb-1.5 block text-sm font-medium text-slate-700" for="username">
              Username
            </label>
            <input
              id="username"
              type="text"
              bind:value={username}
              placeholder="e.g. john_doe"
              class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5"
            />
          </div>
          
          <div>
            <label class="mb-1.5 block text-sm font-medium text-slate-700" for="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              bind:value={password}
              placeholder="••••••••"
              class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5"
            />
          </div>
          
          {#if error}
            <div class="rounded-lg bg-red-50 p-3 text-xs font-medium text-red-600">
              {error}
            </div>
          {/if}
          
          <button
            onclick={handleLogin}
            disabled={isLoading || !username || !password}
            class="w-full rounded-full px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all disabled:opacity-50"
            style={`background-color: ${getAccent()}`}
          >
            {isLoading ? 'Connecting...' : 'Continue'}
          </button>
        </div>
      </div>
    {:else}
      <!-- Logged in - show lists -->
      <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <div class="h-2 w-2 rounded-full bg-green-500"></div>
            <span class="text-sm font-medium text-slate-700">Connected as <span class="font-bold text-slate-900">{username}</span></span>
          </div>
          <button
            onclick={() => { isLoggedIn = false; twoSToken = ''; lists = []; }}
            class="text-xs font-semibold text-red-600 hover:text-red-700"
          >
            Disconnect
          </button>
        </div>
      </div>
      
      <!-- Direct list ID import -->
      <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md">
        <div class="text-xs uppercase text-slate-500">Import by ID</div>
        <div class="mt-3 flex gap-2">
          <input
            id="directListId"
            type="text"
            bind:value={directListId}
            placeholder="Enter TwoS list ID"
            class="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5"
          />
          <button
            onclick={importDirectList}
            disabled={!directListId || isImporting}
            class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold shadow-sm ring-1 ring-black/5 hover:bg-slate-50 disabled:opacity-50"
            style={`color: ${getAccent()}`}
          >
            Import
          </button>
        </div>
      </div>

      <!-- Import Settings -->
      <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md">
        <div class="text-xs uppercase text-slate-500">Settings</div>
        <div class="mt-4">
          <label class="flex cursor-pointer items-center gap-3">
            <div 
              class="flex h-5 w-5 shrink-0 items-center justify-center rounded border transition-all"
              style={overwrite ? `background-color: ${getAccent()}; border-color: ${getAccent()}` : 'border-color: #e2e8f0; background-color: white'}
            >
              <input
                type="checkbox"
                bind:checked={overwrite}
                class="sr-only"
              />
              {#if overwrite}
                <svg class="h-3.5 w-3.5 text-white" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                </svg>
              {/if}
            </div>
            <span class="text-xs font-medium text-slate-600">
              Overwrite existing collections with the same name
            </span>
          </label>
        </div>
      </div>

      <div class="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur-md">
        <div class="flex flex-col gap-4 border-b border-slate-100 pb-3 sm:flex-row sm:items-center sm:justify-between">
          <div class="text-xs uppercase text-slate-500">Your Lists</div>
          <div class="relative flex-1 max-w-sm ml-auto">
            <input
              type="text"
              bind:value={searchQuery}
              onkeydown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search in TwoS..."
              class="w-full rounded-full border border-slate-200 bg-white pl-9 pr-3 py-1.5 text-xs shadow-sm ring-1 ring-black/5 focus:outline-none focus:ring-2 focus:ring-black/5"
            />
            <div class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
              {#if isSearching}
                <div class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-slate-200 border-t-slate-500"></div>
              {:else}
                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              {/if}
            </div>
          </div>
          <div class="flex gap-3">
            <button
              onclick={selectAll}
              class="text-xs font-semibold text-slate-500 hover:text-slate-900"
            >
              Select all
            </button>
            <button
              onclick={deselectAll}
              class="text-xs font-semibold text-slate-500 hover:text-slate-900"
            >
              Deselect all
            </button>
          </div>
        </div>
        
        <div class="mt-3 max-h-[400px] space-y-2 overflow-y-auto pr-1">
          {#if isLoadingLists && !isSearching}
            <div class="flex flex-col items-center justify-center py-12">
              <div class="h-6 w-6 animate-spin rounded-full border-2 border-slate-200 border-t-slate-800"></div>
              <span class="mt-2 text-xs text-slate-500">Loading lists...</span>
            </div>
          {:else if lists.length > 0}
            {#each lists as list (list.id)}
              <div
                class="flex cursor-pointer items-center gap-3 rounded-xl border border-slate-100 bg-white/50 p-3 transition-colors hover:border-slate-200 hover:bg-white"
                onclick={() => toggleList(list.id)}
                role="button"
                tabindex="0"
                onkeydown={(e) => e.key === 'Enter' && toggleList(list.id)}
              >
                <div 
                  class="flex h-5 w-5 shrink-0 items-center justify-center rounded border transition-all"
                  style={selectedLists.has(list.id) ? `background-color: ${getAccent()}; border-color: ${getAccent()}` : 'border-color: #e2e8f0; background-color: white'}
                >
                  {#if selectedLists.has(list.id)}
                    <svg class="h-3.5 w-3.5 text-white" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                    </svg>
                  {/if}
                </div>
                <div class="flex-1 min-w-0">
                  <div class="truncate text-sm font-medium text-slate-900">{list.name}</div>
                  {#if list.thingsCount}
                    <div class="text-[10px] font-medium uppercase tracking-wider text-slate-400">{list.thingsCount} things</div>
                  {/if}
                </div>
                {#if list.isDaily}
                  <span class="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-500">
                    Daily
                  </span>
                {/if}
              </div>
            {/each}
          {:else}
            <div class="py-12 text-center">
              <span class="text-sm text-slate-400">No lists found in your account.</span>
            </div>
          {/if}
        </div>

        {#if lists.length > 0}
          <div class="mt-6">
            <button
              onclick={startImport}
              disabled={isImporting || selectedLists.size === 0}
              class="w-full rounded-full px-4 py-3 text-sm font-semibold text-white shadow-sm transition-all disabled:opacity-50"
              style={`background-color: ${getAccent()}`}
            >
              {isImporting ? 'Importing...' : `Import ${selectedLists.size} Selected`}
            </button>
          </div>
        {/if}
      </div>
      
      {#if importProgress}
        <div class="text-center text-xs font-medium text-slate-500">
          {importProgress}
        </div>
      {/if}
      
      {#if importResult}
        <div class="rounded-xl border border-green-200 bg-green-50/50 p-4 shadow-sm backdrop-blur-md">
          <div class="flex items-center gap-2">
            <div class="grid h-6 w-6 place-items-center rounded-full bg-green-100 text-green-600">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div class="font-semibold text-green-900">Import complete</div>
          </div>
          <div class="mt-3 flex gap-4 text-xs">
            <div class="flex flex-col">
              <span class="text-green-600/70 font-medium">Imported</span>
              <span class="text-lg font-bold text-green-900">{importResult.imported}</span>
            </div>
            <div class="flex flex-col">
              <span class="text-green-600/70 font-medium">Skipped</span>
              <span class="text-lg font-bold text-green-900">{importResult.skipped}</span>
            </div>
          </div>
          {#if importResult.errors.length > 0}
            <div class="mt-3 rounded-lg bg-red-50 p-3 text-xs">
              <div class="font-bold text-red-800">Errors</div>
              <ul class="mt-1 list-inside list-disc space-y-1 text-red-700">
                {#each importResult.errors as err}
                  <li>{err}</li>
                {/each}
              </ul>
            </div>
          {/if}
        </div>
      {/if}
    {/if}
  </div>
</div>

