# Snipsel - User Documentation

## Purpose

Snipsel is a personal knowledge management application that helps you organize notes, tasks, and ideas in collections. It combines the flexibility of a note-taking app with powerful features like tagging, mentions, and search to help you quickly find and connect your information.

## Key Features (Overview)

- **Collections** - Organize your content into themed collections
- **Daily Collections** - Automatic daily notes for each day
- **Snipsels** - Individual notes within collections (text, tasks, links, images)
- **Tags** - Categorize snipsels with #hashtags
- **Mentions** - Reference other users with @username
- **Search** - Find content across all collections
- **Sharing** - Share collections with other users
- **Passcode Protection** - Secure sensitive collections
- **Notifications** - Stay informed about mentions and task assignments

---

## Collections

### What is a Collection?

A collection is a container for related snipsels. Think of it like a notebook or folder. Each collection has:
- **Title** - Name of the collection
- **Icon** - Emoji icon for visual identification
- **Header Color** - Custom color for the collection header
- **Default Snipsel Type** - Preferred type for new snipsels

### Regular Collections

Regular collections are manual containers you create to organize content thematically. Examples:
- "Project Ideas"
- "Meeting Notes"
- "Reading List"

### Daily Collections

Daily collections are automatically created for each day. They provide a quick way to capture daily thoughts, tasks, and notes without creating a collection manually.

**Key behaviors:**
- One collection per day per user (unique by owner + date)
- Shown in the Calendar view
- When viewing your daily collection, you can see snipsels from other users that mention you (read-only)
- Useful for daily standups, journal entries, or daily task lists

![Screenshot: Daily Collection in Calendar View - PLACEHOLDER]

### Creating a Collection

1. Click the **+** button in the sidebar
2. Enter a title for the collection
3. Optionally select an icon and header color
4. Choose a default snipsel type (optional)
5. Click **Create**

### Collection Settings

Access collection settings by clicking the collection menu (three dots) and selecting **Settings**. Options include:
- Rename collection
- Change icon and color
- Set default snipsel type
- Enable/disable passcode protection
- Archive collection
- Delete collection

---

## Snipsels

### What is a Snipsel?

A snipsel is an individual item within a collection. It's the basic unit of content in Snipsel.

### Snipsel Types

1. **Text** - Plain text or markdown content
2. **Task** - A task that can be marked as done/undone
3. **Link** - External URL with optional label
4. **Image** - Image attachments displayed in a grid
5. **Attachment** - File attachments

### Creating a Snipsel

1. Open a collection
2. Click **Add new snipsel** (or press Enter after the last snipsel)
3. The new snipsel inherits the indent level from the previous snipsel
4. Select the type using the dropdown (text, task, link, image)
5. Enter content and press **Save**

### Editing Snipsel Content

- Click on any snipsel to edit it
- Supports Markdown formatting
- Tags and mentions are automatically extracted and linked

### Task Management

For **task** type snipsels:
- Click the checkbox to mark as done/undone
- Done tasks show a strikethrough
- Tasks assigned to you via @mention will appear in your notifications

### Attachments

**Image Type:**
- Click to upload images
- Images display in a grid layout
- Click any image to view full size
- Thumbnails are auto-generated with correct rotation (EXIF-aware)

**Attachment Type:**
- Upload any file type
- Files show as download links
- Maximum file size: 10MB per file

![Screenshot: Snipsel with image attachments - PLACEHOLDER]

### Indent / Nesting

Snipsels can be indented to create hierarchy:
- Use the indent controls on the snipsel (or keyboard shortcuts)
- Indented snipsels are visually nested
- Helps organize related content

---

## Tags

### Using Tags

Tags are words prefixed with `#` that help categorize snipsels. Examples:
- `#project-alpha`
- `#ideas`
- `#read-later`

### How Tags Work

1. Add `#tagname` anywhere in snipsel content
2. Tags are automatically detected when saving
3. Tags are linked to the snipsel owner
4. You can filter snipsels by tag

### Tag Scope

