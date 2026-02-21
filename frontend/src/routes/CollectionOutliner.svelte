<script lang="ts">
  import MarkdownIt from 'markdown-it';
  import { api, type Attachment, type CollectionItem } from '../lib/api';
  import ImageModal from '../lib/ImageModal.svelte';
  import {
    collectionItems,
    currentCollection,
    currentView,
    editingSnipselId,
    isLoading,
    newSnipselRequest,
    pendingReference,
    sortedItems,
  } from '../lib/stores';
  import { currentUser } from '../lib/session';

  const md = new MarkdownIt({ html: false, linkify: true, breaks: true });

  let textareaRef: HTMLTextAreaElement | undefined = $state();
  let editContainerRef: HTMLDivElement | undefined = $state();
  let focusProxyRef: HTMLInputElement | undefined = $state();
  let editContent = $state('');
  let editIndent = $state(0);
  let saving = $state(false);

  let selectedIds = $state<Set<string>>(new Set());

  let modalImage = $state<{ id: string; filename: string } | null>(null);

  let showTypeMenu = $state(false);

  const DEFAULT_HEADER_COLOR = '#4f46e5';

  function getHeaderColor(): string {
    return (
      $currentCollection?.header_color ??
      $currentUser?.default_collection_header_color ??
      DEFAULT_HEADER_COLOR
    );
  }

  function openImageModal(id: string, filename: string) {
    modalImage = { id, filename };
  }

  function closeImageModal() {
    modalImage = null;
  }

  function closeTypeMenu() {
    showTypeMenu = false;
  }

  function toggleSelection(id: string) {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    selectedIds = next;
  }

  function clearSelection() {
    selectedIds = new Set();
  }

  function openDetail(id: string) {
    currentView.set({ type: 'snipsel', id });
  }

  async function toggleTaskDone(item: CollectionItem) {
    if (!$currentCollection) return;
    if (item.snipsel.type !== 'task') return;

    const nextDone = !item.snipsel.task_done;
    await api.snipsels.update(item.snipsel_id, { task_done: nextDone });
    collectionItems.update((items) =>
      items.map((i) => (i.snipsel_id === item.snipsel_id ? { ...i, snipsel: { ...i.snipsel, task_done: nextDone } } : i))
    );
  }

  function openDetailSelected() {
    if (selectedIds.size === 0) return;
    const id = Array.from(selectedIds)[0];
    if (id) openDetail(id);
  }

  async function loadItems() {
    if (!$currentCollection) return;
    isLoading.set(true);
    try {
      const res = await api.snipsels.list($currentCollection.id);
      collectionItems.set(res.items);
    } finally {
      isLoading.set(false);
    }
  }

  function startEdit(item: CollectionItem) {
    if (selectedIds.size > 0) {
      toggleSelection(item.snipsel_id);
      return;
    }
    editingSnipselId.set(item.snipsel_id);
    editContent = item.snipsel.content_markdown || '';
    editIndent = item.indent;
    setTimeout(() => {
      textareaRef?.focus();
      autosizeTextarea();
    }, 0);
  }

  async function saveEdit() {
    const snipselId = $editingSnipselId;
    if (!snipselId || !$currentCollection) return;
    saving = true;
    try {
      const currentItem = $collectionItems.find((i) => i.snipsel_id === snipselId);
      const hasAttachments = (currentItem?.snipsel.attachments?.length ?? 0) > 0;
      const isEmpty = editContent.trim().length === 0;

      if (isEmpty && !hasAttachments) {
        await api.snipsels.delete($currentCollection.id, snipselId);
        collectionItems.update((items) => items.filter((i) => i.snipsel_id !== snipselId));
        return;
      }

      await api.snipsels.update(snipselId, { content_markdown: isEmpty ? null : editContent });

      if (currentItem && currentItem.indent !== editIndent) {
        const items = $sortedItems.map((i, idx) => ({
          snipsel_id: i.snipsel_id,
          position: idx + 1,
          indent: i.snipsel_id === snipselId ? editIndent : i.indent,
        }));
        await api.snipsels.reorder($currentCollection.id, items);
      }

      await loadItems();
    } finally {
      saving = false;
      editingSnipselId.set(null);
    }
  }

  function cancelEdit() {
    editingSnipselId.set(null);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Tab') {
      e.preventDefault();
      if (e.shiftKey) {
        editIndent = Math.max(0, editIndent - 1);
      } else {
        editIndent = Math.min(6, editIndent + 1);
      }
    } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      saveEdit();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      cancelEdit();
    }
  }

  function autosizeTextarea() {
    const el = textareaRef;
    if (!el) return;
    el.style.height = '0px';
    el.style.height = `${el.scrollHeight}px`;
  }

  function handleEditFocusOut(e: FocusEvent) {
    const related = e.relatedTarget as Node | null;
    if (related && editContainerRef?.contains(related)) return;
    if (!saving) saveEdit();
  }

  async function createSnipsel() {
    if (!$currentCollection) return;
    isLoading.set(true);
    try {
      const res = await api.snipsels.create($currentCollection.id, { type: 'text' });
      collectionItems.update((items) => [...items, res.item]);
      startEdit(res.item);
    } finally {
      isLoading.set(false);
    }
  }

  async function createSnipselFromUserGesture() {
    focusProxyRef?.focus();
    await createSnipsel();
    focusProxyRef?.blur();
  }

  $effect(() => {
    if ($newSnipselRequest > 0 && $currentCollection) {
      createSnipsel();
    }
  });

  async function deleteSelected() {
    if (!$currentCollection) return;
    if (selectedIds.size === 0) return;
    if (!confirm(`Delete ${selectedIds.size} snipsel(s)?`)) return;

    isLoading.set(true);
    try {
      const ids = Array.from(selectedIds);
      for (const id of ids) {
        await api.snipsels.delete($currentCollection.id, id);
      }
      collectionItems.update((items) => items.filter((i) => !selectedIds.has(i.snipsel_id)));
      clearSelection();
    } finally {
      isLoading.set(false);
    }
  }

  async function setTypeSelected(nextType: 'text' | 'image' | 'attachment' | 'task') {
    if (selectedIds.size === 0) return;

    isLoading.set(true);
    try {
      const ids = Array.from(selectedIds);
      for (const id of ids) {
        await api.snipsels.update(id, { type: nextType });
      }
      await loadItems();
      closeTypeMenu();
    } finally {
      isLoading.set(false);
    }
  }

  async function copySelected() {
    if (!$currentCollection) return;
    if (selectedIds.size === 0) return;

    isLoading.set(true);
    try {
      const ids = Array.from(selectedIds);
      for (const id of ids) {
        const res = await api.snipsels.copy($currentCollection.id, id);
        collectionItems.update((items) => [...items, res.item]);
      }
      clearSelection();
    } finally {
      isLoading.set(false);
    }
  }

  function addSelectedToCollection() {
    if (selectedIds.size === 0) return;
    pendingReference.set({ snipselIds: Array.from(selectedIds) });
    clearSelection();
    currentView.set({ type: 'collections' });
  }

  async function adjustIndentSelected(delta: number) {
    if (!$currentCollection) return;
    if (selectedIds.size === 0) return;

    const current = $sortedItems;
    const updated = current.map((i) => {
      if (!selectedIds.has(i.snipsel_id)) return i;
      const indent = Math.max(0, Math.min(6, i.indent + delta));
      return { ...i, indent };
    });

    const payload = updated.map((i, idx) => ({
      snipsel_id: i.snipsel_id,
      position: idx + 1,
      indent: i.indent,
    }));

    await api.snipsels.reorder($currentCollection.id, payload);
    collectionItems.set(updated.map((i, idx) => ({ ...i, position: idx + 1 })));
  }

  async function moveSelected(dir: -1 | 1) {
    if (!$currentCollection) return;
    if (selectedIds.size === 0) return;
    const list = [...$sortedItems];

    const indices = list
      .map((i, idx) => ({ id: i.snipsel_id, idx }))
      .filter((x) => selectedIds.has(x.id))
      .map((x) => x.idx);

    if (dir === -1) {
      for (const idx of indices.sort((a, b) => a - b)) {
        if (idx === 0) continue;
        const tmp = list[idx - 1];
        list[idx - 1] = list[idx];
        list[idx] = tmp;
      }
    } else {
      for (const idx of indices.sort((a, b) => b - a)) {
        if (idx === list.length - 1) continue;
        const tmp = list[idx + 1];
        list[idx + 1] = list[idx];
        list[idx] = tmp;
      }
    }

    const payload = list.map((i, index) => ({
      snipsel_id: i.snipsel_id,
      position: index + 1,
      indent: i.indent,
    }));

    await api.snipsels.reorder($currentCollection.id, payload);
    collectionItems.set(list.map((i, index) => ({ ...i, position: index + 1 })));
  }

  function renderMarkdown(text: string | null): string {
    if (!text) return '';
    return md.render(text);
  }

  function isImageAttachment(a: Attachment): boolean {
    return Boolean(a.mime_type?.startsWith('image/') || a.has_thumbnail);
  }

  $effect(() => {
    if ($currentCollection) {
      loadItems();
    }
  });

  $effect(() => {
    void editContent;
    autosizeTextarea();
  });
