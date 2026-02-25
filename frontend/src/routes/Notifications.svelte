<script lang="ts">
  import { api, type Notification } from '../lib/api';
  import { notificationsStore, currentView } from '../lib/stores';

  let viewMode: 'unread' | 'read' = $state('unread');
  let isBusy = $state(false);

  let filteredNotifications = $derived(
    $notificationsStore.filter(n => (viewMode === 'unread' ? !n.is_read : n.is_read))
  );

  async function toggleReadStatus(n: Notification, e: Event) {
    e.stopPropagation(); // prevent clicking the card
    isBusy = true;
    try {
      if (!n.is_read) {
        await api.notifications.markRead(n.id);
        notificationsStore.update(store =>
          store.map(x => (x.id === n.id ? { ...x, is_read: true } : x))
        );
      }
    } finally {
      isBusy = false;
    }
  }

  async function openNotification(n: Notification) {
    if (!n.is_read) {
      await api.notifications.markRead(n.id);
      notificationsStore.update(store =>
        store.map(x => (x.id === n.id ? { ...x, is_read: true } : x))
      );
    }

    if (n.snipsel_id) {
      currentView.set({ type: 'snipsel', id: n.snipsel_id });
    } else if (n.collection_id) {
      currentView.set({ type: 'collection', id: n.collection_id });
    }
  }

  async function markAllRead() {
    isBusy = true;
    try {
      await api.notifications.markAllRead();
      notificationsStore.update(store => store.map(x => ({ ...x, is_read: true })));
    } finally {
      isBusy = false;
    }
  }

  async function deleteAllRead() {
    isBusy = true;
    try {
      await api.notifications.deleteRead();
      notificationsStore.update(store => store.filter(x => !x.is_read));
    } finally {
      isBusy = false;
    }
  }

  function formatDate(iso: string) {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
</script>

<div class="space-y-6">
  <div class="flex flex-col items-center">
    <div class="grid h-16 w-16 place-items-center rounded-full bg-[#4f46e5]/10 text-[#4f46e5] mb-4 shadow-sm ring-1 ring-[#4f46e5]/20">
      <svg class="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
      </svg>
    </div>
    <h1 class="text-3xl font-semibold tracking-tight text-slate-800">Notifications</h1>
  </div>

  <div class="mx-auto flex w-full max-w-sm overflow-hidden rounded-full border border-slate-200 bg-white/80 p-1 shadow-sm ring-1 ring-black/5 backdrop-blur-md" role="tablist">
    <button
      class="flex-1 rounded-full py-2 text-sm font-medium transition-all {viewMode === 'unread' ? 'bg-[#4f46e5] text-white shadow' : 'text-slate-600 hover:bg-slate-100'}"
      onclick={() => (viewMode = 'unread')}
      role="tab"
      aria-selected={viewMode === 'unread'}
    >
      Unread
    </button>
    <button
      class="flex-1 rounded-full py-2 text-sm font-medium transition-all {viewMode === 'read' ? 'bg-[#4f46e5] text-white shadow' : 'text-slate-600 hover:bg-slate-100'}"
      onclick={() => (viewMode = 'read')}
      role="tab"
      aria-selected={viewMode === 'read'}
    >
      Read
    </button>
  </div>

  {#if filteredNotifications.length === 0}
    <div class="py-12 text-center text-slate-500">
      No {viewMode} notifications.
    </div>
  {:else}
    <div class="space-y-3">
      {#each filteredNotifications as n (n.id)}
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div
          class="group flex cursor-pointer items-start gap-4 rounded-3xl border border-slate-200 bg-white/80 p-5 shadow-sm ring-1 ring-black/5 backdrop-blur-md transition-all hover:-translate-y-0.5 hover:shadow-md"
          onclick={() => openNotification(n)}
        >
          <div class="flex-1">
            <p class="text-base text-slate-800">{n.message}</p>
            <p class="mt-1 text-xs text-slate-500">{formatDate(n.created_at)}</p>
          </div>
          
          {#if !n.is_read}
            <button
              class="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-slate-200 bg-white text-slate-400 transition-colors hover:border-[#4f46e5] hover:text-[#4f46e5] focus:outline-none focus:ring-2 focus:ring-[#4f46e5]"
              title="Mark as read"
              aria-label="Mark as read"
              disabled={isBusy}
              onclick={(e) => toggleReadStatus(n, e)}
            >
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 6L9 17l-5-5" />
              </svg>
            </button>
          {/if}
        </div>
      {/each}

      <div class="pt-6">
        {#if viewMode === 'unread'}
          <button
            class="w-full rounded-full border border-slate-200 bg-white/80 px-4 py-3.5 text-base font-semibold text-slate-700 shadow-sm ring-1 ring-black/5 backdrop-blur-md transition-all hover:bg-slate-50 disabled:opacity-50"
            onclick={markAllRead}
            disabled={isBusy}
          >
            Mark all as read
          </button>
        {:else}
          <button
            class="w-full rounded-full border border-slate-200 bg-white/80 px-4 py-3.5 text-base font-semibold text-red-600 shadow-sm ring-1 ring-black/5 backdrop-blur-md transition-all hover:bg-red-50 disabled:opacity-50"
            onclick={deleteAllRead}
            disabled={isBusy}
          >
            Delete all read
          </button>
        {/if}
      </div>
    </div>
  {/if}
</div>