When searching or filtering tags, you can choose scope:
- **My tags** - Tags you created (#mytag)
- **Shared tags** - Tags from others (#someone-else)
- **All tags** - Everything

### Tag Navigation

- Click any tag to filter snipsels by that tag
- Tags page shows all tags with snipsel counts

![Screenshot: Tag filtering - PLACEHOLDER]

---

## Mentions

### Using Mentions

Mention other users with `@username` to:
- Notify them about relevant content
- Assign tasks to them
- Reference their input

### How Mentions Work

1. Type `@username` in any snipsel
2. When saved, the mentioned user receives a notification
3. For tasks: "User assigned a task to you"
4. For other content: "User mentioned you in a snipsel"

### Viewing Mentions

**In your collection:**
- Mentions you receive appear in notifications

**In Daily Collections:**
- When viewing your daily collection, you see snipsels from other users that mention you
- These are shown in a "Mentioned by others on this day" section
- Read-only view (you can see but not edit)
- Shows the author's username

![Screenshot: Incoming mentions in daily collection - PLACEHOLDER]

### Mention Notifications

Notifications are sent for:
- Being mentioned in any snipsel
- Being assigned a task
- Collection sharing invitations

---

## Search

### Basic Search

Enter search terms in the search bar to find snipsels across all your collections.

### Search Behavior

- **AND Logic**: All search terms must match
- Example: Searching "project meeting" finds snipsels containing BOTH "project" AND "meeting"
- Searches: snipsel content, external URLs, external labels

### Search Filters

You can narrow search results with:
- **Type**: text, task, link, image, attachment
- **Tag**: Filter by specific tag
- **Mention**: Filter by mention (@user)
- **Day**: Filter by date
- **Scope**: my, shared, or all collections
- **Task Done**: Filter completed/incomplete tasks

### Search Results

Results show:
- Snipsel content preview
- Collection it belongs to
- Last modified date
- Write access indicator

---

## Permissions & Sharing

### Permission Levels

1. **Owner** - Full control, can delete collection
2. **Write** - Can add/edit snipsels
3. **Read** - View-only access

### Sharing a Collection

1. Open collection settings
2. Click **Share**
3. Enter the username to share with
4. Select permission (Read or Write)
5. The shared user will see the collection in their sidebar

### Sharing Daily Collections

**Important distinction:**

| Feature | Regular Collections | Daily Collections |
|---------|--------------------|--------------------|
| Manual sharing | Yes - via collection settings | No - cannot share |
| Visibility | Only owner + shared users | Only owner (private) |
| Cross-user mentions | Read-only in mentions section | Yes - view others' snipsels mentioning you |

**Daily Collections:**
- Cannot be shared through settings
- However, when OTHER users mention you in THEIR daily collections, you can see those mentions in YOUR daily collection
- This enables cross-user collaboration on the same day without explicit sharing

### Passcode Protection

Protect sensitive collections with a passcode:
1. Open collection settings
2. Enable **Passcode Protection**
3. Set a passcode
4. Users must enter passcode to view collection content

---

## Notifications

### Notification Types

1. **Mention** - Someone mentioned you in a snipsel
2. **Task Assignment** - You were assigned a task
3. **Share** - A collection was shared with you

### Viewing Notifications

- Click the bell icon in the header
- Shows unread count badge
- Click to mark as read
- Click notification to jump to relevant snipsel

---

## Calendar View

The calendar shows your daily collections organized by date.

### Features

- Month view with dots indicating days with collections
- Click any day to view that day's collection
- Navigate between months
- Today's collection highlighted

![Screenshot: Calendar View - PLACEHOLDER]

---

## Settings

### Personal Settings

Access via the settings icon (gear):
- Change username
- View account info

### Collection Settings

Per-collection settings (accessed via collection menu):
- Title, icon, color
- Default snipsel type
- Passcode protection
- Sharing management
- Archive/Delete

---

## Keyboard Shortcuts

- **Enter** after last snipsel: Create new snipsel
- **Tab**: Increase indent
- **Shift+Tab**: Decrease indent
- **Ctrl+Enter**: Save snipsel (when editing)

---

## Technical Notes

### Image Handling

- Thumbnails are auto-generated for images
- EXIF rotation metadata is respected (photos from phones display correctly)
- Supported formats: JPEG, PNG, GIF, WebP

### Data Storage

- All data stored in SQLite database
- File uploads stored in `./uploads/` directory
- Automatic thumbnail generation

### Security

- Sessions managed via secure cookies
- Passwords hashed with bcrypt
- Passcode collections require code to access
