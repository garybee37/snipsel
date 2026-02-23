<script lang="ts">
  import { api } from './lib/api';
  import { currentUser } from './lib/session';
  import {
    collections,
    currentCollection,
    currentView,
    getTodayDate,
    isLoading,
    requestNewSnipsel,
    searchError,
    searchQuery,
    searchResults,
  } from './lib/stores';
  import Login from './routes/Login.svelte';
  import CollectionsList from './routes/CollectionsList.svelte';
  import CollectionOutliner from './routes/CollectionOutliner.svelte';
  import Search from './routes/Search.svelte';
  import Todos from './routes/Todos.svelte';
  import Calendar from './routes/Calendar.svelte';
  import Settings from './routes/Settings.svelte';
  import SnipselDetail from './routes/SnipselDetail.svelte';
  import CollectionSettings from './routes/CollectionSettings.svelte';
  import TagsMentions from './routes/TagsMentions.svelte';

  let initialized = $state(false);

  let isSwitchingCollection = $state(false);

  let lastCollectionId: string | null = $state(null);

  async function pruneEmptySnipsels(collectionId: string) {
    try {
      const res = await api.snipsels.list(collectionId);
      const emptyIds = res.items
        .filter((i) => (i.snipsel.content_markdown ?? '').trim().length === 0 && i.snipsel.attachments.length === 0)
        .map((i) => i.snipsel_id);

      if (emptyIds.length === 0) return;
      for (const id of emptyIds) {
        await api.snipsels.delete(collectionId, id);
      }
    } catch {
      // best-effort
    }
  }

  async function maybeDeleteEmptyDayCollection(collectionId: string) {
    const c = $currentCollection;
    if (!c || c.id !== collectionId) return;
    if (!c.list_for_day) return;

    try {
      await pruneEmptySnipsels(collectionId);
      const res = await api.snipsels.list(collectionId);
      if (res.items.length > 0) return;

      await api.collections.delete(collectionId);
      if ($currentCollection?.id === collectionId) currentCollection.set(null);
      collections.update((xs) => xs.filter((x) => x.id !== collectionId));
    } catch {
      // best-effort
    }
  }

  async function initSession() {
    try {
      const res = await api.me();
      currentUser.set(res.user);
      await openToday();
    } catch {
      currentUser.set(null);
      currentView.set({ type: 'loading' });
    } finally {
      initialized = true;
    }
  }

  async function onNewSnipsel() {
    await openToday();
    requestNewSnipsel();
  }

  async function openToday() {
    isLoading.set(true);
    isSwitchingCollection = true;
    try {
      const today = getTodayDate();
      const res = await api.collections.today(today);
      await pruneEmptySnipsels(res.collection.id);
      currentCollection.set(res.collection);
      currentView.set({ type: 'collection', id: res.collection.id });
    } finally {
      isLoading.set(false);
      isSwitchingCollection = false;
    }
  }

  async function openCollections() {
    isLoading.set(true);
    try {
      const res = await api.collections.list();
      collections.set(res.collections);
      currentView.set({ type: 'collections' });
    } finally {
      isLoading.set(false);
    }
  }

  async function logout() {
    await api.logout();
    currentUser.set(null);
    currentView.set({ type: 'loading' });
  }

  async function openCollectionById(id: string) {
    isLoading.set(true);
    isSwitchingCollection = true;
    try {
      const res = await api.collections.get(id);
      await pruneEmptySnipsels(res.collection.id);
      currentCollection.set(res.collection);
    } finally {
      isLoading.set(false);
      isSwitchingCollection = false;
    }
  }

  async function runSearch() {
    const q = $searchQuery.trim();
    if (!q) {
      searchResults.set(null);
      searchError.set(null);
      return;
    }
    currentView.set({ type: 'search' });
    searchError.set(null);
    isLoading.set(true);
    try {
      const res = await api.search({ q });
      searchResults.set(res);
    } catch {
      searchResults.set(null);
      searchError.set('Search failed');
    } finally {
      isLoading.set(false);
    }
  }

  $effect(() => {
    if (!initialized) {
      initSession();
    }
  });

  $effect(() => {
    if (initialized && $currentUser && $currentView.type === 'loading') {
      openToday().catch(() => {
        currentView.set({ type: 'collections' });
      });
    }
  });

  $effect(() => {
    if ($currentView.type === 'collection') {
      if (isSwitchingCollection) return;
      if ($currentCollection?.id !== $currentView.id) {
        openCollectionById($currentView.id);
      }
    }
  });

  $effect(() => {
    const nextId = $currentView.type === 'collection' ? $currentView.id : null;
    if (lastCollectionId && lastCollectionId !== nextId) {
      pruneEmptySnipsels(lastCollectionId);
      maybeDeleteEmptyDayCollection(lastCollectionId);
    }
    lastCollectionId = nextId;
  });
</script>

