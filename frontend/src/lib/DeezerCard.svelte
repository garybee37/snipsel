<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from './api';

  interface Props {
    type: 'track' | 'album' | 'artist';
    id: string;
    url: string;
  }

  let { type, id, url }: Props = $props();

  let data = $state<any>(null);
  let loading = $state(true);
  let error = $state(false);

  async function fetchData() {
    loading = true;
    error = false;
    try {
      // Use the new backend proxy
      let query = '';
      if (type && id) {
        query = `type=${type}&id=${id}`;
      } else if (url) {
        query = `url=${encodeURIComponent(url)}`;
      }

      if (!query) throw new Error('Missing parameters');

      const res = await fetch(`/api/proxy/deezer?${query}`, {
        credentials: 'include'
      });
      if (!res.ok) throw new Error('Failed to fetch');
      const json = await res.json();
      data = json;
      
      // If we got type/id back from resolving a short URL, we can use them
      // although deriving from data is safer.
    } catch (e) {
      console.error('Deezer fetch error:', e);
      error = true;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    fetchData();
  });

  const title = $derived.by(() => {
    if (!data) return '';
    if (type === 'track') return data.title;
    if (type === 'album') return data.title;
    if (type === 'artist') return data.name;
    return '';
  });

  const subtitle = $derived.by(() => {
    if (!data) return '';
    if (type === 'track') return data.artist?.name;
    if (type === 'album') return data.artist?.name;
    if (type === 'artist') return 'Artist';
    return '';
  });

  const coverUrl = $derived.by(() => {
    if (!data) return '';
    if (type === 'track') return data.album?.cover_medium || data.artist?.picture_medium;
    if (type === 'album') return data.cover_medium;
    if (type === 'artist') return data.picture_medium;
    return '';
  });
</script>

{#if loading}
  <div class="mt-4 flex animate-pulse items-center gap-4 rounded-2xl border border-slate-200 bg-white/50 p-4 dark:border-white/10 dark:bg-slate-900/50">
    <div class="h-20 w-20 flex-shrink-0 rounded-xl bg-slate-200 dark:bg-white/10"></div>
    <div class="flex-1 space-y-2">
      <div class="h-4 w-3/4 rounded bg-slate-200 dark:bg-white/10"></div>
      <div class="h-3 w-1/2 rounded bg-slate-200 dark:bg-white/10"></div>
    </div>
  </div>
{:else if error || !data || data.error}
  <!-- Silently fail or minimal fallback -->
{:else}
  <div class="group relative mt-4 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all hover:shadow-md dark:border-white/10 dark:bg-slate-900">
    <!-- Glassmorphic background effect -->
    <div class="absolute inset-0 z-0 bg-gradient-to-br from-indigo-500/5 to-purple-500/5 opacity-0 transition-opacity group-hover:opacity-100"></div>
    
    <div class="relative z-10 flex items-center gap-4 p-4">
      <a 
        href={url} 
        target="_blank" 
        rel="noopener noreferrer"
        class="relative h-20 w-20 flex-shrink-0 overflow-hidden rounded-xl bg-slate-100 shadow-sm transition-transform hover:scale-105 active:scale-95 dark:bg-white/5"
        onclick={(e) => e.stopPropagation()}
      >
        <img 
          src={coverUrl} 
          alt={title}
          class="h-full w-full object-cover"
        />
        <div class="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 transition-opacity group-hover:opacity-100">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
      </a>

      <div class="min-w-0 flex-1">
        <h4 class="truncate text-lg font-semibold text-slate-900 group-hover:text-indigo-600 dark:text-slate-100 dark:group-hover:text-indigo-400">
          {title}
        </h4>
        <p class="truncate text-sm text-slate-500 dark:text-slate-400">
          {subtitle}
        </p>
        
        <div class="mt-2 flex items-center gap-1">
          <svg class="h-3 w-3 text-slate-400" viewBox="0 0 24 24" fill="currentColor">
             <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 18.423c-3.547 0-6.423-2.876-6.423-6.423S8.453 5.577 12 5.577s6.423 2.876 6.423 6.423-2.876 6.423-6.423 6.423zM12 7.73c-2.358 0-4.27 1.912-4.27 4.27s1.912 4.27 4.27 4.27 4.27-1.912 4.27-4.27-1.912-4.27-4.27-4.27z"/>
          </svg>
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Deezer</span>
        </div>
      </div>

      <a 
        href={url} 
        target="_blank" 
        rel="noopener noreferrer"
        class="grid h-10 w-10 place-items-center rounded-full bg-slate-50 text-slate-400 transition-all hover:bg-slate-100 hover:text-indigo-600 active:scale-90 dark:bg-white/5 dark:hover:bg-white/10 dark:hover:text-indigo-400"
        onclick={(e) => e.stopPropagation()}
        aria-label="Open on Deezer"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
      </a>
    </div>
  </div>
{/if}

<style>
  /* Optional: any specific styles for the card */
</style>
