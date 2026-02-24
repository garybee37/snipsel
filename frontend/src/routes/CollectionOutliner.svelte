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
  let creatingFromTripleEmptyLines = $state(false);

  let selectedIds = $state<Set<string>>(new Set());

  // Prevent stale list fetches from overwriting optimistic mutations.
  let itemsLoadSeq = 0;
  let itemsMutationSeq = 0;

  let hideDoneTasks = $state(false);

  function canWrite(): boolean {
    return $currentCollection?.access_level !== 'read';
  }

  let attachmentsInputRef: HTMLInputElement | undefined = $state();
  let uploadingAttachments = $state(false);

  let templates = $state<Array<{ id: string; title: string; icon: string }>>([]);
  let showTemplateMenu = $state(false);

  let shareCount = $state(0);

  let modalImage = $state<{ id: string; filename: string } | null>(null);

  let showTypeMenu = $state(false);
  function closeTemplateMenu() {
    showTemplateMenu = false;
  }

  const DEFAULT_HEADER_COLOR = '#4f46e5';
  const TOOLBOX_BASE_COLOR = '#ffffff';

  function getHeaderColor(): string {
    const raw =
      ($currentCollection?.header_color || '').trim() ||
      ($currentUser?.default_collection_header_color || '').trim() ||
      DEFAULT_HEADER_COLOR;

    return /^#[0-9a-fA-F]{6}$/.test(raw) ? raw : DEFAULT_HEADER_COLOR;
  }

  type Rgb = { r: number; g: number; b: number };

  function clampByte(n: number): number {
    return Math.max(0, Math.min(255, Math.round(n)));
  }

  function hexToRgb(hex: string): Rgb | null {
    const h = hex.trim();
    const m = /^#([0-9a-fA-F]{6})$/.exec(h);
    if (!m) return null;
    const v = m[1];
    const r = parseInt(v.slice(0, 2), 16);
    const g = parseInt(v.slice(2, 4), 16);
    const b = parseInt(v.slice(4, 6), 16);
    return { r, g, b };
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

  function getToolboxBg(): string {
    const base = hexToRgb(TOOLBOX_BASE_COLOR) ?? { r: 255, g: 255, b: 255 };
    const header = hexToRgb(getHeaderColor());
    const mixed = header ? mixRgb(base, header, 0.14) : base;
    return rgba(mixed, 0.96);
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

  function toggleHideDoneTasks() {
    hideDoneTasks = !hideDoneTasks;
    clearSelection();
    editingSnipselId.set(null);
  }

  function openDetail(id: string) {
    currentView.set({ type: 'snipsel', id });
  }

  async function toggleTaskDone(item: CollectionItem) {
    if (!$currentCollection) return;
    if (!canWrite()) return;
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

  async function uploadAttachmentsSelected(e: Event) {
    const input = e.currentTarget as HTMLInputElement;
    const files = input.files;
    if (!files || files.length === 0) return;
    if (selectedIds.size === 0) {
      input.value = '';
      return;
    }

    uploadingAttachments = true;
    isLoading.set(true);
    try {
      const ids = Array.from(selectedIds);
      for (const snipselId of ids) {
        for (const file of Array.from(files)) {
          await api.attachments.upload(snipselId, file);
        }
      }
      await loadItems();
      clearSelection();
    } finally {
      uploadingAttachments = false;
      isLoading.set(false);
      input.value = '';
    }
  }

  async function loadTemplates() {
    const res = await api.collections.list();
    templates = res.collections
      .filter((c) => Boolean(c.is_template) && c.access_level === 'owner')
      .map((c) => ({ id: c.id, title: c.title, icon: c.icon }));
  }

  async function loadShareCount() {
    if (!$currentCollection) {
      shareCount = 0;
      return;
    }
    if ($currentCollection.access_level !== 'owner') {
      shareCount = 0;
      return;
    }
    try {
      const res = await api.collections.listShares($currentCollection.id);
      shareCount = res.shares.length;
    } catch {
      shareCount = 0;
    }
  }

  async function insertTemplateSelected(templateCollectionId: string) {
    if (!$currentCollection) return;
    if (!canWrite()) return;
    isLoading.set(true);
    try {
      await api.collections.insertTemplate($currentCollection.id, templateCollectionId);
      await loadItems();
      closeTemplateMenu();
    } finally {
      isLoading.set(false);
    }
  }

  async function loadItems() {
    if (!$currentCollection) return;
    const loadSeq = ++itemsLoadSeq;
    const mutationAtStart = itemsMutationSeq;
    isLoading.set(true);
    try {
      const res = await api.snipsels.list($currentCollection.id);
      if (loadSeq !== itemsLoadSeq) return;
      if (mutationAtStart !== itemsMutationSeq) return;
      collectionItems.set(res.items);
    } finally {
      isLoading.set(false);
    }
  }

  function startEdit(item: CollectionItem) {
    if (!canWrite()) return;
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

  async function handleEditInput() {
    autosizeTextarea();
    if (creatingFromTripleEmptyLines) return;

    const el = textareaRef;
    if (!el) return;

    const atEnd = (el.selectionStart ?? 0) === el.value.length && (el.selectionEnd ?? 0) === el.value.length;
    if (!atEnd) return;

    if (!editContent.endsWith('\n\n\n')) return;

    const currentId = $editingSnipselId;
    const currentItem = currentId ? $sortedItems.find((i) => i.snipsel_id === currentId) : null;
    if (!currentId || !currentItem) return;

    creatingFromTripleEmptyLines = true;
    try {
      // Remove the 3 empty lines.
      const nextContent = editContent.slice(0, -3);
      editContent = nextContent;

      // Persist current snipsel update immediately so we don't lose edits when switching focus.
      const contentToSave = nextContent.trim().length === 0 ? null : nextContent;
      itemsMutationSeq += 1;
      await api.snipsels.update(currentId, { content_markdown: contentToSave });
      collectionItems.update((items) =>
        items.map((i) =>
          i.snipsel_id === currentId
            ? { ...i, snipsel: { ...i.snipsel, content_markdown: contentToSave } }
            : i
        )
      );

      await createSnipselAfterPosition(currentItem.position, currentItem.indent);
    } finally {
      creatingFromTripleEmptyLines = false;
    }
  }

  function autosizeTextarea() {
    const el = textareaRef;
    if (!el) return;
    el.style.height = '0px';
    el.style.height = `${el.scrollHeight}px`;
  }

  function handleEditFocusOut(e: FocusEvent) {
    if (creatingFromTripleEmptyLines) return;
    const related = e.relatedTarget as Node | null;
    if (related && editContainerRef?.contains(related)) return;
    if (!saving) saveEdit();
  }

  async function createSnipsel() {
    if (!$currentCollection) return;
    if (!canWrite()) return;
    isLoading.set(true);
    try {
      let geo:
        | { geo_lat: number; geo_lng: number; geo_accuracy_m?: number }
        | null = null;
      try {
        geo = await new Promise((resolve) => {
          if (!('geolocation' in navigator)) return resolve(null);
          navigator.geolocation.getCurrentPosition(
            (pos) =>
              resolve({
                geo_lat: pos.coords.latitude,
                geo_lng: pos.coords.longitude,
                geo_accuracy_m: pos.coords.accuracy,
              }),
            () => resolve(null),
            { enableHighAccuracy: false, maximumAge: 60_000, timeout: 1500 }
          );
        });
      } catch {
        geo = null;
      }

      const res = await api.snipsels.create($currentCollection.id, {
        type: $currentCollection.default_snipsel_type || 'text',
        ...(geo ?? {}),
      });

      itemsMutationSeq += 1;
      collectionItems.update((items) => [...items, res.item]);
      startEdit(res.item);
    } finally {
      isLoading.set(false);
    }
  }

  async function createSnipselAfterPosition(position: number, indent: number) {
    if (!$currentCollection) return;
    if (!canWrite()) return;
    isLoading.set(true);
    try {
      let geo:
        | { geo_lat: number; geo_lng: number; geo_accuracy_m?: number }
        | null = null;
      try {
        geo = await new Promise((resolve) => {
          if (!('geolocation' in navigator)) return resolve(null);
          navigator.geolocation.getCurrentPosition(
            (pos) =>
              resolve({
                geo_lat: pos.coords.latitude,
                geo_lng: pos.coords.longitude,
                geo_accuracy_m: pos.coords.accuracy,
              }),
            () => resolve(null),
            { enableHighAccuracy: false, maximumAge: 60_000, timeout: 1500 }
          );
        });
      } catch {
        geo = null;
      }

      const res = await api.snipsels.create($currentCollection.id, {
        type: $currentCollection.default_snipsel_type || 'text',
        ...(geo ?? {}),
      });

      const newId = res.item.snipsel_id;

      const list = [...$sortedItems];
      const idx = list.findIndex((i) => i.position === position);
      const insertAt = idx >= 0 ? idx + 1 : list.length;
      const next = [...list.slice(0, insertAt), { ...res.item, indent }, ...list.slice(insertAt)];

      const reordered = next.map((i, index) => ({ ...i, position: index + 1 }));
      collectionItems.set(reordered);

      // Mark mutation so any in-flight loadItems doesn't overwrite local optimistic state.
      itemsMutationSeq += 1;

      const payload = reordered.map((i) => ({ snipsel_id: i.snipsel_id, position: i.position, indent: i.indent }));
      await api.snipsels.reorder($currentCollection.id, payload);

      const createdItem = reordered.find((i) => i.snipsel_id === newId);
      if (createdItem) startEdit(createdItem);

      // Ensure we don't immediately auto-delete the newly created empty snipsel
      // due to a focus-out save on the previous snipsel.
      itemsMutationSeq += 1;
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
      // Consume the request so we don't create multiple.
      newSnipselRequest.set(0);
      clearSelection();
      closeTypeMenu();
      closeTemplateMenu();
      // Ensure we start from the correct collection's list before optimistic append.
      loadItems().then(() => createSnipsel());
    }
  });

  $effect(() => {
    loadTemplates();
  });

  $effect(() => {
    loadShareCount();
  });

  async function deleteSelected() {
    if (!$currentCollection) return;
    if (!canWrite()) return;
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
    if (!canWrite()) return;
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
    if (!canWrite()) return;
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

  function moveSelectedToCollection() {
    if (!$currentCollection) return;
    if (!canWrite()) return;
    if (selectedIds.size === 0) return;
    pendingReference.set({
      snipselIds: Array.from(selectedIds),
      mode: 'move',
      fromCollectionId: $currentCollection.id,
    });
    clearSelection();
    currentView.set({ type: 'collections' });
  }

  function addSelectedToCollection() {
    if (!canWrite()) return;
    if (selectedIds.size === 0) return;
    pendingReference.set({ snipselIds: Array.from(selectedIds), mode: 'add' });
    clearSelection();
    currentView.set({ type: 'collections' });
  }

  async function adjustIndentSelected(delta: number) {
    if (!$currentCollection) return;
    if (!canWrite()) return;
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

  async function setIndentSelected(indent: number) {
    if (!$currentCollection) return;
    if (!canWrite()) return;
    if (selectedIds.size === 0) return;

    const nextIndent = Math.max(0, Math.min(6, indent));
    const current = $sortedItems;
    const updated = current.map((i) => {
      if (!selectedIds.has(i.snipsel_id)) return i;
      return { ...i, indent: nextIndent };
    });

    const payload = updated.map((i, idx) => ({
      snipsel_id: i.snipsel_id,
      position: idx + 1,
      indent: i.indent,
    }));

    await api.snipsels.reorder($currentCollection.id, payload);
    collectionItems.set(updated.map((i, idx) => ({ ...i, position: idx + 1 })));
  }

  async function moveSelectedToEdge(edge: 'top' | 'bottom') {
    if (!$currentCollection) return;
    if (!canWrite()) return;
    if (selectedIds.size === 0) return;

    const list = [...$sortedItems];
    const selected = list.filter((i) => selectedIds.has(i.snipsel_id));
    const rest = list.filter((i) => !selectedIds.has(i.snipsel_id));
    const next = edge === 'top' ? [...selected, ...rest] : [...rest, ...selected];

    const payload = next.map((i, index) => ({
      snipsel_id: i.snipsel_id,
      position: index + 1,
      indent: i.indent,
    }));

    await api.snipsels.reorder($currentCollection.id, payload);
    collectionItems.set(next.map((i, index) => ({ ...i, position: index + 1 })));
  }

  function longPress(onLongPress: () => void, onShortPress: () => void, ms = 450) {
    let timer: ReturnType<typeof setTimeout> | null = null;
    let firedLong = false;
    let handledByPointer = false;
    let activePointerId: number | null = null;

    function cancel() {
      if (timer) clearTimeout(timer);
      timer = null;
    }

    function reset() {
      cancel();
      firedLong = false;
      handledByPointer = false;
      activePointerId = null;
    }

    return {
      onpointerdown: (e: PointerEvent) => {
        reset();

        activePointerId = e.pointerId;

        // Make pointerup reliable even if the finger drifts slightly.
        try {
          (e.currentTarget as HTMLElement | null)?.setPointerCapture(e.pointerId);
        } catch {
          // Ignore (some browsers/targets may not support capture).
        }

        timer = setTimeout(() => {
          firedLong = true;
          handledByPointer = true;
          onLongPress();
        }, ms);
      },
      onpointerup: (e: PointerEvent) => {
        cancel();

        if (!firedLong) {
          handledByPointer = true;
          onShortPress();
        }

        if (activePointerId !== null) {
          try {
            (e.currentTarget as HTMLElement | null)?.releasePointerCapture(activePointerId);
          } catch {
            // Ignore.
          }
        }

        activePointerId = null;
      },
      onpointercancel: () => reset(),
      onpointerleave: () => cancel(),
      onclick: (e: MouseEvent) => {
        // If we already handled via pointer events, suppress the synthetic click.
        if (handledByPointer) {
          e.preventDefault();
          e.stopPropagation();
          handledByPointer = false;
          return;
        }

        // Keyboard / non-pointer activation fallback.
        onShortPress();
      },
      oncontextmenu: (e: MouseEvent) => {
        if (firedLong) e.preventDefault();
      },
    };
  }

  const lpMoveTop = longPress(
    () => void moveSelectedToEdge('top'),
    () => void moveSelected(-1)
  );
  const lpMoveBottom = longPress(
    () => void moveSelectedToEdge('bottom'),
    () => void moveSelected(1)
  );
  const lpOutdentToZero = longPress(
    () => void setIndentSelected(0),
    () => void adjustIndentSelected(-1)
  );

  async function moveSelected(dir: -1 | 1) {
    if (!$currentCollection) return;
    if (!canWrite()) return;
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
    const html = md.render(text);
    const tokenBg = getToolboxBg();
    const tokenFg = getHeaderColor();
    return html.replace(
      /(^|[^\w])(#[A-Za-z][\w-]*|@[A-Za-z][\w-]*)/g,
      (m, p1, token) =>
        `${p1}<mark class="snip-token" style="background-color:${tokenBg}; color:${tokenFg}">${token}</mark>`
    );
  }

  function isImageAttachment(a: Attachment): boolean {
    return Boolean(a.mime_type?.startsWith('image/') || a.has_thumbnail);
  }

  function isDoneTask(item: CollectionItem): boolean {
    return item.snipsel.type === 'task' && Boolean(item.snipsel.task_done);
  }

  function visibleItems(items: CollectionItem[]): CollectionItem[] {
    if (!hideDoneTasks) return items;
    return items.filter((i) => !isDoneTask(i));
  }

  function hiddenDoneCount(items: CollectionItem[]): number {
    if (!hideDoneTasks) return 0;
    return items.filter((i) => isDoneTask(i)).length;
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

  function taskProgress() {
    const tasks = $sortedItems.filter((i) => i.snipsel.type === 'task');
    const total = tasks.length;
    const done = tasks.filter((i) => Boolean(i.snipsel.task_done)).length;
    return { total, done, ratio: total > 0 ? done / total : 0 };
  }
</script>

<div class="space-y-3">
  <input
    bind:this={focusProxyRef}
    class="pointer-events-none absolute left-0 top-0 h-0 w-0 opacity-0"
    tabindex="-1"
    aria-hidden="true"
  />

  <div class="relative">
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

      {#if taskProgress().total > 0}
        <button
          class="absolute left-[5.5rem] right-4 top-0 -translate-y-1/2 rounded-full border border-slate-200 bg-white/80 p-1 shadow-sm backdrop-blur-md"
          type="button"
          aria-label="Toggle done tasks"
          title={hideDoneTasks ? 'Show done tasks' : 'Hide done tasks'}
          onclick={toggleHideDoneTasks}
        >
          <div class="h-2 w-full overflow-hidden rounded-full bg-black/10">
            <div
              class="h-full rounded-full"
              style={`width: ${Math.round(taskProgress().ratio * 100)}%; background-color: ${getHeaderColor()}`}
            ></div>
          </div>
        </button>
      {/if}

        <button
          class="pl-20 text-lg font-semibold hover:underline"
          type="button"
          onclick={() => $currentCollection && currentView.set({ type: 'collection_settings', id: $currentCollection.id })}
        >
          {$currentCollection?.title}
        </button>
      </div>
    </div>

    {#if $currentCollection}
      {@const level = $currentCollection.access_level}
      {@const showSharedByYou = level === 'owner' && shareCount > 0}
      {@const showSharedWithYou = level === 'read' || level === 'write'}
      {@const showStatusPill = Boolean(
        $currentCollection.is_favorite ||
          showSharedByYou ||
          showSharedWithYou ||
          $currentCollection.is_template ||
          $currentCollection.archived
      )}

      {#if showStatusPill}
        <div
          class="absolute right-4 top-0 z-5 -translate-y-1/2 flex items-center gap-3 rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-lg text-slate-800 shadow-sm backdrop-blur-md"
          aria-label="Collection status"
        >
          {#if $currentCollection.is_favorite}
            <span class="leading-none" aria-label="Favorite" title="Favorite">♥</span>
          {/if}

          {#if showSharedByYou}
            <span class="leading-none" aria-label="Shared by you" title="Shared by you">⇪</span>
          {/if}
          {#if showSharedWithYou}
            <span class="leading-none" aria-label="Shared with you" title="Shared with you">⇩</span>
          {/if}

          {#if $currentCollection.is_template}
            <span class="leading-none" aria-label="Template" title="Template">▦</span>
          {/if}

          {#if $currentCollection.archived}
            <span class="leading-none" aria-label="Archived" title="Archived">⧗</span>
          {/if}
        </div>
      {/if}
    {/if}
  </div>

  {#if $isLoading && $sortedItems.length === 0}
    <div class="py-8 text-center text-sm text-slate-500">Loading...</div>
  {:else if $sortedItems.length === 0}
    <div class="flex flex-col">
      <div class="py-8 text-center text-base text-slate-500">No snipsels yet</div>
      <button
        class="mt-2 h-24 w-full rounded-lg border border-dashed border-slate-200 bg-slate-50/50 text-left text-base text-slate-400 hover:bg-slate-50"
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
  {:else}
    <div class="flex flex-col">
      {#each visibleItems($sortedItems) as item (item.snipsel_id)}
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
                oninput={handleEditInput}
                onkeydown={handleKeydown}
              ></textarea>
            </div>
          {:else}
            {#if item.snipsel.type === 'task'}
              <button
                type="button"
                aria-label={item.snipsel.task_done ? 'Mark task not done' : 'Mark task done'}
                class="absolute left-1 top-1/2 grid h-7 w-7 -translate-y-1/2 place-items-center rounded-full border border-slate-300 bg-white"
                onclick={(e) => {
                  e.stopPropagation();
                  toggleTaskDone(item);
                }}
                style={item.snipsel.task_done
                  ? `border-color: ${getHeaderColor()}; background-color: ${getToolboxBg()}; color: ${getHeaderColor()}`
                  : undefined}
              >
                {#if item.snipsel.task_done}
                  ✓
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
        disabled={!canWrite()}
      ></button>

      {#if hideDoneTasks && hiddenDoneCount($sortedItems) > 0}
        <div class="mt-3 text-center text-sm text-slate-500">
          {hiddenDoneCount($sortedItems)} erledigte Aufgaben ausgeblendet
        </div>
      {/if}
    </div>
  {/if}

  {#if selectedIds.size > 0}
    <div class="fixed bottom-20 left-0 right-0 z-20 px-4 pb-4">
      <div
        class="mx-auto flex max-w-3xl flex-wrap items-center justify-center gap-2 rounded-xl px-3 py-3 text-slate-900 shadow-lg ring-1 ring-black/5 backdrop-blur-md"
        style={`background-color: ${getToolboxBg()}`}
      >

         <input
           bind:this={attachmentsInputRef}
           class="hidden"
           type="file"
           multiple
           onchange={uploadAttachmentsSelected}
           disabled={uploadingAttachments}
         />

        <button
          class="grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10"
          type="button"
          aria-label="Move up"
          title="Move up"
          onclick={lpMoveTop.onclick}
          onpointerdown={lpMoveTop.onpointerdown}
          onpointerup={lpMoveTop.onpointerup}
          onpointercancel={lpMoveTop.onpointercancel}
          onpointerleave={lpMoveTop.onpointerleave}
          oncontextmenu={lpMoveTop.oncontextmenu}
          disabled={!canWrite()}
        >
          ↑
        </button>
        <button
          class="grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10"
          type="button"
          aria-label="Move down"
          title="Move down"
          onclick={lpMoveBottom.onclick}
          onpointerdown={lpMoveBottom.onpointerdown}
          onpointerup={lpMoveBottom.onpointerup}
          onpointercancel={lpMoveBottom.onpointercancel}
          onpointerleave={lpMoveBottom.onpointerleave}
          oncontextmenu={lpMoveBottom.oncontextmenu}
          disabled={!canWrite()}
        >
          ↓
        </button>

        <button
          class="grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10"
          type="button"
          aria-label="Outdent"
          title="Outdent"
          onclick={lpOutdentToZero.onclick}
          onpointerdown={lpOutdentToZero.onpointerdown}
          onpointerup={lpOutdentToZero.onpointerup}
          onpointercancel={lpOutdentToZero.onpointercancel}
          onpointerleave={lpOutdentToZero.onpointerleave}
          oncontextmenu={lpOutdentToZero.oncontextmenu}
          disabled={!canWrite()}
        >
          ⇤
        </button>
        <button
          class="grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10"
          type="button"
          aria-label="Indent"
          title="Indent"
          onclick={() => adjustIndentSelected(1)}
          disabled={!canWrite()}
        >
          ⇥
        </button>

        <div class="relative">
          <button
            class="grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10"
            type="button"
            aria-label="Change type"
            title="Change type"
            onclick={() => (showTypeMenu = !showTypeMenu)}
            disabled={!canWrite()}
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
          class="grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10"
          type="button"
          aria-label="Copy"
          title="Copy"
          onclick={copySelected}
          disabled={!canWrite()}
        >
          ⧉
        </button>

        <div class="relative">
          <button
            class="grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10"
            type="button"
            aria-label="Insert template"
            title="Insert template"
            onclick={() => (showTemplateMenu = !showTemplateMenu)}
            disabled={!canWrite()}
          >
            □
          </button>
          {#if showTemplateMenu}
            <div class="absolute bottom-12 right-0 w-56 overflow-hidden rounded-lg border border-slate-200 bg-white text-slate-900 shadow-xl">
              {#if templates.length === 0}
                <div class="px-3 py-2 text-sm text-slate-500">No templates</div>
              {:else}
                {#each templates as t (t.id)}
                  <button
                    class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50"
                    type="button"
                    onclick={() => insertTemplateSelected(t.id)}
                  >
                    <span class="text-base" aria-hidden="true">{t.icon}</span>
                    <span class="min-w-0 flex-1 truncate">{t.title}</span>
                  </button>
                {/each}
              {/if}
              <button
                class="w-full border-t px-3 py-2 text-left text-sm text-slate-500 hover:bg-slate-50"
                type="button"
                onclick={closeTemplateMenu}
              >
                Cancel
              </button>
            </div>
          {/if}
        </div>

        <button
          class="grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10"
          type="button"
          aria-label="Add attachments"
          title="Add attachments"
          onclick={() => attachmentsInputRef?.click()}
          disabled={uploadingAttachments || !canWrite()}
        >
          📎
        </button>
        <button
          class="grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10"
          type="button"
          aria-label="Move"
          title="Move"
          onclick={moveSelectedToCollection}
          disabled={!canWrite()}
        >
          ⇄
        </button>
        <button
          class="grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10"
          type="button"
          aria-label="Add to collection"
          title="Add to collection"
          onclick={addSelectedToCollection}
          disabled={!canWrite()}
        >
          ＋
        </button>
        <button
          class="grid h-11 w-11 place-items-center rounded-md bg-black/5 text-lg hover:bg-black/10"
          type="button"
          aria-label="Info"
          title="Info"
          onclick={openDetailSelected}
        >
          ⓘ
        </button>
        <button
          class="grid h-11 w-11 place-items-center rounded-md bg-red-600/90 text-lg text-white hover:bg-red-600"
          type="button"
          aria-label="Delete"
          title="Delete"
          onclick={deleteSelected}
          disabled={!canWrite()}
        >
          🗑
        </button>
        <button
          class="grid h-11 w-11 place-items-center rounded-md text-lg text-slate-600 hover:bg-black/5 hover:text-slate-900"
          type="button"
          aria-label="Clear selection"
          title="Clear selection"
          onclick={() => {
            clearSelection();
            closeTypeMenu();
            closeTemplateMenu();
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
