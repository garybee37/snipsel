<script lang="ts">
  import { currentView } from '../lib/stores';
  import { api } from '../lib/api';

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

  async function handleLogin() {
    if (!username || !password) {
      error = 'Please enter username and password';
      return;
    }
    
    isLoading = true;
    error = null;
    
    try {
      const res = await api.importer.twosLogin(username, password);
      console.log('Login response:', res);
      twoSToken = res.user.token;
      twoSUserId = res.user.id;
      console.log('After setting:', { twoSToken, twoSUserId });
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
    if (!lastSync) {
      const d = new Date();
      d.setFullYear(d.getFullYear() - 2);
      lastSync = d.toISOString();
    }
    isLoadingLists = true;
    try {
      const res = await api.importer.twosLists(lastSync, twoSUserId, twoSToken);
      lists = res.lists;
    } catch (e) {
      error = 'Failed to load lists';
    } finally {
      isLoadingLists = false;
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
    console.log('importDirectList called', { directListId, twoSToken, twoSUserId });
    if (!directListId) {
      error = 'Please enter a list ID';
      return;
    }
    
    console.log('Calling API with:', { listIds: [directListId], overwrite, token: twoSToken, userId: twoSUserId });
    isImporting = true;
    importProgress = '';
    importResult = null;
    error = null;
    
    try {
      console.log('API call starting');
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
      console.log('API call starting');
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

<div class="mx-auto max-w-2xl p-6">
  <div class="mb-6 flex items-center gap-4">
    <button
      class="rounded-lg p-2 hover:bg-slate-100"
      onclick={goBack}
      type="button"
      aria-label="Back to settings"
    >
      <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
    </button>
    <h1 class="text-2xl font-bold text-slate-800">Import from TwoS</h1>
  </div>

  {#if !isLoggedIn}
    <!-- Login Form -->
    <div class="rounded-lg border border-slate-200 bg-white p-6">
      <p class="mb-4 text-slate-600">
        Enter your TwoS credentials to import your lists and things.
      </p>
      
      <div class="space-y-4">
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700" for="username">
            TwoS Username
          </label>
          <input
            id="username"
            type="text"
            bind:value={username}
            placeholder="your username"
            class="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-slate-500 focus:outline-none"
          />
        </div>
        
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-700" for="password">
            TwoS Password
          </label>
          <input
            id="password"
            type="password"
            bind:value={password}
            placeholder="your password"
            class="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-slate-500 focus:outline-none"
          />
        </div>
        
        {#if error}
          <div class="rounded-lg bg-red-50 p-3 text-sm text-red-600">
            {error}
          </div>
        {/if}
        
        <button
          onclick={handleLogin}
          disabled={isLoading}
          class="w-full rounded-lg bg-slate-800 px-4 py-2 font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {isLoading ? 'Logging in...' : 'Login to TwoS'}
        </button>
      </div>
    </div>
  {:else}
    <!-- Logged in - show lists -->
    <div class="space-y-4">
      <div class="flex items-center justify-between rounded-lg border border-slate-200 bg-green-50 p-4">
        <div class="flex items-center gap-2">
          <span class="text-green-600">✓</span>
          <span class="text-sm font-medium text-green-800">
            Logged in as {username}
          </span>
        </div>
        <button
          onclick={() => { isLoggedIn = false; twoSToken = ''; lists = []; }}
          class="text-sm text-green-700 hover:underline"
        >
          Logout
        </button>
      </div>
      
      <!-- Direct list ID import -->
      <div class="rounded-lg border border-slate-200 bg-white p-4">
        <label class="mb-2 block text-sm font-medium text-slate-700" for="directListId">
          Or import a specific list by ID:
        </label>
        <div class="flex gap-2">
          <input
            id="directListId"
            type="text"
            bind:value={directListId}
            placeholder="Enter TwoS list ID"
            class="flex-1 rounded-lg border border-slate-300 px-3 py-2 focus:border-slate-500 focus:outline-none"
          />
          <button
            onclick={importDirectList}
            disabled={!directListId || isImporting}
            class="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            Import
          </button>
        </div>
      </div>

      {#if isLoadingLists}
        <div class="py-8 text-center text-slate-500">
          Loading lists...
        </div>
      {:else if lists.length > 0}
        <!-- Selection controls -->
        <div class="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 p-4">
          <div class="flex gap-2">
            <button
              onclick={selectAll}
              class="text-sm text-slate-600 hover:text-slate-800"
            >
              Select all
            </button>
            <span class="text-slate-300">|</span>
            <button
              onclick={deselectAll}
              class="text-sm text-slate-600 hover:text-slate-800"
            >
              Deselect all
            </button>
          </div>
          <span class="text-sm text-slate-500">
            {selectedLists.size} of {lists.length} selected
          </span>
        </div>
        
        <!-- Lists -->
        <div class="space-y-2">
          {#each lists as list (list.id)}
            <label
              class="flex cursor-pointer items-center gap-3 rounded-lg border border-slate-200 bg-white p-4 hover:bg-slate-50"
            >
              <input
                type="checkbox"
                checked={selectedLists.has(list.id)}
                onchange={() => toggleList(list.id)}
                class="h-5 w-5 rounded border-slate-300 text-slate-800 focus:ring-slate-500"
              />
              <div class="flex-1">
                <div class="font-medium text-slate-800">{list.name}</div>
                {#if list.thingsCount}
                  <div class="text-sm text-slate-500">{list.thingsCount} things</div>
                {/if}
              </div>
              {#if list.isDaily}
                <span class="rounded bg-blue-100 px-2 py-1 text-xs font-medium text-blue-700">
                  Daily
                </span>
              {/if}
            </label>
          {/each}
        </div>
        
        <!-- Import options -->
        <div class="rounded-lg border border-slate-200 bg-white p-4">
          <label class="flex cursor-pointer items-center gap-3">
            <input
              type="checkbox"
              bind:checked={overwrite}
              class="h-5 w-5 rounded border-slate-300 text-slate-800 focus:ring-slate-500"
            />
            <span class="text-sm text-slate-700">
              Overwrite existing collections with the same name
            </span>
          </label>
        </div>
        
        <!-- Import button -->
        <button
          onclick={startImport}
          disabled={isImporting || selectedLists.size === 0}
          class="w-full rounded-lg bg-slate-800 px-4 py-3 font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {isImporting ? 'Importing...' : `Import ${selectedLists.size} list${selectedLists.size === 1 ? '' : 's'}`}
        </button>
        
        {#if importProgress}
          <div class="text-center text-sm text-slate-500">
            {importProgress}
          </div>
        {/if}
        
        {#if importResult}
          <div class="rounded-lg border border-slate-200 bg-green-50 p-4">
            <div class="font-medium text-green-800">Import complete!</div>
            <div class="mt-2 space-y-1 text-sm text-green-700">
              <div>Imported: {importResult.imported}</div>
              <div>Skipped: {importResult.skipped}</div>
              {#if importResult.errors.length > 0}
                <div class="mt-2 text-red-600">
                  Errors:
                  <ul class="list-inside list-disc">
                    {#each importResult.errors as err}
                      <li>{err}</li>
                    {/each}
                  </ul>
                </div>
              {/if}
            </div>
          </div>
        {/if}
      {:else}
        <div class="py-8 text-center text-slate-500">
          No lists found
        </div>
      {/if}
    </div>
  {/if}
</div>
