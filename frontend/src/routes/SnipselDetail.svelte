<script lang="ts">
  import { api, type Attachment, type Snipsel } from '../lib/api';
  import ImageModal from '../lib/ImageModal.svelte';
  import { currentView, isLoading, searchError, searchQuery, searchResults } from '../lib/stores';

  interface Props {
    snipselId: string;
  }

  let { snipselId }: Props = $props();

  let snipsel = $state<Snipsel | null>(null);
  let placements = $state<Array<{
    collection_id: string;
    collection_title?: string;
    collection_icon?: string;
    position: number;
    indent: number;
  }>>([]);
  let backlinks = $state<Array<{ from_snipsel_id: string; to_snipsel_id: string }>>([]);
  let loading = $state(true);
  let changingType = $state(false);

  let modalImage = $state<{ id: string; filename: string } | null>(null);

  function openImageModal(id: string, filename: string) {
    modalImage = { id, filename };
  }

  function closeImageModal() {
    modalImage = null;
  }

  async function load() {
    loading = true;
    try {
      const res = (await fetch(`/api/snipsels/${snipselId}`, { credentials: 'include' }).then((r) => r.json())) as {
        snipsel: Snipsel;
        tags?: string[];
        mentions?: string[];
        placements?: Array<{ collection_id: string; position: number; indent: number }>;
        backlinks?: Array<{ from_snipsel_id: string; to_snipsel_id: string }>;
      };
      snipsel = res.snipsel;
      snipsel.tags = res.tags ?? [];
      snipsel.mentions = res.mentions ?? [];
      placements = res.placements ?? [];
      backlinks = res.backlinks ?? [];
    } finally {
      loading = false;
    }
  }

  async function setInternalLinkTarget(targetId: string) {
    await api.snipsels.update(snipselId, { type: 'link_internal', internal_target_snipsel_id: targetId });
    await load();
  }

  async function setType(nextType: 'text' | 'image' | 'attachment' | 'task') {
    if (!snipsel) return;
    if (snipsel.type === nextType) return;
    changingType = true;
    try {
      await api.snipsels.update(snipselId, { type: nextType });
      await load();
    } finally {
      changingType = false;
    }
  }

  function isImageAttachment(a: Attachment): boolean {
    return Boolean(a.mime_type?.startsWith('image/') || a.has_thumbnail);
  }

  function formatWhen(iso: string | null): string {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleString();
  }

  function hasGeo(s: Snipsel): boolean {
    return typeof s.geo_lat === 'number' && typeof s.geo_lng === 'number';
  }

  function osmEmbedUrl(lat: number, lng: number): string {
    const delta = 0.005;
    const bbox = `${lng - delta},${lat - delta},${lng + delta},${lat + delta}`;
    const marker = `${lat},${lng}`;
    return `https://www.openstreetmap.org/export/embed.html?bbox=${encodeURIComponent(bbox)}&layer=mapnik&marker=${encodeURIComponent(marker)}`;
  }

  function highlightTokens(text: string | null): string {
    if (!text) return '';
    const escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    return escaped.replace(
      /(^|[^\w])(#[A-Za-z][\w-]*|@[A-Za-z][\w-]*)/g,
      (m, p1, token) => `${p1}<mark class="snip-token">${token}</mark>`
    );
  }

  function attachmentDownloadIcon() {
    return {
      __html:
        '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>',
    };
  }

  async function deleteAttachment(attachmentId: string) {
    if (!confirm('Delete attachment?')) return;
    await api.attachments.delete(attachmentId);
    await load();
  }

  load();
</script>

<div class="space-y-5">
  <button class="text-sm text-slate-600 underline" type="button" onclick={() => currentView.set({ type: 'collections' })}>
    Back
  </button>

  {#if loading}
    <div class="text-sm text-slate-500">Loading...</div>
  {:else if !snipsel}
    <div class="text-sm text-slate-500">Not found</div>
  {:else}
    <div class="rounded-lg border bg-white p-5">
      <div class="text-xs uppercase text-slate-500">Snipsel</div>
      <div class="mt-1 text-base font-medium">{snipsel.type}</div>

      <div class="mt-3 flex items-center gap-2">
        <span class="text-base text-slate-500">Type</span>
        <div class="inline-flex overflow-hidden rounded-md border">
          <button
            class="px-4 py-3 text-lg {snipsel.type === 'text' ? 'bg-slate-100 font-medium' : 'bg-white'}"
            type="button"
            onclick={() => setType('text')}
            disabled={changingType}
          >
            Note
          </button>
          <button
            class="border-l px-4 py-3 text-lg {snipsel.type === 'image' ? 'bg-slate-100 font-medium' : 'bg-white'}"
            type="button"
            onclick={() => setType('image')}
            disabled={changingType}
          >
            Image
          </button>
          <button
            class="border-l px-4 py-3 text-lg {snipsel.type === 'attachment' ? 'bg-slate-100 font-medium' : 'bg-white'}"
            type="button"
            onclick={() => setType('attachment')}
            disabled={changingType}
          >
            File
          </button>
          <button
            class="border-l px-4 py-3 text-lg {snipsel.type === 'task' ? 'bg-slate-100 font-medium' : 'bg-white'}"
            type="button"
            onclick={() => setType('task')}
            disabled={changingType}
          >
            Task
          </button>
        </div>
      </div>

      <div class="mt-3 rounded-md bg-slate-50 px-4 py-3 text-base text-slate-600">
        <div class="flex flex-wrap gap-x-4 gap-y-1">
          <div>
            <span class="font-medium">Created:</span>
            <span class="ml-1">{formatWhen(snipsel.created_at)}</span>
            {#if snipsel.created_by_username}
              <span class="ml-1 text-slate-500">by {snipsel.created_by_username}</span>
            {/if}
          </div>
          <div>
            <span class="font-medium">Modified:</span>
            <span class="ml-1">{formatWhen(snipsel.modified_at)}</span>
            {#if snipsel.modified_by_username}
              <span class="ml-1 text-slate-500">by {snipsel.modified_by_username}</span>
            {/if}
          </div>
        </div>

        {#if snipsel.type === 'task' && snipsel.done_at}
          <div class="mt-1">
            <span class="font-medium">Done:</span>
            <span class="ml-1">{formatWhen(snipsel.done_at)}</span>
            {#if snipsel.done_by_username}
              <span class="ml-1 text-slate-500">by {snipsel.done_by_username}</span>
            {/if}
          </div>
        {/if}
      </div>

      <div class="mt-4 whitespace-pre-wrap text-lg text-slate-700">{@html highlightTokens(snipsel.content_markdown)}</div>
    </div>

    {#if (snipsel.tags?.length ?? 0) > 0 || (snipsel.mentions?.length ?? 0) > 0}
      <div class="rounded-lg border bg-white p-3">
        <div class="text-xs uppercase text-slate-500">Tags / Mentions</div>
        <div class="mt-2 flex flex-wrap gap-2">
          {#each snipsel.tags ?? [] as t (t)}
            <button
              type="button"
              class="rounded-full border bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              onclick={() => {
                currentView.set({ type: 'search' });
                searchQuery.set('');
                api.search({ tag: t }).then(searchResults.set).catch(() => searchError.set('Search failed'));
              }}
            >
              #{t}
            </button>
          {/each}
          {#each snipsel.mentions ?? [] as m (m)}
            <button
              type="button"
              class="rounded-full border bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              onclick={() => {
                currentView.set({ type: 'search' });
                searchQuery.set('');
                api.search({ mention: m }).then(searchResults.set).catch(() => searchError.set('Search failed'));
              }}
            >
              @{m}
            </button>
          {/each}
        </div>
      </div>
    {/if}

    <div class="rounded-lg border bg-white p-3">
      <div class="text-xs uppercase text-slate-500">Attachments</div>

      {#if snipsel.attachments.length === 0}
        <div class="mt-2 text-sm text-slate-500">No attachments</div>
      {:else}
        {#if snipsel.type === 'image'}
          {@const images = snipsel.attachments.filter(isImageAttachment)}
          {@const others = snipsel.attachments.filter((a) => !isImageAttachment(a))}

          {#if images.length === 0}
            <div class="mt-2 text-sm text-slate-500">No image attachments</div>
          {:else}
            <div class="mt-3 grid grid-cols-3 gap-2">
              {#each images as a}
                <button
                  type="button"
                  class="block overflow-hidden rounded-md border bg-slate-50"
                  aria-label={`View ${a.filename}`}
                  onclick={() => openImageModal(a.id, a.filename)}
                >
                  <img
                    class="h-24 w-full object-cover"
                    src={a.has_thumbnail ? api.attachments.thumbnailUrl(a.id) : api.attachments.downloadUrl(a.id)}
                    alt={a.filename}
                    loading="lazy"
                  />
                </button>
              {/each}
            </div>
          {/if}

          {#if others.length > 0}
            <div class="mt-3 space-y-2">
              {#each others as a}
                <div class="flex items-center gap-2 rounded-md border px-3 py-2">
                  <span class="text-lg" aria-hidden="true">📄</span>
                  <div class="flex-1">
                    <div class="text-sm font-medium">{a.filename}</div>
                    <div class="text-xs text-slate-500">{a.size_bytes} bytes</div>
                  </div>
                  <a
                    class="grid h-9 w-9 place-items-center rounded-md text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    href={api.attachments.downloadUrl(a.id)}
                    target="_blank"
                    rel="noreferrer"
                    aria-label="Download attachment"
                    title="Download"
                  >
                    {@html attachmentDownloadIcon().__html}
                  </a>
                  <button class="ml-1 grid h-9 w-9 place-items-center rounded-md hover:bg-slate-50" type="button" aria-label="Delete attachment" onclick={() => deleteAttachment(a.id)}>
                    🗑
                  </button>
                </div>
              {/each}
            </div>
          {/if}
        {:else if snipsel.type === 'attachment'}
          {@const images = snipsel.attachments.filter(isImageAttachment)}
          {@const others = snipsel.attachments.filter((a) => !isImageAttachment(a))}

          {#if images.length > 0}
            <div class="mt-3 grid grid-cols-3 gap-2">
              {#each images as a}
                <button
                  type="button"
                  class="block overflow-hidden rounded-md border bg-slate-50"
                  aria-label={`View ${a.filename}`}
                  onclick={() => openImageModal(a.id, a.filename)}
                >
                  <img
                    class="h-24 w-full object-cover"
                    src={a.has_thumbnail ? api.attachments.thumbnailUrl(a.id) : api.attachments.downloadUrl(a.id)}
                    alt={a.filename}
                    loading="lazy"
                  />
                </button>
              {/each}
            </div>
          {/if}

          {#if others.length > 0}
            <div class="mt-3 space-y-2">
              {#each others as a}
                <div class="flex items-center gap-2 rounded-md border px-3 py-2">
                  <span class="text-lg" aria-hidden="true">📎</span>
                  <div class="flex-1">
                    <div class="text-sm font-medium">{a.filename}</div>
                    <div class="text-xs text-slate-500">{a.size_bytes} bytes</div>
                  </div>
                  <a
                    class="grid h-9 w-9 place-items-center rounded-md text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    href={api.attachments.downloadUrl(a.id)}
                    target="_blank"
                    rel="noreferrer"
                    aria-label="Download attachment"
                    title="Download"
                  >
                    {@html attachmentDownloadIcon().__html}
                  </a>
                  <button class="ml-1 grid h-9 w-9 place-items-center rounded-md hover:bg-slate-50" type="button" aria-label="Delete attachment" onclick={() => deleteAttachment(a.id)}>
                    🗑
                  </button>
                </div>
              {/each}
            </div>
          {/if}
        {:else}
          <div class="mt-3 space-y-2">
            {#each snipsel.attachments as a}
              <div class="flex items-center gap-3 rounded-md border px-3 py-2">
                {#if a.has_thumbnail}
                  <img class="h-10 w-10 rounded object-cover" src={api.attachments.thumbnailUrl(a.id)} alt={a.filename} />
                {:else}
                  <div class="h-10 w-10 rounded bg-slate-100"></div>
                {/if}
                <div class="flex-1">
                  <div class="text-sm font-medium">{a.filename}</div>
                  <div class="text-xs text-slate-500">{a.size_bytes} bytes</div>
                </div>
                <a
                  class="grid h-9 w-9 place-items-center rounded-md text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  href={api.attachments.downloadUrl(a.id)}
                  target="_blank"
                  rel="noreferrer"
                  aria-label="Download attachment"
                  title="Download"
                >
                  {@html attachmentDownloadIcon().__html}
                </a>
                <button class="ml-1 grid h-9 w-9 place-items-center rounded-md hover:bg-slate-50" type="button" aria-label="Delete attachment" onclick={() => deleteAttachment(a.id)}>
                  🗑
                </button>
              </div>
            {/each}
          </div>
        {/if}
      {/if}
    </div>

    <div class="rounded-lg border bg-white p-3">
      <div class="text-xs uppercase text-slate-500">Placements</div>
      {#if placements.length === 0}
        <div class="mt-2 text-sm text-slate-500">Not in any collection</div>
      {:else}
        <div class="mt-2 space-y-1">
          {#each placements as p}
            <button
              class="text-left text-sm underline"
              type="button"
              onclick={() => currentView.set({ type: 'collection', id: p.collection_id })}
            >
              {p.collection_icon ? `${p.collection_icon} ` : ''}{p.collection_title ?? p.collection_id} (pos {p.position}, indent {p.indent})
            </button>
          {/each}
        </div>
      {/if}
    </div>

    {#if hasGeo(snipsel)}
      <div class="rounded-lg border bg-white p-3">
        <div class="text-xs uppercase text-slate-500">Location</div>
        <div class="mt-2 overflow-hidden rounded-md border">
          <iframe
            class="h-64 w-full"
            title="OpenStreetMap"
            src={osmEmbedUrl(snipsel.geo_lat ?? 0, snipsel.geo_lng ?? 0)}
            loading="lazy"
          ></iframe>
        </div>
        <div class="mt-2 text-sm text-slate-500">
          {snipsel.geo_lat?.toFixed(5)}, {snipsel.geo_lng?.toFixed(5)}
          {#if typeof snipsel.geo_accuracy_m === 'number'}
            · ±{Math.round(snipsel.geo_accuracy_m)}m
          {/if}
        </div>
      </div>
    {/if}

    <div class="rounded-lg border bg-white p-3">
      <div class="text-xs uppercase text-slate-500">Backlinks</div>
      {#if backlinks.length === 0}
        <div class="mt-2 text-sm text-slate-500">No backlinks</div>
      {:else}
        <div class="mt-2 space-y-1">
          {#each backlinks as b}
            <button
              class="text-left text-sm underline"
              type="button"
              onclick={() => currentView.set({ type: 'snipsel', id: b.from_snipsel_id })}
            >
              {b.from_snipsel_id}
            </button>
          {/each}
        </div>
      {/if}
    </div>

    <div class="rounded-lg border bg-white p-3">
      <div class="text-xs uppercase text-slate-500">Internal link</div>
      <div class="mt-2 flex gap-2">
        <input class="flex-1 rounded-md border px-3 py-2 text-sm" placeholder="Target snipsel id" onkeydown={(e) => {
          if (e.key === 'Enter') {
            const v = (e.currentTarget as HTMLInputElement).value.trim();
            if (v) setInternalLinkTarget(v);
          }
        }} />
      </div>
      {#if snipsel.internal_target_snipsel_id}
        <div class="mt-2 text-sm text-slate-600">Target: {snipsel.internal_target_snipsel_id}</div>
      {/if}
    </div>
  {/if}
</div>

<ImageModal
  attachmentId={modalImage?.id ?? null}
  filename={modalImage?.filename ?? ''}
  onClose={closeImageModal}
/>
