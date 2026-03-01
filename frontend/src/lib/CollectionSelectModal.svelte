<script lang="ts">
  import { api, type SearchCollectionHit } from './api';
  import { onMount } from 'svelte';

  interface Props {
    title: string;
    onSelect: (collectionId: string) => void;
    onClose: () => void;
  }

  let { title, onSelect, onClose }: Props = $props();

  let query = $state('');
  let recentCollections = $state<SearchCollectionHit[]>([]);
  let searchResults = $state<SearchCollectionHit[]>([]);
  let loading = $state(false);
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;
  let inputRef: HTMLInputElement | undefined = $state();

  let displayItems = $derived(query.trim() ? searchResults : recentCollections);

  $effect(() => {
    if (inputRef) {
      inputRef.focus();
    }
  });

  onMount(async () => {
    loading = true;
    try {
      const res = await api.collections.listRecent();
      recentCollections = res.collections.map(c => ({
        id: c.id,
        title: c.title,
        icon: c.icon,
        list_for_day: null // Not heavily used in autocomplete selection context
      }));
    } catch (err) {
      console.error('Failed to load recent collections', err);
    } finally {
      loading = false;
    }
  });

  function handleSearchInput() {
    if (debounceTimer) clearTimeout(debounceTimer);
    
    if (!query.trim()) {
      searchResults = [];
      return;
    }

    debounceTimer = setTimeout(async () => {
      loading = true;
      try {
        const res = await api.collections.autocomplete(query);
        searchResults = res.collections.map(c => ({
          id: c.id,
          title: c.title,
          icon: c.icon,
          list_for_day: null
        }));
      } catch (err) {
        console.error('Failed to search collections', err);
      } finally {
        loading = false;
      }
    }, 300);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

<div
  class="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm transition-all"
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
  tabindex="-1"
  onclick={(e) => e.target === e.currentTarget && onClose()}
  onkeydown={handleKeydown}
>
  <div class="w-full max-w-md overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-black/5 dark:bg-slate-900 dark:ring-white/10 flex flex-col max-h-[85vh]">
    <div class="border-b border-slate-100 bg-slate-50/50 px-6 py-4 dark:border-white/5 dark:bg-slate-800/50 flex items-center justify-between">
      <h2 id="modal-title" class="text-xl font-semibold text-slate-900 dark:text-slate-100">
        {title}
      </h2>
      <button
        class="rounded-full p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/5 dark:hover:text-slate-300"
        type="button"
        onclick={onClose}
        aria-label="Close"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>

    <div class="p-6">
      <div class="relative">
        <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
          <svg class="h-5 w-5 text-slate-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
          </svg>
        </div>
        <input
          bind:this={inputRef}
          type="text"
          class="block w-full rounded-xl border border-slate-200 bg-white py-3 pl-10 pr-3 text-sm placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-white/10 dark:bg-slate-800 dark:text-slate-100 dark:focus:border-indigo-400 dark:focus:ring-indigo-400 shadow-sm"
          placeholder="Search collections..."
          bind:value={query}
          oninput={handleSearchInput}
        />
      </div>
      
      {#if loading && !query && recentCollections.length === 0}
         <div class="mt-8 flex justify-center text-slate-400">
           <svg class="h-6 w-6 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
             <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
             <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
           </svg>
         </div>
      {/if}
    </div>

    <div class="flex-1 overflow-y-auto px-6 pb-6">
      
      {#if displayItems.length > 0}
        <div class="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {query.trim() ? 'Search Results' : 'Recent Collections'}
        </div>
        <div class="space-y-1">
          {#each displayItems as c (c.id)}
            <button
              type="button"
              class="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left transition-colors hover:bg-slate-50 dark:hover:bg-white/5 group"
              onclick={() => onSelect(c.id)}
            >
              <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white shadow-sm ring-1 ring-slate-200 dark:bg-slate-800 dark:ring-white/10 text-xl group-hover:scale-110 transition-transform">
                {c.icon || '📁'}
              </span>
              <span class="flex-1 truncate font-medium text-slate-700 dark:text-slate-200">
                {c.title}
              </span>
            </button>
          {/each}
        </div>
      {:else if query.trim() && !loading}
        <div class="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
          No collections found matching "{query}"
        </div>
      {:else if !query.trim() && !loading && recentCollections.length === 0}
        <div class="py-8 text-center text-sm text-slate-500 dark:text-slate-400">
          No recent collections
        </div>
      {/if}
    </div>
  </div>
</div>
