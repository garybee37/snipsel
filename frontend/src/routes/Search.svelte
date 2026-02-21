<script lang="ts">
  import { currentView, isLoading, searchError, searchQuery, searchResults } from '../lib/stores';

  function openSnipsel(id: string) {
    currentView.set({ type: 'snipsel', id });
  }
</script>

<div class="space-y-3">
  <h2 class="text-lg font-semibold">Search</h2>

  <div class="text-sm text-slate-600">
    Query: <span class="font-medium">{$searchQuery.trim() || '—'}</span>
  </div>

  {#if $searchError}
    <div class="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
      {$searchError}
    </div>
  {/if}

  {#if $isLoading && !$searchResults}
    <div class="py-6 text-center text-sm text-slate-500">Searching...</div>
  {:else if $searchResults}
    <div class="space-y-2">
      <div class="text-xs font-medium uppercase text-slate-500">Snipsels</div>
      {#if $searchResults.snipsels.length === 0}
        <div class="text-sm text-slate-500">No snipsels</div>
      {:else}
        <div class="space-y-1">
          {#each $searchResults.snipsels as s}
            <button
              class="w-full rounded-md border bg-white px-3 py-2 text-left text-sm hover:bg-slate-50"
              type="button"
              onclick={() => openSnipsel(s.id)}
            >
              <div class="flex items-center justify-between gap-2">
                <span class="font-medium">{s.type}</span>
                <span class="text-xs text-slate-500">{new Date(s.modified_at).toLocaleString()}</span>
              </div>
              <div class="mt-1 line-clamp-2 text-slate-700">{s.content_markdown ?? ''}</div>
            </button>
          {/each}
        </div>
      {/if}
    </div>
  {:else}
    <div class="text-sm text-slate-500">Type a query in the header and press Enter.</div>
  {/if}
</div>
