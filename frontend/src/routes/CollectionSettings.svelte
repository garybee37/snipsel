<script lang="ts">
  import { api, type Collection, type CollectionShare, type UserLite } from '../lib/api';
  import { collectionAnchor, collections, currentCollection, currentView, isLoading } from '../lib/stores';

  interface Props {
    collectionId: string;
  }

  let { collectionId }: Props = $props();

  let collection = $state<Collection | null>(null);
  let title = $state('');
  let icon = $state('');
  let headerImageUrl = $state('');
  let headerColor = $state('');
  let isFavorite = $state(false);
  let defaultSnipselType = $state('');
  let saving = $state(false);

  let users = $state<UserLite[]>([]);
  let shares = $state<CollectionShare[]>([]);
  let shareUserId = $state('');
  let sharePermission = $state<'read' | 'write'>('read');
  let sharingBusy = $state(false);

  async function load() {
    isLoading.set(true);
    try {
      const res = await api.collections.get(collectionId);
      collection = res.collection;
      title = collection.title;
      icon = collection.icon;
      headerImageUrl = collection.header_image_url ?? '';
      headerColor = collection.header_color ?? '';
      isFavorite = Boolean(collection.is_favorite);
      defaultSnipselType = collection.default_snipsel_type ?? '';

      const [uRes, sRes] = await Promise.all([
        api.users.list(),
        api.collections.listShares(collectionId),
      ]);
      users = uRes.users;
      shares = sRes.shares;
    } finally {
      isLoading.set(false);
    }
  }

  async function addShare() {
    if (!collection) return;
    if (!shareUserId) return;
    sharingBusy = true;
    try {
      await api.collections.createShare(collection.id, {
        shared_with_user_id: shareUserId,
        permission: sharePermission,
      });
      const sRes = await api.collections.listShares(collection.id);
      shares = sRes.shares;
      shareUserId = '';
      sharePermission = 'read';
    } finally {
      sharingBusy = false;
    }
  }

  async function revokeShare(shareId: string) {
    if (!collection) return;
    if (!confirm('Remove access?')) return;
    sharingBusy = true;
    try {
      await api.collections.deleteShare(collection.id, shareId);
      shares = shares.filter((s) => s.id !== shareId);
    } finally {
      sharingBusy = false;
    }
  }

  async function save() {
    if (!collection) return;
    saving = true;
    try {
      const res = await api.collections.update(collection.id, {
        title: title.trim(),
        icon: icon.trim(),
        header_image_url: headerImageUrl.trim() || undefined,
        header_color: headerColor.trim() || undefined,
        is_template: Boolean(collection.is_template),
        default_snipsel_type: defaultSnipselType.trim() || undefined,
      });
      collection = res.collection;
      collections.update((list) => list.map((c) => (c.id === res.collection.id ? res.collection : c)));
      currentCollection.update((c) => (c?.id === res.collection.id ? res.collection : c));
    } finally {
      saving = false;
    }
  }

  async function toggleArchive() {
    if (!collection) return;
    const res = await api.collections.update(collection.id, { archived: !collection.archived });
    collection = res.collection;
    collections.update((list) => list.map((c) => (c.id === res.collection.id ? res.collection : c)));
  }

  async function toggleFavorite() {
    if (!collection) return;
    const next = !isFavorite;
    isFavorite = next;
    if (next) {
      await api.collections.favorite(collection.id);
    } else {
      await api.collections.unfavorite(collection.id);
    }
    const refreshed = await api.collections.get(collection.id);
    collection = refreshed.collection;
    collections.update((list) => list.map((c) => (c.id === collection?.id ? collection : c)));
    currentCollection.update((c) => (c?.id === collection?.id ? collection : c));
  }

  async function toggleTemplate() {
    if (!collection) return;
    const next = !Boolean(collection.is_template);
    collection = { ...collection, is_template: next };
    const res = await api.collections.update(collection.id, { is_template: next });
    collection = res.collection;
    collections.update((list) => list.map((c) => (c.id === res.collection.id ? res.collection : c)));
    currentCollection.update((c) => (c?.id === res.collection.id ? res.collection : c));
  }

  async function deleteCollection() {
    if (!collection) return;
    if (!confirm('Delete collection?')) return;
    const id = collection.id;
    await api.collections.delete(id);
    collections.update((list) => list.filter((c) => c.id !== id));
    currentCollection.set(null);
    collectionAnchor.set(null);
    currentView.set({ type: 'collections' });
  }

  load();
</script>

