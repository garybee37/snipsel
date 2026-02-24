<script lang="ts">
  import { api, type Attachment, type Snipsel } from '../lib/api';
  import ImageModal from '../lib/ImageModal.svelte';
  import { collectionAnchor, currentView, isLoading, searchError, searchQuery, searchResults } from '../lib/stores';
  import { currentUser } from '../lib/session';
  import { getCurrentUrl } from '../lib/router';

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
	let loading = $state(true);
  let changingType = $state(false);

  let copied = $state(false);

  const DEFAULT_ACCENT = '#4f46e5';
  type Rgb = { r: number; g: number; b: number };

  function clampByte(n: number): number {
    return Math.max(0, Math.min(255, Math.round(n)));
  }

  function hexToRgb(hex: string): Rgb | null {
    const h = hex.trim();
    const m = /^#([0-9a-fA-F]{6})$/.exec(h);
    if (!m) return null;
    const v = m[1];
    return {
      r: parseInt(v.slice(0, 2), 16),
      g: parseInt(v.slice(2, 4), 16),
      b: parseInt(v.slice(4, 6), 16),
    };
  }

  function mixRgb(a: Rgb, b: Rgb, t: number): Rgb {
    const tt = Math.max(0, Math.min(1, t));
    return {
      r: clampByte(a.r + (b.r - a.r) * tt),
      g: clampByte(a.g + (b.g - a.g) * tt),
      b: clampByte(a.b + (b.b - a.b) * tt),
    };
  }

  function rgba(c: Rgb, alpha: number): string {
    const a = Math.max(0, Math.min(1, alpha));
    return `rgba(${c.r}, ${c.g}, ${c.b}, ${a})`;
  }

  function getAccent(): string {
    const raw = ($currentUser?.default_collection_header_color || '').trim() || DEFAULT_ACCENT;
    return /^#[0-9a-fA-F]{6}$/.test(raw) ? raw : DEFAULT_ACCENT;
  }

  function getAccentTint(): string {
    const base = { r: 255, g: 255, b: 255 };
    const accent = hexToRgb(getAccent());
    const mixed = accent ? mixRgb(base, accent, 0.14) : base;
    return rgba(mixed, 0.96);
  }

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
		};
      snipsel = res.snipsel;
      snipsel.tags = res.tags ?? [];
      snipsel.mentions = res.mentions ?? [];
		const nextPlacements = res.placements ?? [];
		placements = nextPlacements;
		void loadPlacementFavorites(nextPlacements);
		// backlinks currently unused in UI
	} finally {
		loading = false;
	}
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
    const raw = ($currentUser?.default_collection_header_color || '').trim() || '#4f46e5';
    const accent = /^#[0-9a-fA-F]{6}$/.test(raw) ? raw : '#4f46e5';
    // tinted background like the toolbox for readability
    const tokenBg = `rgba(255, 255, 255, 0.96)`;
    return escaped.replace(
      /(^|[^\w])(#[A-Za-z][\w-]*|@[A-Za-z][\w-]*)/g,
      (m, p1, token) =>
        `${p1}<mark class="snip-token" style="background-color:${tokenBg}; color:${accent}">${token}</mark>`
    );
  }

	function attachmentDownloadIcon() {
		return {
			__html:
				'<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>',
		};
	}

	function attachmentDeleteIcon() {
		return {
			__html:
				'<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M1 7h22m-5-3H6a1 1 0 00-1 1v2h14V5a1 1 0 00-1-1z" /></svg>',
		};
	}

	function favoriteIcon(filled: boolean) {
		return {
			__html: filled
				? '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M10 15l-5.878 3.09 1.122-6.545L.488 6.91l6.562-.955L10 .5l2.95 5.455 6.562.955-4.756 4.635 1.122 6.545z"/></svg>'
				: '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M10 1.2l2.86 5.3 6.03.88-4.36 4.25 1.03 6.01L10 14.9 4.44 17.64l1.03-6.01-4.36-4.25 6.03-.88L10 1.2z"/></svg>',
		};
	}

	function infoIcon() {
		return {
			__html:
				'<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M10 18a8 8 0 100-16 8 8 0 000 16z"/><path stroke-linecap="round" stroke-linejoin="round" d="M10 9v5"/><path stroke-linecap="round" stroke-linejoin="round" d="M10 6h.01"/></svg>',
		};
	}

	let favoriteByCollectionId = $state<Record<string, boolean>>({});

	async function loadPlacementFavorites(nextPlacements: Array<{ collection_id: string }>) {
		const ids = Array.from(new Set(nextPlacements.map((p) => p.collection_id)));
		if (ids.length === 0) return;

		const missing = ids.filter((id) => !(id in favoriteByCollectionId));
		if (missing.length === 0) return;

		try {
			const res = await api.collections.list(true);
			const wanted = new Set(missing);
			const next: Record<string, boolean> = {};
			for (const c of res.collections) {
				if (wanted.has(c.id)) next[c.id] = Boolean(c.is_favorite);
			}
			favoriteByCollectionId = { ...favoriteByCollectionId, ...next };
		} catch {
			// best-effort
		}
	}

	async function toggleCollectionFavorite(collectionId: string) {
		const current = Boolean(favoriteByCollectionId[collectionId]);
		const next = !current;
		favoriteByCollectionId = { ...favoriteByCollectionId, [collectionId]: next };
		try {
			if (next) {
				await api.collections.favorite(collectionId);
			} else {
				await api.collections.unfavorite(collectionId);
			}
		} catch {
			favoriteByCollectionId = { ...favoriteByCollectionId, [collectionId]: current };
		}
	}

	function openCollectionInfo(collectionId: string) {
		currentView.set({ type: 'collection_settings', id: collectionId });
	}

  async function deleteAttachment(attachmentId: string) {
    if (!confirm('Delete attachment?')) return;
    await api.attachments.delete(attachmentId);
    await load();
  }

  load();

	function directLinkUrl(): string {
		const u = new URL(window.location.href);
		u.searchParams.set('v', 'snipsel');
		u.searchParams.set('id', snipselId);
		// drop unrelated params
		u.searchParams.delete('sn');
		u.searchParams.delete('pos');
		u.searchParams.delete('q');
		u.searchParams.delete('returnTo');
		return u.toString();
	}

  async function copyDirectLink() {
    const text = directLinkUrl();
    try {
      await navigator.clipboard.writeText(text);
      copied = true;
      setTimeout(() => {
        copied = false;
      }, 1200);
    } catch {
      // fallback
      const el = document.getElementById('snipsel-direct-link') as HTMLInputElement | null;
      if (el) {
        el.focus();
        el.select();
      }
    }
  }

	function goBack() {
		const returnTo = ($currentView.type === 'snipsel' ? ($currentView as { returnTo?: string }).returnTo : undefined) ?? '';
		if (returnTo) {
			history.replaceState(null, '', returnTo);
			window.dispatchEvent(new PopStateEvent('popstate'));
			return;
		}

    // If we have browser history (e.g. came from search/collection), go back.
    // Otherwise fallback to collections.
    if (history.length > 1) {
      history.back();
      return;
    }

    // Ensure URL is in a sensible state even if history is not usable
    // (e.g. opened in a new tab).
    if (getCurrentUrl().includes('v=snipsel')) {
      currentView.set({ type: 'collections' });
      return;
    }

    currentView.set({ type: 'collections' });
  }
