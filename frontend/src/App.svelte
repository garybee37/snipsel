<script lang="ts">
  import { api } from './lib/api';
  import { currentUser } from './lib/session';
  import {
    collections,
    currentCollection,
    currentView,
    getTodayDate,
    isLoading,
    collectionAnchor,
    requestNewSnipsel,
    searchError,
    searchQuery,
    searchResults,
    notificationsStore,
  } from './lib/stores';
  import {
    getCurrentUrl,
    parseRouteFromLocation,
    pushUrl,
    replaceUrl,
    routeToUrl,
    routeToView,
    viewToRoute,
  } from './lib/router';
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
  import Notifications from './routes/Notifications.svelte';

  let initialized = $state(false);

  let isApplyingRoute = $state(false);
  let didInitRoute = $state(false);

  let hasSyncedUrl = $state(false);

  let lastUserId: string | null = $state(null);

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
      applyInitialRoute();
    } catch {
      currentUser.set(null);
      currentView.set({ type: 'loading' });
    } finally {
      initialized = true;
    }
  }

  function applyInitialRoute() {
    if (didInitRoute) return;
    didInitRoute = true;

    const route = parseRouteFromLocation(window.location);
    if (!route) {
      openToday().then(() => {
        const id = $currentCollection?.id;
        replaceUrl(id ? routeToUrl({ v: 'collection', id }) : routeToUrl({ v: 'collections' }));
      });
      return;
    }

    isApplyingRoute = true;
    try {
      currentView.set(routeToView(route));
      if (route.v === 'collection') {
        if (route.sn || route.pos) {
          collectionAnchor.set({ collectionId: route.id, snipselId: route.sn, pos: route.pos });
        } else {
          collectionAnchor.set(null);
        }
      } else {
        collectionAnchor.set(null);
      }
      if (route.v === 'search') {
        searchQuery.set(route.q ?? '');
      }
    } finally {
      isApplyingRoute = false;
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
    } catch {
      currentCollection.set(null);
      collectionAnchor.set(null);
      currentView.set({ type: 'collections' });
      replaceUrl(routeToUrl({ v: 'collections' }));
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

  async function fetchNotifications() {
    try {
      const res = await api.notifications.list();
      notificationsStore.set(res.notifications);
    } catch {
      // ignore
    }
  }

  $effect(() => {
    if (!initialized) {
      initSession();
    }
  });

  $effect(() => {
    const uid = $currentUser?.id ?? null;

    if (uid && uid !== lastUserId) {
      // New login (or user switched): allow deep links to be applied again.
      didInitRoute = false;
      hasSyncedUrl = false;
      lastUserId = uid;
      return;
    }

    if (!uid && lastUserId) {
      // Logout: reset routing init state.
      didInitRoute = false;
      hasSyncedUrl = false;
      lastUserId = null;
    }
  });

  $effect(() => {
    if (initialized && $currentUser && $currentView.type === 'loading') {
      applyInitialRoute();
    }
  });

  $effect(() => {
    if (!initialized || !$currentUser) return;

    // Track view changes
    void $currentView.type;

    fetchNotifications();

    const intervalId = setInterval(fetchNotifications, 60000);
    return () => clearInterval(intervalId);
  });

  $effect(() => {
    if (!initialized) return;
    if (!$currentUser) return;
    if (isApplyingRoute) return;

    if ($currentView.type === 'collection') {
      const a = $collectionAnchor;
      if (!a || a.collectionId !== $currentView.id) collectionAnchor.set(null);
    } else {
      if ($collectionAnchor) collectionAnchor.set(null);
    }

    let route = viewToRoute($currentView);
    if (route.v === 'collection') {
      const a = $collectionAnchor;
      if (a && a.collectionId === route.id) {
        route = { ...route, sn: a.snipselId, pos: a.pos };
      }
    } else if (route.v === 'search') {
      const q = $searchQuery.trim();
      route = { v: 'search', q: q || undefined };
    }

    const nextUrl = routeToUrl(route);
    const cur = getCurrentUrl();

    if (!hasSyncedUrl) {
      replaceUrl(nextUrl);
      hasSyncedUrl = true;
      return;
    }

    const shouldReplace = $currentView.type === 'loading' || $currentView.type === 'search';
    if (shouldReplace) replaceUrl(nextUrl);
    else if (cur !== nextUrl) pushUrl(nextUrl);
  });

  $effect(() => {
    if (!initialized) return;

    const onPopState = () => {
      if (!$currentUser) return;
      const route = parseRouteFromLocation(window.location);
      if (!route) return;

      isApplyingRoute = true;
      try {
        currentView.set(routeToView(route));
        if (route.v === 'collection') {
          if (route.sn || route.pos) {
            collectionAnchor.set({ collectionId: route.id, snipselId: route.sn, pos: route.pos });
          } else {
            collectionAnchor.set(null);
          }
        } else {
          collectionAnchor.set(null);
        }
        if (route.v === 'search') {
          searchQuery.set(route.q ?? '');
        }
      } finally {
        isApplyingRoute = false;
      }
    };

    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
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
  {#if $currentUser}
    <header class="sticky top-4 z-20 mx-auto max-w-3xl px-4 pointer-events-none">
      <div class="pointer-events-auto flex items-center gap-3 rounded-full border border-slate-200 bg-white/80 px-3 py-2 shadow-lg ring-1 ring-black/5 backdrop-blur-md">
        <button
          class="flex items-center gap-2 pl-2 pr-1 font-bold text-lg text-slate-800 transition-colors hover:text-[#4f46e5]"
          type="button"
          onclick={openToday}
        >
          <img src="/logo.svg" alt="snipsel logo" class="h-6 w-6" />
          <span class="hidden sm:inline">snipsel</span>
        </button>
        <input
          class="min-w-0 flex-1 rounded-full border border-slate-200 bg-slate-100/50 px-4 py-2 text-base transition-all focus:border-[#4f46e5] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#4f46e5]/20"
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
        <button
          class="relative grid h-10 w-10 shrink-0 place-items-center rounded-full transition-colors {$currentView.type === 'notifications'
            ? 'bg-[#4f46e5]/10 text-[#4f46e5]'
            : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}"
          type="button"
          onclick={() => currentView.set({ type: 'notifications' })}
          aria-label="Notifications"
          title="Notifications"
        >
          {#if $notificationsStore.filter(n => !n.is_read).length > 0}
            <span class="absolute -right-1 -top-1 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-[#4f46e5] px-1 text-xs font-bold text-white shadow-sm ring-2 ring-white">
              {$notificationsStore.filter(n => !n.is_read).length}
            </span>
          {/if}
          <svg
            class="h-5 w-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
          </svg>
        </button>
        <button
          class="grid h-10 w-10 shrink-0 place-items-center rounded-full transition-colors {$currentView.type === 'settings'
            ? 'bg-[#4f46e5]/10 text-[#4f46e5]'
            : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}"
          type="button"
          onclick={() => currentView.set({ type: 'settings' })}
          aria-label="Settings"
          title="Settings"
        >
          <svg
            class="h-5 w-5"
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
      </div>
    </header>
  {/if}

  <main class="mx-auto max-w-3xl px-4 pt-24 pb-28">
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
    {:else if $currentView.type === 'notifications'}
      <Notifications />
    {:else if $currentView.type === 'snipsel'}
      <SnipselDetail snipselId={$currentView.id} />
    {:else if $currentView.type === 'collection_settings'}
      <CollectionSettings collectionId={$currentView.id} />
    {/if}
  </main>

  {#if $currentUser}
    <nav class="pointer-events-none fixed bottom-0 left-0 right-0 z-10">
      <div class="mx-auto max-w-3xl px-4 pt-2" style="padding-bottom: calc(env(safe-area-inset-bottom) + 0.75rem);">
        <div class="pointer-events-auto mx-auto flex w-fit items-center gap-2 rounded-full border border-slate-200 bg-white/80 px-3 py-2 text-slate-700 shadow-lg ring-1 ring-black/5 backdrop-blur-md">
          <button
            class="grid h-12 w-12 place-items-center rounded-full transition-colors {$currentView.type === 'collections'
              ? 'bg-black/10 text-slate-900'
              : 'hover:bg-black/5 hover:text-slate-900'}"
            type="button"
            onclick={openCollections}
            aria-label="Collections"
            title="Collections"
          >
            <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M3 4h6a2 2 0 012 2v14H5a2 2 0 01-2-2V4z" />
              <path d="M13 6a2 2 0 012-2h6v14a2 2 0 01-2 2h-6V6z" />
            </svg>
          </button>

          <button
            class="grid h-12 w-12 place-items-center rounded-full transition-colors {$currentView.type === 'tags_mentions'
              ? 'bg-black/10 text-slate-900'
              : 'hover:bg-black/5 hover:text-slate-900'}"
            type="button"
            onclick={() => currentView.set({ type: 'tags_mentions' })}
            aria-label="Tags and mentions"
            title="Tags / Mentions"
          >
            <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M4 12h16" />
              <path d="M6 8h12" />
              <path d="M6 16h12" />
              <path d="M10 4l-2 16" />
              <path d="M16 4l-2 16" />
            </svg>
          </button>

          <button
            class="grid h-12 w-12 place-items-center rounded-full transition-colors hover:bg-black/5 hover:text-slate-900"
            type="button"
            onclick={onNewSnipsel}
            aria-label="New snipsel (today)"
            title="New snipsel (today)"
          >
            <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M12 20h9" />
              <path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4 12.5-12.5z" />
            </svg>
          </button>

          <button
            class="grid h-12 w-12 place-items-center rounded-full transition-colors {$currentView.type === 'calendar'
              ? 'bg-black/10 text-slate-900'
              : 'hover:bg-black/5 hover:text-slate-900'}"
            type="button"
            onclick={() => currentView.set({ type: 'calendar' })}
            aria-label="Calendar"
            title="Calendar"
          >
            <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <rect x="3" y="4" width="18" height="18" rx="2" />
              <path d="M16 2v4" />
              <path d="M8 2v4" />
              <path d="M3 10h18" />
            </svg>
          </button>

          <button
            class="grid h-12 w-12 place-items-center rounded-full transition-colors {$currentView.type === 'todos'
              ? 'bg-black/10 text-slate-900'
              : 'hover:bg-black/5 hover:text-slate-900'}"
            type="button"
            onclick={() => currentView.set({ type: 'todos' })}
            aria-label="Todos"
            title="Todos"
          >
            <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M9 11l3 3L22 4" />
              <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
            </svg>
          </button>
        </div>
      </div>
    </nav>
    <div class="h-24"></div>
  {/if}
</div>
