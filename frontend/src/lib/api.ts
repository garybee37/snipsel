export type ApiError = {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
};

export type User = {
  id: string;
  username: string;
  email: string;
  created_at: string;
  default_collection_header_color?: string | null;
  carry_over_open_tasks?: boolean;
  theme?: 'light' | 'dark' | 'system';
  day_collection_template_id?: string | null;
  passcode_set?: boolean;
  otp_enabled?: boolean;
  passkeys_count?: number;
  max_upload_bytes?: number;
};

export type UserStats = {
  collections: number;
  snipsels: number;
  completed_tasks: number;
  attachments: number;
};

export type UserPasskey = {
  id: string;
  name: string;
  created_at: string;
};

export type Collection = {
  id: string;
  title: string;
  icon: string;
  header_image_url: string | null;
  header_color?: string | null;
  header_image_position?: string | null;
  header_image_x_position?: string | null;
  header_image_zoom?: number | null;
  is_favorite?: boolean;
  is_template: boolean;
  is_passcode_protected: boolean;
  show_completed_tasks: boolean;
  default_snipsel_type: string | null;
  archived: boolean;
  list_for_day: string | null;
  created_at: string;
  modified_at: string;
  access_level?: 'owner' | 'write' | 'read';
  shared_by_username?: string | null;
  shared_out?: boolean;
  modified_by_id?: string;
  modified_by_username?: string | null;
  public_token?: string | null;
};
export type UserLite = { id: string; username: string };

export type CollectionBacklink = {
  snipsel_id: string;
  snipsel_content: string;
  collection_id: string;
  collection_title: string;
  collection_icon: string;
  position: number;
};


export type CollectionShare = {
  id: string;
  shared_with_user_id: string;
  shared_with_username?: string | null;
  permission: 'read' | 'write';
  created_at: string;
};

export type Notification = {
  id: string;
  message: string;
  is_read: boolean;
  snipsel_id?: string | null;
  collection_id?: string | null;
  created_at: string;
};

export type ReactionSummary = {
  emoji: string;
  count: number;
  me: boolean;
};

export type Snipsel = {
  id: string;
  type: string;
  content_markdown: string | null;
  task_done: boolean;
  done_at: string | null;
  done_by_id: string | null;
  done_by_username?: string | null;
  external_url: string | null;
  external_label: string | null;
  internal_target_snipsel_id: string | null;
  geo_lat?: number | null;
  geo_lng?: number | null;
  geo_accuracy_m?: number | null;
  reminder_at?: string | null;
  reminder_rrule?: string | null;
  created_at: string;
  created_by_id?: string;
  created_by_username?: string | null;
  modified_at: string;
  modified_by_id?: string;
  modified_by_username?: string | null;
  attachments: Array<{
    id: string;
    filename: string;
    mime_type: string | null;
    size_bytes: number;
    has_thumbnail: boolean;
  }>;
  tags?: string[];
  mentions?: string[];
  reactions?: ReactionSummary[];
};

export type SnipselDetailResponse = {
  snipsel: Snipsel;
  tags?: string[];
  mentions?: string[];
  placements?: Array<{ collection_id: string; position: number; indent: number }>;
  backlinks?: Array<{ from_snipsel_id: string; to_snipsel_id: string }>;
  has_collection_access?: boolean;
  has_write_access?: boolean;
  can_toggle_task_done?: boolean;
};

export type Attachment = {
  id: string;
  filename: string;
  mime_type: string | null;
  size_bytes: number;
  has_thumbnail: boolean;
};

export type CollectionItem = {
  collection_id: string;
  snipsel_id: string;
  position: number;
  indent: number;
  snipsel: Snipsel;
  collection_refs?: Array<{ title: string; collection_id: string }>;
};

export type SearchSnipselHit = {
  id: string;
  type: string;
  content_markdown: string | null;
  task_done: boolean;
  done_at: string | null;
  external_url: string | null;
  external_label: string | null;
  internal_target_snipsel_id: string | null;
  created_at: string;
  modified_at: string;
  collection_id?: string | null;
  collection_title?: string | null;
  collection_icon?: string | null;
  position?: number | null;
  has_collection_access?: boolean;
  has_write_access?: boolean;
  can_toggle_task_done?: boolean;
  reminder_at?: string | null;
  reminder_rrule?: string | null;
  attachments?: Attachment[];
  reactions?: ReactionSummary[];
  created_by_id?: string;
  created_by_username?: string | null;
  tags?: string[];
  mentions?: string[];
};

export type SearchCollectionHit = {
  id: string;
  title: string;
  icon: string;
  list_for_day: string | null;
};

