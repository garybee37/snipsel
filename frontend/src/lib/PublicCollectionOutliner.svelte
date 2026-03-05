<script lang="ts">
  import MarkdownIt from 'markdown-it';
  import { api, type Attachment, type CollectionItem } from './api';
  import ImageModal from './ImageModal.svelte';
  import VideoModal from './VideoModal.svelte';

  let { token, collection, items, canWrite = false, onReload } = $props<{
    token: string;
    collection: {
      id: string;
      title: string;
      icon: string;
      header_color: string | null;
      header_image_url: string | null;
      header_image_position: string | null;
      header_image_x_position: string | null;
      header_image_zoom: number | null;
    };
    items: CollectionItem[];
    canWrite?: boolean;
    onReload?: () => void;
  }>();

  const md = new MarkdownIt({ html: false, linkify: true, breaks: false });

  let expandedSnipsels = $state<Set<string>>(new Set());
  let modalImage = $state<{ id: string; filename: string } | null>(null);
  let modalVideo = $state<{ id: string; filename: string } | null>(null);

  let newContent = $state('');
  let creating = $state(false);

  let sortedItems = $derived([...items].sort((a, b) => a.position - b.position));

  async function handleCreate() {
    if (!newContent.trim() || creating) return;
    creating = true;
    try {
      await api.public.createSnipsel(token, {
        content_markdown: newContent.trim(),
        type: collection.default_snipsel_type || 'text'
      });
      newContent = '';
      if (onReload) onReload();
    } catch (err) {
      console.error('Failed to create snipsel:', err);
      alert('Fehler beim Erstellen des Snipsels.');
    } finally {
      creating = false;
    }
  }

  let collapsibleParentIds = $derived.by(() => {
    const ids = new Set<string>();
    for (let i = 0; i < sortedItems.length - 1; i++) {
      if (sortedItems[i + 1].indent > sortedItems[i].indent) {
        ids.add(sortedItems[i].snipsel_id);
      }
    }
    return ids;
  });

  function toggleExpand(id: string) {
    const next = new Set(expandedSnipsels);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    expandedSnipsels = next;
  }

  function renderMarkdown(content: string | null) {
    if (!content) return '';
    return md.render(content);
  }

  function isImageAttachment(a: any) {
    return a.mime_type?.startsWith('image/');
  }

  function isVideoAttachment(a: any) {
    return a.mime_type?.startsWith('video/');
  }

  function getThumbnailUrl(a: any) {
    return `/api/attachments/${a.id}/thumbnail`;
  }
</script>

