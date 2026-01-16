// Format Video Enrichment Response
const response = $input.first().json;

if (response.error) {
  return {
    success: false,
    message: `❌ Video konnte nicht analysiert werden: ${response.error}\n\n💡 Unterstützte Plattformen:\n- YouTube (youtube.com, youtu.be)\n- Vimeo (vimeo.com)\n- Brightcove (players.brightcove.net)\n- Direct MP4/WebM/MOV`
  };
}

// Format duration
const formatDuration = (seconds) => {
  if (!seconds) return null;
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  if (hours > 0) return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  return `${minutes}:${String(secs).padStart(2, '0')}`;
};

// Format file size
const formatFileSize = (bytes) => {
  if (!bytes) return null;
  const mb = bytes / 1024 / 1024;
  return `${mb.toFixed(1)} MB`;
};

// Build formatted response
let message = `🎬 VIDEO ERFOLGREICH ANALYSIERT!\n\n`;

if (response.title) {
  message += `📌 Titel: ${response.title}\n`;
}

if (response.platform) {
  const platformName = response.platform.charAt(0).toUpperCase() + response.platform.slice(1);
  message += `🌐 Platform: ${platformName}\n`;
}

const duration = formatDuration(response.duration);
if (duration) {
  message += `⏱️ Dauer: ${duration}\n`;
}

const metadata = response.metadata || {};

if (metadata.resolution) {
  message += `📐 Auflösung: ${metadata.resolution}\n`;
}

const fileSize = formatFileSize(metadata.file_size);
if (fileSize) {
  message += `💾 Dateigröße: ${fileSize}\n`;
}

if (response.channel_title) {
  message += `👤 Kanal: ${response.channel_title}\n`;
}

if (response.view_count) {
  message += `👁️ Aufrufe: ${response.view_count.toLocaleString('de-DE')}\n`;
}

if (response.like_count) {
  message += `👍 Likes: ${response.like_count.toLocaleString('de-DE')}\n`;
}

if (metadata.models && metadata.models.length > 0) {
  message += `📋 Modelle: ${metadata.models.join(', ')}\n`;
}

// Only show description if different from title
if (response.description && response.description !== response.title) {
  const desc = response.description.substring(0, 150);
  message += `\n📝 ${desc}${response.description.length > 150 ? '...' : ''}\n`;
}

if (response.thumbnail_url) {
  message += `\n🖼️ Thumbnail verfügbar\n`;
}

if (response.database_id) {
  message += `\n✅ Video gespeichert`;
  if (response.linked_products > 0) {
    message += ` (${response.linked_products} Produkte verknüpft)`;
  }
  message += '\n';
}

return {
  success: true,
  message: message,
  raw_data: response
};