<div class="min-h-screen bg-slate-50 text-slate-900">
  <header class="sticky top-0 z-10 border-b bg-white/95 backdrop-blur">
    <div class="mx-auto flex max-w-3xl items-center justify-between gap-3 px-4 py-3">
      <button
        class="font-semibold hover:underline text-lg"
        type="button"
        onclick={openToday}
      >
        snipsel
      </button>
      <input
        class="min-w-0 flex-1 rounded-md border border-slate-200 bg-slate-100 px-3 py-3 text-lg"
        placeholder="Search"
        type="search"
        bind:value={$searchQuery}
        onfocus={() => {
          if ($currentUser) currentView.set({ type: 'search' });
        }}
        onkeydown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            runSearch();
          }
        }}
      />
      {#if $currentUser}
        <button
          class="grid h-12 w-12 place-items-center rounded-md border border-slate-200 bg-slate-100 text-slate-800 hover:bg-slate-200 {$currentView.type === 'settings'
            ? 'bg-slate-200'
            : ''}"
          type="button"
          onclick={() => currentView.set({ type: 'settings' })}
          aria-label="Settings"
          title="Settings"
        >
          <svg
            class="h-6 w-6"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path d="M12 15.5a3.5 3.5 0 100-7 3.5 3.5 0 000 7z" />
            <path d="M19.4 15a1.8 1.8 0 00.36 1.98l.05.05a2.2 2.2 0 01-1.56 3.76h-.07a1.8 1.8 0 00-1.98.36 1.8 1.8 0 00-.52 1.27V22a2.2 2.2 0 01-4.4 0v-.07a1.8 1.8 0 00-.36-1.98 1.8 1.8 0 00-1.27-.52H8a2.2 2.2 0 010-4.4h.07a1.8 1.8 0 001.98-.36 1.8 1.8 0 00.52-1.27V12a2.2 2.2 0 014.4 0v.07a1.8 1.8 0 00.36 1.98 1.8 1.8 0 001.27.52H16a2.2 2.2 0 013.4.93z" />
          </svg>
        </button>
      {/if}
      <div class="w-12"></div>
    </div>
  </header>

  <main class="mx-auto max-w-3xl px-4 py-6">
    {#if !initialized}
      <div class="py-8 text-center text-sm text-slate-500">Loading...</div>
    {:else if !$currentUser}
      <Login />
    {:else if $currentView.type === 'loading'}
      <div class="py-8 text-center text-sm text-slate-500">Loading...</div>
    {:else if $currentView.type === 'collections'}
      <CollectionsList />
    {:else if $currentView.type === 'collection'}
      <CollectionOutliner />
    {:else if $currentView.type === 'search'}
      <Search />
    {:else if $currentView.type === 'tags_mentions'}
      <TagsMentions />
    {:else if $currentView.type === 'todos'}
      <Todos />
    {:else if $currentView.type === 'calendar'}
      <Calendar />
    {:else if $currentView.type === 'settings'}
      <Settings />
    {:else if $currentView.type === 'snipsel'}
      <SnipselDetail snipselId={$currentView.id} />
    {:else if $currentView.type === 'collection_settings'}
      <CollectionSettings collectionId={$currentView.id} />
    {/if}
  </main>

  {#if $currentUser}
    <nav class="fixed bottom-0 left-0 right-0 border-t bg-white">
      <div class="mx-auto grid max-w-3xl grid-cols-5 gap-1 px-2 py-2 text-xl text-slate-700">
        <button
          class="rounded-md px-2 py-4 {$currentView.type === 'collections' ? 'bg-slate-100 font-medium' : ''}"
          type="button"
          onclick={openCollections}
          aria-label="Collections"
          title="Collections"
        >
          <svg class="mx-auto h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M3 4h6a2 2 0 012 2v14H5a2 2 0 01-2-2V4z" />
            <path d="M13 6a2 2 0 012-2h6v14a2 2 0 01-2 2h-6V6z" />
          </svg>
        </button>
        <button
          class="rounded-md px-2 py-4 {$currentView.type === 'tags_mentions' ? 'bg-slate-100 font-medium' : ''}"
          type="button"
          onclick={() => currentView.set({ type: 'tags_mentions' })}
          aria-label="Tags and mentions"
          title="Tags / Mentions"
        >
          <svg class="mx-auto h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M4 12h16" />
            <path d="M6 8h12" />
            <path d="M6 16h12" />
            <path d="M10 4l-2 16" />
            <path d="M16 4l-2 16" />
          </svg>
        </button>

        <button
          class="rounded-md px-2 py-4"
          type="button"
          onclick={onNewSnipsel}
          aria-label="New snipsel (today)"
          title="New snipsel (today)"
        >
          <svg class="mx-auto h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M12 20h9" />
            <path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4 12.5-12.5z" />
          </svg>
        </button>

        <button
          class="rounded-md px-2 py-4 {$currentView.type === 'calendar' ? 'bg-slate-100 font-medium' : ''}"
          type="button"
          onclick={() => currentView.set({ type: 'calendar' })}
          aria-label="Calendar"
          title="Calendar"
        >
          <svg class="mx-auto h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <rect x="3" y="4" width="18" height="18" rx="2" />
            <path d="M16 2v4" />
            <path d="M8 2v4" />
            <path d="M3 10h18" />
          </svg>
        </button>
        <button
          class="rounded-md px-2 py-4 {$currentView.type === 'todos' ? 'bg-slate-100 font-medium' : ''}"
          type="button"
          onclick={() => currentView.set({ type: 'todos' })}
          aria-label="Todos"
          title="Todos"
        >
          <svg class="mx-auto h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M9 11l3 3L22 4" />
            <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
          </svg>
        </button>
      </div>
    </nav>
    <div class="h-16"></div>
  {/if}
</div>
