// Format Response Node - Error Code Search V6
// Copy this into N8N Code Node

let results = $input.first().json;

// Debug: Check what we got
console.log('Results type:', typeof results);
console.log('Results keys:', Object.keys(results));
console.log('Results:', JSON.stringify(results).substring(0, 500));

// Supabase returns array directly from RPC call
if (!Array.isArray(results)) {
  console.log('Not an array, wrapping...');
  results = [results];
}

console.log('After processing - Array length:', results.length);
if (results.length > 0) {
  console.log('First item keys:', Object.keys(results[0]));
  console.log('First item:', JSON.stringify(results[0]));
}

if (!results || results.length === 0) {
  return {
    success: false,
    message: 'Error Code nicht gefunden!\n\nBitte pruefe:\n- Ist der Code korrekt? (z.B. 30.03.30)\n- Ist der Hersteller korrekt?\n- Ist das Modell korrekt?'
  };
}

// Group by source type and document type
const documents = results.filter(r => r.source_type === 'document');
const videos = results.filter(r => r.source_type === 'video');
const relatedVideos = results.filter(r => r.source_type === 'related_video');

// Further group documents by type
const serviceManuals = documents.filter(d => {
  const docType = d.metadata?.document_type || '';
  return docType === 'service_manual' || docType === 'cpmd';
});
const bulletins = documents.filter(d => {
  const docType = d.metadata?.document_type || '';
  return docType === 'service_bulletin';
});
const partsCatalogs = documents.filter(d => {
  const docType = d.metadata?.document_type || '';
  return docType === 'parts_catalog';
});

// Combine all videos (direct + related)
const allVideos = [...videos, ...relatedVideos];

let message = '🔴 ERROR CODE: ' + results[0].code + '\n';
if (results[0].error_description) {
  message += '📝 ' + results[0].error_description + '\n';
}
message += '\n';

// Service Manuals & CPMD
if (serviceManuals.length > 0) {
  message += '📖 DOKUMENTATION (' + serviceManuals.length + '):\n\n';
  
  serviceManuals.forEach((doc, i) => {
    message += (i+1) + '. ' + doc.source_title;
    if (doc.page_number) {
      message += ' (Seite ' + doc.page_number + ')';
    }
    message += '\n';
    
    if (doc.solution_text) {
      const solution = doc.solution_text.substring(0, 150);
      message += '   💡 Loesung: ' + solution;
      if (doc.solution_text.length > 150) {
        message += '...';
      }
      message += '\n';
    }
    
    if (doc.parts_list) {
      message += '   🔧 Parts: ' + doc.parts_list + '\n';
    }
    message += '\n';
  });
}

// Service Bulletins
if (bulletins.length > 0) {
  message += '📋 SERVICE BULLETINS (' + bulletins.length + '):\n\n';
  
  bulletins.forEach((doc, i) => {
    message += (i+1) + '. ' + doc.source_title;
    if (doc.page_number) {
      message += ' (Seite ' + doc.page_number + ')';
    }
    message += '\n';
    
    if (doc.solution_text) {
      const solution = doc.solution_text.substring(0, 150);
      message += '   📄 Info: ' + solution;
      if (doc.solution_text.length > 150) {
        message += '...';
      }
      message += '\n';
    }
    message += '\n';
  });
}

// Parts Catalogs
if (partsCatalogs.length > 0) {
  message += '🔧 ERSATZTEILE (' + partsCatalogs.length + '):\n\n';
  
  partsCatalogs.forEach((doc, i) => {
    message += (i+1) + '. ' + doc.source_title;
    if (doc.page_number) {
      message += ' (Seite ' + doc.page_number + ')';
    }
    message += '\n';
    
    if (doc.parts_list) {
      message += '   🔩 Parts: ' + doc.parts_list + '\n';
    }
    message += '\n';
  });
}

// All Videos (combined, no duplicates)
if (allVideos.length > 0) {
  message += '\n🎬 VIDEOS (' + allVideos.length + '):\n\n';
  
  allVideos.forEach((vid, i) => {
    message += (i+1) + '. ' + vid.source_title;
    if (vid.video_duration) {
      const mins = Math.floor(vid.video_duration / 60);
      const secs = vid.video_duration % 60;
      message += ' (' + mins + ':' + String(secs).padStart(2, '0') + ')';
    }
    
    // Mark if it's a related video (keyword match)
    if (vid.source_type === 'related_video') {
      message += ' (verwandt)';
    }
    message += '\n';
    
    if (vid.solution_text) {
      const solution = vid.solution_text.substring(0, 100);
      message += '   ' + solution;
      if (vid.solution_text.length > 100) {
        message += '...';
      }
      message += '\n';
    }
    
    if (vid.video_url) {
      message += '   🔗 Link: ' + vid.video_url + '\n';
    }
    message += '\n';
  });
}

message += '\n💡 Moechtest du mehr Details zu einem der Quellen?';

return {
  success: true,
  message: message,
  raw_data: {
    documents: documents,
    videos: videos,
    related_videos: relatedVideos,
    total_sources: results.length
  }
};