</script>

<div class="space-y-4">
  <div class="flex items-center justify-between gap-3">
    <button
      class="rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm ring-1 ring-black/5 backdrop-blur-md hover:bg-white"
      type="button"
      onclick={goBack}
      aria-label="Back"
      title="Back"
    >
      Back
    </button>

    <div
      class="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-sm font-medium shadow-sm ring-1 ring-black/5 backdrop-blur-md"
      style={`background-color: ${getAccentTint()}; color: ${getAccent()}`}
    >
      <span class="text-xs uppercase tracking-wide" style={`color: ${getAccent()}`}>Snipsel</span>
      <span class="opacity-70">·</span>
      <span class="font-semibold">{snipselId}</span>
    </div>
  </div>

  {#if loading}
    <div class="text-sm text-slate-500">Loading...</div>
  {:else if !snipsel}
    <div class="text-sm text-slate-500">Not found</div>
  {:else}
    <div class="space-y-3">

			
			<div class="rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md">
				<div class="flex items-center justify-between gap-2">
					<div class="text-xs uppercase text-slate-500">Type</div>
          {#if changingType}
            <div class="text-xs text-slate-500">Updating...</div>
          {/if}
        </div>
        <div class="mt-2 overflow-hidden rounded-full border border-slate-200 bg-white">
          <div class="grid grid-cols-4">
          <button
            class="px-4 py-3 text-sm font-medium transition-colors {snipsel.type === 'text' ? 'text-slate-900' : 'text-slate-600 hover:text-slate-900'}"
            type="button"
            onclick={() => setType('text')}
            disabled={changingType}
            style={snipsel.type === 'text' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            Note
          </button>
          <button
            class="border-l border-black/5 px-4 py-3 text-sm font-medium transition-colors {snipsel.type === 'image'
              ? 'text-slate-900'
              : 'text-slate-600 hover:text-slate-900'}"
            type="button"
            onclick={() => setType('image')}
            disabled={changingType}
            style={snipsel.type === 'image' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            Image
          </button>
          <button
            class="border-l border-black/5 px-4 py-3 text-sm font-medium transition-colors {snipsel.type === 'attachment'
              ? 'text-slate-900'
              : 'text-slate-600 hover:text-slate-900'}"
            type="button"
            onclick={() => setType('attachment')}
            disabled={changingType}
            style={snipsel.type === 'attachment' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            File
          </button>
          <button
            class="border-l border-black/5 px-4 py-3 text-sm font-medium transition-colors {snipsel.type === 'task'
              ? 'text-slate-900'
              : 'text-slate-600 hover:text-slate-900'}"
            type="button"
            onclick={() => setType('task')}
            disabled={changingType}
            style={snipsel.type === 'task' ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
          >
            Task
          </button>
				</div>
			</div>
		</div>
			
			<div class="rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md">
				<div class="text-xs uppercase text-slate-500">Timestamps</div>
				<div class="mt-2 space-y-1 text-sm text-slate-600">
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
					{#if snipsel.type === 'task' && snipsel.done_at}
						<div>
							<span class="font-medium">Done:</span>
							<span class="ml-1">{formatWhen(snipsel.done_at)}</span>
							{#if snipsel.done_by_username}
								<span class="ml-1 text-slate-500">by {snipsel.done_by_username}</span>
							{/if}
						</div>
					{/if}
				</div>
			</div>




    </div>

    {#if (snipsel.tags?.length ?? 0) > 0 || (snipsel.mentions?.length ?? 0) > 0}
      <div class="rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md">
        <div class="text-xs uppercase text-slate-500">Tags / Mentions</div>
        <div class="mt-2 flex flex-wrap gap-2">
            {#each snipsel.tags ?? [] as t (t)}
              <button
                type="button"
                class="rounded-full border bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                style={`background-color: rgba(255,255,255,0.92); color: ${/^#[0-9a-fA-F]{6}$/.test(($currentUser?.default_collection_header_color || '').trim() || '#4f46e5')
                  ? (($currentUser?.default_collection_header_color || '').trim() || '#4f46e5')
                  : '#4f46e5'}`}
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
                style={`background-color: rgba(255,255,255,0.92); color: ${/^#[0-9a-fA-F]{6}$/.test(($currentUser?.default_collection_header_color || '').trim() || '#4f46e5')
                  ? (($currentUser?.default_collection_header_color || '').trim() || '#4f46e5')
                  : '#4f46e5'}`}
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

    {#if hasGeo(snipsel)}
      <div class="rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md">
        <div class="text-xs uppercase text-slate-500">Location</div>
        <div class="mt-2 overflow-hidden rounded-md border border-black/5">
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

			<div class="rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md">
				<div class="text-xs uppercase text-slate-500">Attachments</div>
				{#if snipsel.attachments.length === 0}
					<div class="mt-2 text-sm text-slate-500">No attachments</div>
				{:else}
					<div class="mt-3 space-y-2">
						{#each snipsel.attachments as a}
							<div class="flex items-center gap-3 px-1 py-1">
								{#if isImageAttachment(a) && a.has_thumbnail}
									<button
										type="button"
										class="h-10 w-10 overflow-hidden rounded"
										aria-label={`View ${a.filename}`}
										onclick={() => openImageModal(a.id, a.filename)}
									>
										<img class="h-10 w-10 object-cover" src={api.attachments.thumbnailUrl(a.id)} alt={a.filename} loading="lazy" />
									</button>
								{:else if a.has_thumbnail}
									<img class="h-10 w-10 rounded object-cover" src={api.attachments.thumbnailUrl(a.id)} alt={a.filename} loading="lazy" />
								{:else}
									<div class="h-10 w-10 rounded bg-slate-100"></div>
								{/if}
								<div class="min-w-0 flex-1">
									<div class="truncate text-sm font-medium">{a.filename}</div>
									<div class="text-xs text-slate-500">{a.size_bytes} bytes</div>
								</div>
								<div class="flex items-center gap-1 rounded-full border border-slate-200 bg-white/80 p-1 shadow-sm ring-1 ring-black/5">
									<a
										class="grid h-9 w-9 place-items-center rounded-full text-slate-700 hover:bg-black/5"
										href={api.attachments.downloadUrl(a.id)}
										target="_blank"
										rel="noreferrer"
										aria-label="Download attachment"
										title="Download"
									>
										{@html attachmentDownloadIcon().__html}
									</a>
									<button
										class="grid h-9 w-9 place-items-center rounded-full text-slate-700 hover:bg-black/5"
										type="button"
										aria-label="Delete attachment"
										onclick={() => deleteAttachment(a.id)}
										title="Delete"
									>
										{@html attachmentDeleteIcon().__html}
									</button>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>

    <div class="rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md">
      <div class="text-xs uppercase text-slate-500">Placements</div>
      {#if placements.length === 0}
        <div class="mt-2 text-sm text-slate-500">Not in any collection</div>
      {:else}
		<div class="mt-2 flex flex-col gap-2">
			{#each placements as p}
				<div class="flex items-center justify-between gap-2">
					<button
						class="min-w-0 flex-1 text-left text-sm font-medium text-slate-700 hover:underline"
						type="button"
						onclick={() => {
							currentView.set({ type: 'collection', id: p.collection_id });
							collectionAnchor.set({ collectionId: p.collection_id, pos: p.position });
						}}
					>
						<span class="truncate">{p.collection_icon ? `${p.collection_icon} ` : ''}{p.collection_title ?? p.collection_id}</span>
					</button>
					<div class="flex items-center gap-1 rounded-full border border-slate-200 bg-white/80 p-1 shadow-sm ring-1 ring-black/5">
						<button
							class="grid h-9 w-9 place-items-center rounded-full text-slate-700 hover:bg-black/5"
							type="button"
							aria-label={(favoriteByCollectionId[p.collection_id] ?? false) ? 'Unfavorite collection' : 'Favorite collection'}
							title={(favoriteByCollectionId[p.collection_id] ?? false) ? 'Unfavorite' : 'Favorite'}
							onclick={() => toggleCollectionFavorite(p.collection_id)}
							style={(favoriteByCollectionId[p.collection_id] ?? false) ? `color: ${getAccent()}` : undefined}
						>
							{@html favoriteIcon(Boolean(favoriteByCollectionId[p.collection_id])).__html}
						</button>
						<button
							class="grid h-9 w-9 place-items-center rounded-full text-slate-700 hover:bg-black/5"
							type="button"
							aria-label="Collection info"
							title="Info"
							onclick={() => openCollectionInfo(p.collection_id)}
						>
							{@html infoIcon().__html}
						</button>
					</div>
				</div>
			{/each}
        </div>
      {/if}
    </div>

    <div class="rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm ring-1 ring-black/5 backdrop-blur-md">
      <div class="flex items-center justify-between gap-2">
        <div class="text-xs uppercase text-slate-500">Direct link</div>
        {#if copied}
          <div class="text-xs text-slate-500">Copied</div>
        {/if}
      </div>
      <div class="mt-2 flex items-center gap-2">
        <input
          id="snipsel-direct-link"
          class="min-w-0 flex-1 rounded-md border border-slate-200 bg-white/80 px-3 py-2 text-sm text-slate-700 shadow-sm ring-1 ring-black/5"
          readonly
          value={directLinkUrl()}
        />
        <div class="flex items-center gap-1 rounded-full border border-slate-200 bg-white/80 p-1 shadow-sm ring-1 ring-black/5">
          <button
            class="rounded-full px-4 py-2 text-sm font-medium text-slate-700 hover:bg-black/5"
            type="button"
            onclick={copyDirectLink}
            aria-label="Copy direct link"
            title="Copy"
          >
            Copy
          </button>
        </div>
      </div>
    </div>



			
  {/if}
</div>

<ImageModal
  attachmentId={modalImage?.id ?? null}
  filename={modalImage?.filename ?? ''}
  onClose={closeImageModal}
/>