</script>

<div class="space-y-3">
  <input
    bind:this={focusProxyRef}
    class="pointer-events-none absolute left-0 top-0 h-0 w-0 opacity-0"
    tabindex="-1"
    aria-hidden="true"
  />

  <div class="overflow-hidden rounded-xl border border-slate-200 bg-white">
    <div
      class="relative h-28 w-full bg-cover bg-center"
      style={$currentCollection?.header_image_url
        ? `background-image: url('${$currentCollection.header_image_url}'); background-color: ${getHeaderColor()}`
        : `background-color: ${getHeaderColor()}`}
    ></div>

    <div class="relative px-4 py-3">
      <div
        class="absolute left-4 top-0 -translate-y-1/2 grid h-16 w-16 place-items-center rounded-xl border border-slate-200 bg-white shadow-sm"
        aria-hidden="true"
      >
        <span class="text-4xl leading-none">{$currentCollection?.icon}</span>
      </div>

      <button
        class="pl-20 text-lg font-semibold hover:underline"
        type="button"
        onclick={() => $currentCollection && currentView.set({ type: 'collection_settings', id: $currentCollection.id })}
      >
        {$currentCollection?.title}
      </button>
    </div>
  </div>

  {#if $isLoading && $sortedItems.length === 0}
    <div class="py-8 text-center text-sm text-slate-500">Loading...</div>
  {:else if $sortedItems.length === 0}
    <div class="py-8 text-center text-sm text-slate-500">No snipsels yet</div>
  {:else}
    <div class="flex flex-col">
      {#each $sortedItems as item (item.snipsel_id)}
        <div class="group relative pl-6 pr-10" style="margin-left: {item.indent * 1.25}rem">
          {#if item.snipsel_id === $editingSnipselId}
            <div
              bind:this={editContainerRef}
              class="rounded-lg bg-slate-50 px-4 py-3 ring-1 ring-indigo-200 shadow-sm"
              onfocusout={handleEditFocusOut}
            >
              <textarea
                bind:this={textareaRef}
                class="w-full resize-none bg-transparent text-lg outline-none"
                rows="1"
                bind:value={editContent}
                oninput={autosizeTextarea}
                onkeydown={handleKeydown}
              ></textarea>
            </div>
          {:else}
            {#if item.snipsel.type === 'task'}
              <button
                type="button"
                aria-label={item.snipsel.task_done ? 'Mark task not done' : 'Mark task done'}
                class="absolute left-1 top-1/2 -translate-y-1/2 h-7 w-7 rounded border border-slate-300 bg-white"
                onclick={(e) => {
                  e.stopPropagation();
                  toggleTaskDone(item);
                }}
              >
                {#if item.snipsel.task_done}
                  <span class="block h-full w-full rounded bg-indigo-600"></span>
                {/if}
              </button>

              <button
                type="button"
                aria-label="Select snipsel"
                class="absolute right-1 top-1/2 -translate-y-1/2 grid h-7 w-7 place-items-center rounded border border-slate-200 bg-white text-base leading-none transition-opacity {selectedIds.has(
                  item.snipsel_id
                )
                  ? 'opacity-100'
                  : 'opacity-0 group-hover:opacity-100'}"
                onclick={(e) => {
                  e.stopPropagation();
                  toggleSelection(item.snipsel_id);
                }}
              >
                {#if selectedIds.has(item.snipsel_id)}
                  ✓
                {/if}
              </button>
            {:else}
              <button
                type="button"
                aria-label="Select snipsel"
                class="absolute right-1 top-1/2 -translate-y-1/2 grid h-7 w-7 place-items-center rounded border border-slate-200 bg-white text-base leading-none transition-opacity {selectedIds.has(
                  item.snipsel_id
                )
                  ? 'opacity-100'
                  : 'opacity-0 group-hover:opacity-100'}"
                onclick={(e) => {
                  e.stopPropagation();
                  toggleSelection(item.snipsel_id);
                }}
              >
                {#if selectedIds.has(item.snipsel_id)}
                  ✓
                {/if}
              </button>
            {/if}

            <div
              class="rounded px-4 py-3 {selectedIds.has(item.snipsel_id)
                ? 'bg-slate-100'
                : 'hover:bg-slate-50'}"
              role="button"
              tabindex="0"
              onclick={() => startEdit(item)}
              onkeydown={(e) => e.key === 'Enter' && startEdit(item)}
            >
              {#if item.snipsel.content_markdown}
                  <div class="prose prose-sm max-w-none text-lg prose-p:my-0 prose-ul:my-2 prose-ol:my-2 prose-li:my-1 prose-headings:my-2 prose-h1:text-xl prose-h2:text-xl prose-h3:text-lg">
                    {@html renderMarkdown(item.snipsel.content_markdown)}
                  </div>
              {:else}
                <span class="text-sm italic text-slate-400">Empty snipsel</span>
              {/if}

              {#if item.snipsel.attachments.length > 0 && item.snipsel.type === 'image'}
                {@const images = item.snipsel.attachments.filter(isImageAttachment)}
                {@const others = item.snipsel.attachments.filter((a) => !isImageAttachment(a))}

                {#if images.length > 0}
                  <div class="mt-3 grid grid-cols-3 gap-2">
                    {#each images.slice(0, 9) as a}
                      <button
                        type="button"
                        class="aspect-square w-full overflow-hidden rounded-lg border bg-slate-50"
                        aria-label={`View ${a.filename}`}
                        onclick={(e) => {
                          e.stopPropagation();
                          openImageModal(a.id, a.filename);
                        }}
                      >
                        <img
                          class="h-full w-full object-cover"
                          src={a.has_thumbnail ? api.attachments.thumbnailUrl(a.id) : api.attachments.downloadUrl(a.id)}
                          alt={a.filename}
                          loading="lazy"
                        />
                      </button>
                    {/each}
                  </div>
                  {#if images.length > 9}
                    <div class="mt-2 text-sm text-slate-400">+{images.length - 9} more</div>
                  {/if}
                {/if}

                {#if others.length > 0}
                  <div class="mt-2 space-y-1">
                    {#each others.slice(0, 3) as a}
                      <a
                        class="flex items-center gap-2 rounded-md border bg-white px-2 py-1 text-xs"
                        href={api.attachments.downloadUrl(a.id)}
                        target="_blank"
                        rel="noreferrer"
                        onclick={(e) => e.stopPropagation()}
                      >
                        <span class="text-sm" aria-hidden="true">📄</span>
                        <span class="min-w-0 flex-1 truncate">{a.filename}</span>
                      </a>
                    {/each}
                    {#if others.length > 3}
                      <div class="text-[11px] text-slate-400">+{others.length - 3} more files</div>
                    {/if}
                  </div>
                {/if}
              {:else if item.snipsel.attachments.length > 0 && item.snipsel.type === 'attachment'}
                <div class="mt-2 space-y-1">
                  {#each item.snipsel.attachments.slice(0, 3) as a}
                    <a
                      class="flex items-center gap-2 rounded-md border bg-white px-2 py-1 text-xs"
                      href={api.attachments.downloadUrl(a.id)}
                      target="_blank"
                      rel="noreferrer"
                      onclick={(e) => e.stopPropagation()}
                    >
                      <span class="text-sm" aria-hidden="true">📎</span>
                      <span class="min-w-0 flex-1 truncate">{a.filename}</span>
                    </a>
                  {/each}
                  {#if item.snipsel.attachments.length > 3}
                    <div class="text-[11px] text-slate-400">+{item.snipsel.attachments.length - 3} more files</div>
                  {/if}
                </div>
              {:else if item.snipsel.attachments.length > 0}
                <div class="mt-1 flex items-center gap-1 text-[11px] text-slate-400">
                  <span aria-hidden="true">📎</span>
                  <span>{item.snipsel.attachments.length}</span>
                </div>
              {/if}
            </div>
          {/if}
        </div>
      {/each}

      <button
        class="mt-6 h-24 w-full rounded-lg border border-dashed border-slate-200 bg-slate-50/50 text-left text-base text-slate-400 hover:bg-slate-50"
        type="button"
        aria-label="Add new snipsel"
        onclick={() => {
          if (selectedIds.size > 0) {
            clearSelection();
            return;
          }
          createSnipselFromUserGesture();
        }}
      ></button>
    </div>
  {/if}

  {#if selectedIds.size > 0}
    <div class="fixed bottom-20 left-0 right-0 z-20 px-4 pb-4">
      <div class="mx-auto flex max-w-3xl flex-wrap items-center justify-center gap-2 rounded-xl bg-slate-900 px-3 py-3 text-white shadow-lg">

        <button
          class="grid h-11 w-11 place-items-center rounded-md bg-white/10 text-lg hover:bg-white/20"
          type="button"
          aria-label="Move up"
          title="Move up"
          onclick={() => moveSelected(-1)}
        >
          ↑
        </button>
        <button
          class="grid h-11 w-11 place-items-center rounded-md bg-white/10 text-lg hover:bg-white/20"
          type="button"
          aria-label="Move down"
          title="Move down"
          onclick={() => moveSelected(1)}
        >
          ↓
        </button>

        <button
          class="grid h-11 w-11 place-items-center rounded-md bg-white/10 text-lg hover:bg-white/20"
          type="button"
          aria-label="Outdent"
          title="Outdent"
          onclick={() => adjustIndentSelected(-1)}
        >
          ⇤
        </button>
        <button
          class="grid h-11 w-11 place-items-center rounded-md bg-white/10 text-lg hover:bg-white/20"
          type="button"
          aria-label="Indent"
          title="Indent"
          onclick={() => adjustIndentSelected(1)}
        >
          ⇥
        </button>

        <div class="relative">
          <button
            class="grid h-11 w-11 place-items-center rounded-md bg-white/10 text-lg hover:bg-white/20"
            type="button"
            aria-label="Change type"
            title="Change type"
            onclick={() => (showTypeMenu = !showTypeMenu)}
          >
            T
          </button>
          {#if showTypeMenu}
            <div class="absolute bottom-12 right-0 w-40 overflow-hidden rounded-lg border border-slate-200 bg-white text-slate-900 shadow-xl">
              <button class="w-full px-3 py-2 text-left text-sm hover:bg-slate-50" type="button" onclick={() => setTypeSelected('text')}>
                Note
              </button>
              <button class="w-full px-3 py-2 text-left text-sm hover:bg-slate-50" type="button" onclick={() => setTypeSelected('image')}>
                Image
              </button>
              <button class="w-full px-3 py-2 text-left text-sm hover:bg-slate-50" type="button" onclick={() => setTypeSelected('attachment')}>
                File
              </button>
              <button class="w-full px-3 py-2 text-left text-sm hover:bg-slate-50" type="button" onclick={() => setTypeSelected('task')}>
                Task
              </button>
              <button
                class="w-full border-t px-3 py-2 text-left text-sm text-slate-500 hover:bg-slate-50"
                type="button"
                onclick={closeTypeMenu}
              >
                Cancel
              </button>
            </div>
          {/if}
        </div>

        <button
          class="grid h-11 w-11 place-items-center rounded-md bg-white/10 text-lg hover:bg-white/20"
          type="button"
          aria-label="Copy"
          title="Copy"
          onclick={copySelected}
        >
          ⧉
        </button>
        <button
          class="grid h-11 w-11 place-items-center rounded-md bg-white/10 text-lg hover:bg-white/20"
          type="button"
          aria-label="Add to collection"
          title="Add to collection"
          onclick={addSelectedToCollection}
        >
          ＋
        </button>
        <button
          class="grid h-11 w-11 place-items-center rounded-md bg-white/10 text-lg hover:bg-white/20"
          type="button"
          aria-label="Info"
          title="Info"
          onclick={openDetailSelected}
        >
          ⓘ
        </button>
        <button
          class="grid h-11 w-11 place-items-center rounded-md bg-red-500/80 text-lg hover:bg-red-500"
          type="button"
          aria-label="Delete"
          title="Delete"
          onclick={deleteSelected}
        >
          🗑
        </button>
        <button
          class="grid h-11 w-11 place-items-center rounded-md text-lg text-white/80 hover:bg-white/10 hover:text-white"
          type="button"
          aria-label="Clear selection"
          title="Clear selection"
          onclick={() => {
            clearSelection();
            closeTypeMenu();
          }}
        >
          ✕
        </button>
      </div>
    </div>
  {/if}
</div>

<ImageModal
  attachmentId={modalImage?.id ?? null}
  filename={modalImage?.filename ?? ''}
  onClose={closeImageModal}
/>
