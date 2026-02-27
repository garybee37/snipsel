<script lang="ts">
  import { api, type SearchSnipselHit } from '../lib/api';
  import { collectionAnchor, currentView, isLoading } from '../lib/stores';
  import { currentUser } from '../lib/session';
  import { getCurrentUrl } from '../lib/router';

	let items = $state<SearchSnipselHit[]>([]);
	let showDone = $state(false);

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
    const isDark = document.documentElement.classList.contains('dark');
    const baseColor = isDark ? '#1e293b' : '#ffffff';
    const base = hexToRgb(baseColor) ?? { r: 255, g: 255, b: 255 };
    const accent = hexToRgb(getAccent());
    const mixed = accent ? mixRgb(base, accent, 0.14) : base;
    return rgba(mixed, 0.96);
  }

	async function load() {
		isLoading.set(true);
		try {
			const mentionName = ($currentUser?.username || '').trim();
			const res = await api.search({
				type: 'task',
				mentions_me: Boolean(mentionName),
				task_done: showDone,
			});
			items = res.snipsels;
		} finally {
			isLoading.set(false);
		}
	}

	$effect(() => {
		const uname = ($currentUser?.username || '').trim();
		void uname;
		void showDone;
		load();
	});

	async function toggleDone(id: string, current: boolean) {
		collectionAnchor.set(null);
		await api.snipsels.update(id, { task_done: !current });
		await load();
	}

  function openInfo(id: string) {
    collectionAnchor.set(null);
    currentView.set({ type: 'snipsel', id, returnTo: getCurrentUrl() });
  }

	function openInCollection(t: SearchSnipselHit) {
		const hasAccess = t.has_collection_access !== false;
		if (!hasAccess) {
			openInfo(t.id);
			return;
		}
		const collectionId = (t.collection_id ?? '').trim();
		if (!collectionId) {
			openInfo(t.id);
			return;
		}
    currentView.set({ type: 'collection', id: collectionId });
    const pos = typeof t.position === 'number' ? t.position : undefined;
    if (pos) {
      collectionAnchor.set({ collectionId, pos });
    } else {
      collectionAnchor.set({ collectionId, snipselId: t.id });
    }
  }

	// loaded via $effect
</script>

<div class="space-y-4">
	<h2 class="flex items-center gap-2 text-2xl font-semibold dark:text-slate-100">
    <svg class="h-6 w-6 text-slate-700 dark:text-slate-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M9 11l3 3L22 4" />
      <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
    </svg>
    <span>Todos</span>
	</h2>

	<div class="overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900 dark:ring-white/10">
		<div class="grid grid-cols-2 divide-x divide-black/5 dark:divide-white/5">
			<button
				class="px-4 py-3 text-sm font-medium transition-colors {showDone
					? 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'
					: 'text-slate-900 dark:text-white'}"
				type="button"
				onclick={() => (showDone = false)}
				style={!showDone ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
			>
				Open
			</button>
			<button
				class="px-4 py-3 text-sm font-medium transition-colors {showDone
					? 'text-slate-900 dark:text-white'
					: 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
				type="button"
				onclick={() => (showDone = true)}
				style={showDone ? `background-color: ${getAccentTint()}; color: ${getAccent()}` : undefined}
			>
				Done
			</button>
		</div>
	</div>

	{#if items.length === 0}
		<div class="py-8 text-center text-sm text-slate-500">No {showDone ? 'done' : 'open'} tasks</div>
	{:else}
    <div class="space-y-2">
		{#each items as t}
			{@const hasAccess = t.has_collection_access !== false}
			{@const canToggle = t.can_toggle_task_done === true}
			<div class="flex w-full items-center gap-3 px-1 py-2">
				<button
					class="grid h-8 w-8 place-items-center rounded-full border border-slate-300 bg-white disabled:opacity-40 dark:border-white/20 dark:bg-slate-900"
					type="button"
					aria-label={t.task_done ? 'Mark open' : 'Mark done'}
					title={t.task_done ? 'Open' : 'Done'}
					disabled={!canToggle}
					style={canToggle ? `border-color: ${getAccent()}` : undefined}
					onclick={() => toggleDone(t.id, t.task_done)}
				>
					{#if t.task_done}
						<span class="text-sm font-semibold" style={`color: ${getAccent()}`}>✓</span>
					{/if}
				</button>

				<button class="min-w-0 flex flex-1 items-start gap-3 text-left" type="button" onclick={() => openInCollection(t)}>
					<div class="min-w-0 flex-1">
						<div class="truncate text-lg font-medium text-slate-900 dark:text-slate-100">{t.content_markdown ?? ''}</div>
						<div class="mt-0.5 flex flex-wrap items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
							<span class="rounded px-1.5 py-0.5" style={`background-color: ${getAccentTint()}; color: ${getAccent()}`}>
								{#if hasAccess}
									{t.collection_icon ? `${t.collection_icon} ` : ''}{t.collection_title ?? 'Collection'}
								{:else}
									Restricted
								{/if}
							</span>
						</div>
					</div>
				</button>

          <div class="overflow-hidden rounded-full border border-slate-200 bg-white shadow-sm ring-1 ring-black/5 dark:border-white/10 dark:bg-slate-900 dark:ring-white/10">
            <div class="flex">
              <button
                class="grid h-11 w-12 place-items-center text-lg text-slate-700 hover:bg-black/5 dark:text-slate-400 dark:hover:bg-white/5"
                type="button"
                aria-label="Info"
                title="Info"
                onclick={() => openInfo(t.id)}
              >
                ⓘ
              </button>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