<div class="public-outliner" style="--header-color: {collection.header_color || '#3b82f6'}">
  {#if collection.header_image_url}
    <div class="header-image-container">
      <img
        src={collection.header_image_url}
        alt=""
        class="header-image"
        style="object-position: {collection.header_image_x_position || '50%'} {collection.header_image_position || '50%'}; transform: scale({collection.header_image_zoom || 1});"
      />
    </div>
  {/if}

  <header class="collection-header">
    <div class="title-row">
      <span class="icon">{collection.icon}</span>
      <h1>{collection.title}</h1>
    </div>
  </header>

  <div class="items-list">
    {#each sortedItems as item (item.snipsel_id)}
      {@const isExpanded = expandedSnipsels.has(item.snipsel_id)}
      {@const isCollapsible = collapsibleParentIds.has(item.snipsel_id)}
      
      <div 
        class="item-row indent-{item.indent}"
        class:is-task={item.snipsel.type === 'task'}
        class:is-done={item.snipsel.task_done}
      >
        <div class="item-content-wrapper">
          {#if isCollapsible}
            <button class="expand-toggle" onclick={() => toggleExpand(item.snipsel_id)}>
              {isExpanded ? '▼' : '▶'}
            </button>
          {:else}
            <div class="expand-spacer"></div>
          {/if}

          <div class="snipsel-body">
            <div class="markdown-content">
              {@html renderMarkdown(item.snipsel.content_markdown)}
            </div>

            {#if item.snipsel.attachments?.length}
              <div class="attachments-grid">
                {#each item.snipsel.attachments as a}
                  {#if isImageAttachment(a)}
                    <button class="attachment-preview" onclick={() => modalImage = a}>
                      <img src={getThumbnailUrl(a)} alt={a.filename} />
                    </button>
                  {:else if isVideoAttachment(a)}
                    <button class="attachment-preview video-preview" onclick={() => modalVideo = a}>
                      <img src={getThumbnailUrl(a)} alt={a.filename} />
                      <div class="play-overlay">▶</div>
                    </button>
                  {:else}
                    <a href="/api/attachments/{a.id}" class="attachment-file" target="_blank">
                      <span class="file-icon">📎</span>
                      <span class="filename">{a.filename}</span>
                    </a>
                  {/if}
                {/each}
              </div>
            {/if}
          </div>
        </div>
      </div>
    {/each}
  </div>

  {#if canWrite}
    <div class="create-snipsel-section">
      <div class="create-input-wrapper">
        <textarea
          bind:value={newContent}
          placeholder="Add something anonymously..."
          class="create-textarea"
          rows="2"
          onkeydown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
              handleCreate();
            }
          }}
        ></textarea>
        <button
          class="create-button"
          onclick={handleCreate}
          disabled={creating || !newContent.trim()}
        >
          {creating ? 'Adding...' : 'Add'}
        </button>
      </div>
      <div class="create-hint">
        Cmd+Enter to add
      </div>
    </div>
  {/if}
</div>

{#if modalImage}
  <ImageModal
    id={modalImage.id}
    filename={modalImage.filename}
    onClose={() => modalImage = null}
  />
{/if}

{#if modalVideo}
  <VideoModal
    id={modalVideo.id}
    filename={modalVideo.filename}
    onClose={() => modalVideo = null}
  />
{/if}

<style>
  .public-outliner {
    max-width: 800px;
    margin: 0 auto;
    padding-bottom: 100px;
    background: var(--bg-color, #fff);
    min-height: 100vh;
  }

  .header-image-container {
    height: 200px;
    overflow: hidden;
    position: relative;
    background: #eee;
  }

  .header-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .collection-header {
    padding: 2rem 1rem;
    border-bottom: 2px solid var(--header-color);
  }

  .title-row {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .icon {
    font-size: 2.5rem;
  }

  h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
  }

  .items-list {
    padding: 1rem 0;
  }

  .item-row {
    padding: 0.5rem 1rem;
    display: flex;
    flex-direction: column;
  }

  .item-content-wrapper {
    display: flex;
    gap: 0.5rem;
    align-items: flex-start;
  }

  .expand-toggle {
    background: none;
    border: none;
    cursor: pointer;
    padding: 2px;
    color: #666;
    width: 20px;
    text-align: center;
  }

  .expand-spacer {
    width: 20px;
  }

  .snipsel-body {
    flex: 1;
    min-width: 0;
  }

  .markdown-content :global(p) { margin: 0; }

  .indent-1 { padding-left: 2rem; }
  .indent-2 { padding-left: 3.5rem; }
  .indent-3 { padding-left: 5rem; }

  .attachments-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }

  .attachment-preview {
    width: 120px;
    height: 120px;
    padding: 0;
    border: 1px solid #ddd;
    border-radius: 8px;
    overflow: hidden;
    cursor: pointer;
    background: #f9f9f9;
  }

  .attachment-preview img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .video-preview { position: relative; }
  .play-overlay {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(0,0,0,0.5);
    color: white;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
  }

  .attachment-file {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.8rem;
    background: #f1f1f1;
    border-radius: 20px;
    text-decoration: none;
    color: #333;
    font-size: 0.9rem;
  }

  .is-done .markdown-content {
    text-decoration: line-through;
    color: #888;
  }

  .create-snipsel-section {
    margin-top: 2rem;
    padding: 1rem;
    border-top: 1px solid #eee;
  }

  .create-input-wrapper {
    display: flex;
    gap: 0.5rem;
    align-items: flex-start;
    padding: 1rem;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 1rem;
  }

  .create-textarea {
    flex: 1;
    resize: none;
    border: none;
    background: transparent;
    padding: 0;
    font-size: 0.9rem;
    outline: none;
  }

  .create-button {
    background: var(--header-color);
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 2rem;
    font-weight: 600;
    font-size: 0.8rem;
    cursor: pointer;
  }

  .create-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .create-hint {
    margin-top: 0.3rem;
    font-size: 0.7rem;
    color: #94a3b8;
    text-align: right;
  }

  @media (prefers-color-scheme: dark) {
    .create-snipsel-section { border-top-color: #334155; }
    .create-input-wrapper {
      background: #1e293b;
      border-color: #334155;
    }
    .create-textarea { color: #f1f5f9; }
    .create-hint { color: #64748b; }
  }
</style>
