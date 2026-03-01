<script lang="ts">
  import { onMount } from 'svelte';

  interface Props {
    url: string;
  }

  let { url }: Props = $props();

  let data = $state<any>(null);
  let loading = $state(true);
  let error = $state(false);

  async function fetchData() {
    loading = true;
    error = false;
    try {
      const res = await fetch(`/api/proxy/youtube?url=${encodeURIComponent(url)}`, {
        credentials: 'include'
      });
      if (!res.ok) throw new Error('Failed to fetch');
      data = await res.json();
    } catch (e) {
      console.error('YouTube fetch error:', e);
      error = true;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    fetchData();
  });

  const title = $derived(data?.title || 'YouTube Video');
  const author = $derived(data?.author_name || '');
  const thumbnail = $derived(data?.thumbnail_url || '');
</script>

{#if loading}
  <div class="mt-4 flex animate-pulse items-center gap-4 rounded-2xl border border-slate-200 bg-white/50 p-4 dark:border-white/10 dark:bg-slate-900/50">
    <div class="aspect-video w-32 flex-shrink-0 rounded-xl bg-slate-200 dark:bg-white/10"></div>
    <div class="flex-1 space-y-2">
      <div class="h-4 w-3/4 rounded bg-slate-200 dark:bg-white/10"></div>
      <div class="h-3 w-1/2 rounded bg-slate-200 dark:bg-white/10"></div>
    </div>
  </div>
{:else if error || !data}
  <!-- Silently fail -->
{:else}
  <div class="group relative mt-4 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all hover:shadow-md dark:border-white/10 dark:bg-slate-900">
    <div class="absolute inset-0 z-0 bg-gradient-to-br from-red-500/5 to-orange-500/5 opacity-0 transition-opacity group-hover:opacity-100"></div>
    
    <div class="relative z-10 flex flex-col sm:flex-row items-center gap-4 p-4">
      <a 
        href={url} 
        target="_blank" 
        rel="noopener noreferrer"
        class="relative aspect-video w-full sm:w-40 flex-shrink-0 overflow-hidden rounded-xl bg-slate-100 shadow-sm transition-transform hover:scale-[1.02] active:scale-98 dark:bg-white/5"
        onclick={(e) => e.stopPropagation()}
      >
        <img 
          src={thumbnail} 
          alt={title}
          class="h-full w-full object-cover"
        />
        <div class="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 transition-opacity group-hover:opacity-100">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"/>
          </svg>
        </div>
      </a>

      <div class="min-w-0 flex-1">
        <h4 class="line-clamp-2 text-lg font-semibold text-slate-900 group-hover:text-red-600 dark:text-slate-100 dark:group-hover:text-red-400">
          {title}
        </h4>
        <p class="truncate text-sm text-slate-500 dark:text-slate-400">
          {author}
        </p>
        
        <div class="mt-2 flex items-center gap-1.5">
          <svg class="h-3 w-3 text-red-600" viewBox="0 0 24 24" fill="currentColor">
            <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
          </svg>
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">YouTube</span>
        </div>
      </div>

      <a 
        href={url} 
        target="_blank" 
        rel="noopener noreferrer"
        class="hidden sm:grid h-10 w-10 place-items-center rounded-full bg-slate-50 text-slate-400 transition-all hover:bg-slate-100 hover:text-red-600 active:scale-90 dark:bg-white/5 dark:hover:bg-white/10 dark:hover:text-red-400"
        onclick={(e) => e.stopPropagation()}
        aria-label="Open on YouTube"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
      </a>
    </div>
  </div>
{/if}