export type SearchResponse = {
  snipsels: SearchSnipselHit[];
  collections: SearchCollectionHit[];
};

export type TagCount = { name: string; count: number };

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (res.status === 413) {
    throw {
      error: {
        code: 'payload_too_large',
        message: 'Die Datei ist zu groß für den Upload (Limit: 10MB).',
      },
    } as ApiError;
  }

  const contentType = res.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    const data = (await res.json()) as T | ApiError;
    if (!res.ok) {
      throw data;
    }
    return data as T;
  }

  if (!res.ok) {
    throw {
      error: {
        code: 'unknown_error',
        message: `Ein unerwarteter Fehler ist aufgetreten (${res.status}).`,
      },
    } as ApiError;
  }

  return {} as T;
}

export const api = {
  getConfig: () => requestJson<{ registration_enabled: boolean }>('/api/auth/config'),
  register: (input: { username: string; email: string; password: string }) =>
    requestJson<{ user: User }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  login: (input: { username: string; password: string }) =>
    requestJson<{ user?: User; status?: '2fa_required' }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  loginOtp: (code: string) =>
    requestJson<{ user: User }>('/api/auth/login/otp', {
      method: 'POST',
      body: JSON.stringify({ code }),
    }),
  twoFactor: {
    generate: () => requestJson<{ secret: string; provisioning_url: string }>('/api/auth/2fa/generate', { method: 'POST' }),
    qrUrl: () => '/api/auth/2fa/qr',
    enable: (input: { code: string; password_confirm: string }) =>
      requestJson<{ ok: true }>('/api/auth/2fa/enable', {
        method: 'POST',
        body: JSON.stringify(input),
      }),
    disable: (password_confirm: string) =>
      requestJson<{ ok: true }>('/api/auth/2fa/disable', {
        method: 'POST',
        body: JSON.stringify({ password_confirm }),
      }),
  },
  passkeys: {
    list: () => requestJson<{ passkeys: UserPasskey[] }>('/api/auth/passkeys'),
    registerBegin: () => requestJson<any>('/api/auth/passkeys/register/begin', { method: 'POST' }),
    registerComplete: (credential: any, name: string) =>
      requestJson<{ ok: true }>('/api/auth/passkeys/register/complete', {
        method: 'POST',
        body: JSON.stringify({ ...credential, name }),
      }),
    loginBegin: (username: string) =>
      requestJson<any>('/api/auth/passkeys/login/begin', {
        method: 'POST',
        body: JSON.stringify({ username }),
      }),
    loginComplete: (credential: any) =>
      requestJson<{ user: User }>('/api/auth/passkeys/login/complete', {
        method: 'POST',
        body: JSON.stringify(credential),
      }),
    delete: (id: string) => requestJson<{ ok: true }>(`/api/auth/passkeys/${id}`, { method: 'DELETE' }),
  },
  logout: () => requestJson<{ ok: true }>('/api/auth/logout', { method: 'POST' }),
  passcode: {
    set: (input: { passcode: string; password_confirm: string }) =>
      requestJson<{ ok: true }>('/api/auth/passcode/set', {
        method: 'POST',
        body: JSON.stringify(input),
      }),
    verify: (input: { passcode: string; collection_id: string }) =>
      requestJson<{ ok: true; unlocked_until: string }>('/api/auth/passcode/verify', {
        method: 'POST',
        body: JSON.stringify(input),
      }),
  },
  me: () => requestJson<{ user: User }>('/api/auth/me'),
  meStats: () => requestJson<{ stats: UserStats }>('/api/auth/me/stats'),
  updateMe: (input: {
    default_collection_header_color?: string | null;
    carry_over_open_tasks?: boolean;
    theme?: 'light' | 'dark' | 'system' | null;
    day_collection_template_id?: string | null;
    email?: string;
    password?: string;
    current_password?: string;
  }) =>
    requestJson<{ user: User }>('/api/auth/me', {
      method: 'PATCH',
      body: JSON.stringify(input),
    }),

  collections: {
    list: (includeArchived = false) =>
      requestJson<{ collections: Collection[] }>(
        `/api/collections${includeArchived ? '?include_archived=1' : ''}`
      ),
    get: (id: string) =>
      requestJson<{ collection: Collection }>(`/api/collections/${id}`),
    today: (day?: string) =>
      requestJson<{ collection: Collection }>(
        `/api/collections/today${day ? `?day=${day}` : ''}`
      ),
    create: (input: {
      title: string;
      icon?: string;
      header_image_url?: string | null;
      header_color?: string | null;
      default_snipsel_type?: string | null;
      show_completed_tasks?: boolean;
    }) =>
      requestJson<{ collection: Collection }>('/api/collections', {
        method: 'POST',
        body: JSON.stringify(input),
      }),
    update: (
      id: string,
      input: {
        title?: string;
        icon?: string;
        header_image_url?: string | null;
        header_color?: string | null;
        archived?: boolean;
        is_template?: boolean;
        default_snipsel_type?: string | null;
        is_passcode_protected?: boolean;
        show_completed_tasks?: boolean;
        header_image_position?: string | null;
      }
    ) =>
      requestJson<{ collection: Collection }>(`/api/collections/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(input),
      }),

    uploadHeaderImage: async (id: string, file: File, onProgress?: (percent: number) => void) => {
      return new Promise<{ collection: Collection }>((resolve, reject) => {
        const form = new FormData();
        form.append('file', file);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', `/api/collections/${id}/header-image`);
        xhr.withCredentials = true;

        if (onProgress) {
          xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
              onProgress((e.loaded / e.total) * 100);
            }
          };
        }

        xhr.onload = () => {
          if (xhr.status === 413) {
            reject({
              error: {
                code: 'payload_too_large',
                message: 'Die Datei ist zu groß für den Upload.',
              },
            } as ApiError);
            return;
          }

          let data: any;
          try {
            data = JSON.parse(xhr.responseText);
          } catch {
            data = { error: { code: 'unknown_error', message: `Ein unerwarteter Fehler ist aufgetreten (${xhr.status}).` } };
          }

          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(data);
          } else {
            reject(data);
          }
        };

        xhr.onerror = () => {
          reject({ error: { code: 'network_error', message: 'Netzwerkfehler beim Upload.' } } as ApiError);
        };

        xhr.send(form);
      });
    },

    favorite: (id: string) => requestJson<{ ok: true }>(`/api/collections/${id}/favorite`, { method: 'POST' }),
    unfavorite: (id: string) => requestJson<{ ok: true }>(`/api/collections/${id}/favorite`, { method: 'DELETE' }),
    delete: (id: string) =>
      requestJson<{ ok: true }>(`/api/collections/${id}`, { method: 'DELETE' }),
    autocomplete: (q: string) =>
      requestJson<{ collections: Array<{ id: string; title: string; icon: string }> }>(
        `/api/collections/autocomplete?q=${encodeURIComponent(q)}`
      ),

    listShares: (id: string) =>
      requestJson<{ shares: CollectionShare[] }>(`/api/collections/${id}/shares`),
    createShare: (id: string, input: { shared_with_user_id: string; permission: 'read' | 'write' }) =>
      requestJson<{ share: { id: string } }>(`/api/collections/${id}/shares`, {
        method: 'POST',
        body: JSON.stringify(input),
      }),
    deleteShare: (id: string, shareId: string) =>
      requestJson<{ ok: true }>(`/api/collections/${id}/shares/${shareId}`, { method: 'DELETE' }),

    insertTemplate: (id: string, templateCollectionId: string) =>
      requestJson<{ ok: true }>(`/api/collections/${id}/insert_template`, {
        method: 'POST',
        body: JSON.stringify({ template_collection_id: templateCollectionId }),
      }),
    listBacklinks: (id: string) => requestJson<{ backlinks: CollectionBacklink[] }>(`/api/collections/${id}/backlinks`),
    listRecent: () => requestJson<{ collections: Array<{ id: string; title: string; icon: string }> }>('/api/collections/recent'),
    clearRecent: () => requestJson<{ ok: true }>('/api/collections/recent', { method: 'DELETE' }),
    deleteCompletedTasks: (id: string) => requestJson<{ ok: true; count: number }>(`/api/collections/${id}/snipsels/completed`, { method: 'DELETE' }),
    resetCompletedTasks: (id: string) => requestJson<{ ok: true; count: number }>(`/api/collections/${id}/snipsels/completed/reset`, { method: 'POST' }),
  },

  users: {
    list: () => requestJson<{ users: UserLite[] }>('/api/users'),
  },

  snipsels: {
    list: (collectionId: string) =>
      requestJson<{ items: CollectionItem[] }>(
        `/api/collections/${collectionId}/snipsels`
      ),
    get: (snipselId: string) =>
      requestJson<{ snipsel: Snipsel }>(`/api/snipsels/${snipselId}`),
    create: (
      collectionId: string,
      input: {
        type?: string;
        content_markdown?: string;
        geo_lat?: number;
        geo_lng?: number;
        geo_accuracy_m?: number;
        indent?: number;
      }
    ) =>
      requestJson<{ item: CollectionItem }>(
        `/api/collections/${collectionId}/snipsels`,
        {
          method: 'POST',
          body: JSON.stringify(input),
        }
      ),
    update: (
      snipselId: string,
      input: {
        type?: string;
        content_markdown?: string | null;
        task_done?: boolean;
        external_url?: string | null;
        external_label?: string | null;
        internal_target_snipsel_id?: string | null;
        reminder_at?: string | null;
        reminder_rrule?: string | null;
      }
    ) =>
      requestJson<{ snipsel: Snipsel }>(`/api/snipsels/${snipselId}`, {
        method: 'PATCH',
        body: JSON.stringify(input),
      }),
    delete: (collectionId: string, snipselId: string) =>
      requestJson<{ ok: true }>(
        `/api/collections/${collectionId}/snipsels/${snipselId}`,
        { method: 'DELETE' }
      ),
    copy: (collectionId: string, snipselId: string) =>
      requestJson<{ item: CollectionItem }>(
        `/api/collections/${collectionId}/snipsels/${snipselId}/copy`,
        { method: 'POST' }
      ),
    reference: (collectionId: string, snipselId: string, indent?: number) =>
      requestJson<{ item: CollectionItem }>(
        `/api/collections/${collectionId}/snipsels/${snipselId}/reference`,
        { method: 'POST', body: JSON.stringify({ indent }) }
      ),
    reorder: (
      collectionId: string,
      items: Array<{ snipsel_id: string; position: number; indent: number }>
    ) =>
      requestJson<{ ok: true }>(
        `/api/collections/${collectionId}/snipsels/reorder`,
        {
          method: 'PATCH',
          body: JSON.stringify({ items }),
        }
      ),
    toggleReaction: (snipselId: string, emoji: string) =>
      requestJson<{ message: string; active: boolean }>(`/api/snipsels/${snipselId}/reactions`, {
        method: 'POST',
        body: JSON.stringify({ emoji }),
      }),
  },

  notifications: {
    list: () => requestJson<{ notifications: Notification[] }>('/api/notifications'),
    markRead: (id: string) => requestJson<{ success: boolean }>(`/api/notifications/${id}/mark-read`, { method: 'POST' }),
    markAllRead: () => requestJson<{ success: boolean }>('/api/notifications/mark-all-read', { method: 'POST' }),
    deleteRead: () => requestJson<{ success: boolean }>('/api/notifications/read', { method: 'DELETE' }),
    testPush: () => requestJson<{ success: boolean }>('/api/notifications/test-push', { method: 'POST' }),
  },

  attachments: {
    upload: async (snipselId: string, file: File, onProgress?: (percent: number) => void) => {
      return new Promise<{ attachment: Attachment }>((resolve, reject) => {
        const form = new FormData();
        form.append('file', file);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', `/api/snipsels/${snipselId}/attachments`);
        xhr.withCredentials = true;

        if (onProgress) {
          xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
              onProgress((e.loaded / e.total) * 100);
            }
          };
        }

        xhr.onload = () => {
          if (xhr.status === 413) {
            reject({
              error: {
                code: 'payload_too_large',
                message: 'Die Datei ist zu groß für den Upload.',
              },
            } as ApiError);
            return;
          }

          let data: any;
          try {
            data = JSON.parse(xhr.responseText);
          } catch {
            data = { error: { code: 'unknown_error', message: `Ein unerwarteter Fehler ist aufgetreten (${xhr.status}).` } };
          }

          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(data);
          } else {
            reject(data);
          }
        };

        xhr.onerror = () => {
          reject({ error: { code: 'network_error', message: 'Netzwerkfehler beim Upload.' } } as ApiError);
        };

        xhr.send(form);
      });
    },
    delete: async (attachmentId: string) => {
      const res = await fetch(`/api/attachments/${attachmentId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      const data = (await res.json()) as { ok: true } | ApiError;
      if (!res.ok) throw data;
      return data as { ok: true };
    },
    downloadUrl: (attachmentId: string) => `/api/attachments/${attachmentId}`,
    thumbnailUrl: (attachmentId: string) => `/api/attachments/${attachmentId}/thumbnail`,
  },

  search: (params: {
    q?: string;
    tag?: string;
    mention?: string;
    mentions_me?: boolean;
    type?: string;
    task_done?: boolean;
    include_archived?: boolean;
    day?: string;
    scope?: 'my' | 'shared' | 'all';
  }) => {
    const sp = new URLSearchParams();
    if (params.q) sp.set('q', params.q);
    if (params.tag) sp.set('tag', params.tag);
    if (params.mention) sp.set('mention', params.mention);
    if (params.mentions_me) sp.set('mentions_me', '1');
    if (params.type) sp.set('type', params.type);
    if (typeof params.task_done === 'boolean') sp.set('task_done', params.task_done ? '1' : '0');
    if (params.include_archived) sp.set('include_archived', '1');
    if (params.day) sp.set('day', params.day);
    if (params.scope) sp.set('scope', params.scope);
    const qs = sp.toString();
    return requestJson<SearchResponse>(`/api/search${qs ? `?${qs}` : ''}`);
  },

  tags: {
    list: (scope?: 'my' | 'shared' | 'all', q?: string) => {
      const sp = new URLSearchParams();
      if (scope) sp.set('scope', scope);
      if (q) sp.set('q', q);
      const qs = sp.toString();
      return requestJson<{ tags: TagCount[] }>(`/api/tags${qs ? `?${qs}` : ''}`);
    },
  },

  mentions: {
    list: (scope?: 'my' | 'shared' | 'all', q?: string) => {
      const sp = new URLSearchParams();
      if (scope) sp.set('scope', scope);
      if (q) sp.set('q', q);
      const qs = sp.toString();
      return requestJson<{ mentions: TagCount[] }>(`/api/mentions${qs ? `?${qs}` : ''}`);
    },
    getIncomingDayMentions: (day: string) => {
      return requestJson<{ snipsels: SearchSnipselHit[] }>(`/api/search/mentions/incoming?day=${encodeURIComponent(day)}`);
    },
  },

  importer: {
    twosLogin: (username: string, password: string) => {
      return requestJson<{ user: { id: string; username: string; token: string } }>(
        '/api/importer/twos/login',
        {
          method: 'POST',
          body: JSON.stringify({ username, password }),
        }
      );
    },
    twosLists: (lastSync: string, userId: string, token: string) => {
      return requestJson<{ lists: Array<{ id: string; name: string; isDaily: boolean; emoji: string }> }>(
        '/api/importer/twos/lists',
        {
          method: 'POST',
          body: JSON.stringify({ lastSync, userId, token }),
        }
      );
    },
    importFromTwoS: (input: { listIds: string[]; overwrite: boolean; token: string; userId: string }) => {
      return requestJson<{ imported: number; skipped: number; errors: string[] }>(
        '/api/importer/twos/import',
        {
          method: 'POST',
          body: JSON.stringify({ listIds: input.listIds, overwrite: input.overwrite, token: input.token, userId: input.userId }),
        }
      );
    },
    twosSearch: (query: string, userId: string, token: string) => {
      return requestJson<{ lists: Array<{ id: string; name: string; isDaily: boolean; emoji: string; thingsCount: number }> }>(
        '/api/importer/twos/search',
        {
          method: 'POST',
          body: JSON.stringify({ query, userId, token }),
        }
      );
    },
  },
  public: {
    getCollection: (token: string) =>
      requestJson<{
        collection: {
          id: string;
          title: string;
          icon: string;
          header_color: string | null;
          header_image_url: string | null;
          header_image_position: string | null;
          header_image_x_position: string | null;
          header_image_zoom: number | null;
          is_passcode_protected: boolean;
          is_unlocked: boolean;
          default_snipsel_type: string | null;
        }
      }>(`/api/public/collections/${token}`),
    verifyPasscode: (token: string, passcode: string) =>
      requestJson<{ ok: true }>(`/api/public/collections/${token}/passcode/verify`, {
        method: 'POST',
        body: JSON.stringify({ passcode }),
      }),
    listSnipsels: (token: string) =>
      requestJson<{ items: CollectionItem[], can_write: boolean }>(`/api/public/collections/${token}/snipsels`),
    createSnipsel: (token: string, input: { content_markdown: string; type: string; indent?: number }) =>
      requestJson<{ item: CollectionItem }>(`/api/public/collections/${token}/snipsels`, {
        method: 'POST',
        body: JSON.stringify(input),
      }),
    patchSnipsel: (token: string, snipselId: string, input: { content_markdown?: string; type?: string; task_done?: boolean }) =>
      requestJson<{ item: CollectionItem }>(`/api/public/collections/${token}/snipsels/${snipselId}`, {
        method: 'PATCH',
        body: JSON.stringify(input),
      }),
    deleteSnipsel: (token: string, snipselId: string) =>
      requestJson<{ ok: true }>(`/api/public/collections/${token}/snipsels/${snipselId}`, {
        method: 'DELETE',
      }),
  },
};