<div class="space-y-3">
  <button class="text-sm text-slate-600 underline" type="button" onclick={() => currentView.set({ type: 'collections' })}>
    Back
  </button>

  <h2 class="text-lg font-semibold">Edit collection</h2>

  {#if !collection}
    <div class="text-sm text-slate-500">Loading...</div>
  {:else}
    <div class="rounded-lg border bg-white p-3 space-y-3">
      <div class="flex items-center justify-between">
        <div class="text-xs font-medium uppercase text-slate-500">Info</div>
        <div class="flex items-center gap-2">
          <button
            class="grid h-10 w-10 place-items-center rounded-md border text-xl hover:bg-slate-50"
            type="button"
            aria-label={isFavorite ? 'Unfavorite' : 'Favorite'}
            title={isFavorite ? 'Unfavorite' : 'Favorite'}
            onclick={toggleFavorite}
          >
            {isFavorite ? '♥' : '♡'}
          </button>
          <button
            class="grid h-10 w-10 place-items-center rounded-md border text-xl hover:bg-slate-50"
            type="button"
            aria-label={collection?.is_template ? 'Unset template' : 'Mark as template'}
            title={collection?.is_template ? 'Template' : 'Not a template'}
            onclick={toggleTemplate}
          >
            {collection?.is_template ? '▦' : '▢'}
          </button>
        </div>
      </div>

      <label class="block">
        <span class="mb-1 block text-xs font-medium text-slate-600">Title</span>
        <input class="w-full rounded-md border px-3 py-2 text-sm" bind:value={title} />
      </label>

      <label class="block">
        <span class="mb-1 block text-xs font-medium text-slate-600">Icon</span>
        <input class="w-24 rounded-md border px-3 py-2 text-sm" bind:value={icon} />
      </label>

      <label class="block">
        <span class="mb-1 block text-xs font-medium text-slate-600">Header image URL</span>
        <input class="w-full rounded-md border px-3 py-2 text-sm" bind:value={headerImageUrl} />
      </label>

      <label class="block">
        <span class="mb-1 block text-xs font-medium text-slate-600">Header color</span>
        <div class="flex items-center gap-3">
          <input class="h-10 w-16 rounded-md border" type="color" bind:value={headerColor} />
          <input class="flex-1 rounded-md border px-3 py-2 text-sm" bind:value={headerColor} placeholder="#4f46e5" />
          <button
            class="rounded-md border px-3 py-2 text-sm"
            type="button"
            onclick={() => (headerColor = '')}
            disabled={!headerColor.trim()}
          >
            Clear
          </button>
        </div>
      </label>

      <label class="block">
        <span class="mb-1 block text-xs font-medium text-slate-600">Default snipsel type</span>
        <div class="flex items-center gap-3">
          <select class="flex-1 rounded-md border px-3 py-2 text-sm" bind:value={defaultSnipselType}>
            <option value="">Text (default)</option>
            <option value="task">Task</option>
            <option value="image">Image</option>
            <option value="attachment">File</option>
          </select>
          <button
            class="rounded-md border px-3 py-2 text-sm"
            type="button"
            onclick={() => (defaultSnipselType = '')}
            disabled={!defaultSnipselType.trim()}
          >
            Clear
          </button>
        </div>
      </label>

      <div class="rounded-lg border bg-slate-50 p-3 space-y-3">
        <div class="text-xs font-medium uppercase text-slate-500">Sharing</div>

        <div class="flex flex-col gap-2">
          <select class="w-full rounded-md border px-3 py-2 text-sm" bind:value={shareUserId} disabled={sharingBusy}>
            <option value="">Select user…</option>
            {#each users as u (u.id)}
              <option value={u.id}>{u.username}</option>
            {/each}
          </select>
          <div class="flex gap-2">
            <button
              class="flex-1 rounded-md border px-3 py-2 text-sm {sharePermission === 'read' ? 'bg-white font-medium' : 'bg-slate-50'}"
              type="button"
              onclick={() => (sharePermission = 'read')}
              disabled={sharingBusy}
            >
              Read
            </button>
            <button
              class="flex-1 rounded-md border px-3 py-2 text-sm {sharePermission === 'write' ? 'bg-white font-medium' : 'bg-slate-50'}"
              type="button"
              onclick={() => (sharePermission = 'write')}
              disabled={sharingBusy}
            >
              Write
            </button>
            <button
              class="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white"
              type="button"
              onclick={addShare}
              disabled={sharingBusy || !shareUserId}
              aria-label="Share collection"
            >
              Add
            </button>
          </div>
        </div>

        {#if shares.length === 0}
          <div class="text-sm text-slate-500">Not shared yet</div>
        {:else}
          <div class="space-y-2">
            {#each shares as s (s.id)}
              <div class="flex items-center justify-between gap-3 rounded-md border bg-white px-3 py-2">
                <div class="min-w-0">
                  <div class="truncate text-sm font-medium">{s.shared_with_username ?? s.shared_with_user_id}</div>
                  <div class="text-xs text-slate-500">{s.permission}</div>
                </div>
                <button
                  class="grid h-10 w-10 place-items-center rounded-md border text-base text-slate-700 hover:bg-slate-50"
                  type="button"
                  aria-label="Remove share"
                  title="Remove"
                  onclick={() => revokeShare(s.id)}
                  disabled={sharingBusy}
                >
                  ✕
                </button>
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <div class="flex gap-2">
        <button class="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white" type="button" onclick={save} disabled={saving}>
          Save
        </button>
        <button class="rounded-md border px-3 py-2 text-sm" type="button" onclick={toggleArchive}>
          {collection.archived ? 'Unarchive' : 'Archive'}
        </button>
        <div class="flex-1"></div>
        <button class="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" type="button" onclick={deleteCollection}>
          Delete
        </button>
      </div>
    </div>
  {/if}
</div>
