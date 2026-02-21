<script lang="ts">
  import { api, type Collection } from '../lib/api';
  import { collections, currentCollection, currentView, isLoading } from '../lib/stores';

  export let collectionId: string;

  let collection: Collection | null = null;
  let title = '';
  let icon = '';
  let headerImageUrl = '';
  let saving = false;

  async function load() {
    isLoading.set(true);
    try {
      const res = await api.collections.get(collectionId);
      collection = res.collection;
      title = collection.title;
      icon = collection.icon;
      headerImageUrl = collection.header_image_url ?? '';
    } finally {
      isLoading.set(false);
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

  async function deleteCollection() {
    if (!collection) return;
    if (!confirm('Delete collection?')) return;
    const id = collection.id;
    await api.collections.delete(id);
    collections.update((list) => list.filter((c) => c.id !== id));
    currentCollection.set(null);
    currentView.set({ type: 'collections' });
  }

  load();
</script>

<div class="space-y-3">
  <button class="text-sm text-slate-600 underline" type="button" on:click={() => currentView.set({ type: 'collections' })}>
    Back
  </button>

  <h2 class="text-lg font-semibold">Edit collection</h2>

  {#if !collection}
    <div class="text-sm text-slate-500">Loading...</div>
  {:else}
    <div class="rounded-lg border bg-white p-3 space-y-3">
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

      <div class="flex gap-2">
        <button class="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white" type="button" on:click={save} disabled={saving}>
          Save
        </button>
        <button class="rounded-md border px-3 py-2 text-sm" type="button" on:click={toggleArchive}>
          {collection.archived ? 'Unarchive' : 'Archive'}
        </button>
        <div class="flex-1"></div>
        <button class="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" type="button" on:click={deleteCollection}>
          Delete
        </button>
      </div>
    </div>
  {/if}
</div>
