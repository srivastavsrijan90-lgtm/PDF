/* PDF Studio — Frontend Logic */

const state = {
  files: {},
  rotation: 90,
};

const TOOL_META = {
  merge:          { title: 'Merge PDFs',        desc: 'Combine multiple PDF files into a single document', color: '#7c6df0' },
  split:          { title: 'Split PDF',         desc: 'Extract specific pages into separate files', color: '#f472b6' },
  rotate:         { title: 'Rotate PDF',        desc: 'Rotate pages clockwise or counter-clockwise', color: '#22d3ee' },
  compress:       { title: 'Compress PDF',      desc: 'Reduce file size by optimizing content streams', color: '#fbbf24' },
  'extract-text': { title: 'Extract Text',      desc: 'Pull all readable text from your PDF into a .txt file', color: '#34d399' },
  watermark:      { title: 'Add Watermark',     desc: 'Stamp a diagonal text watermark on every page', color: '#60a5fa' },
  reorder:        { title: 'Reorder Pages',     desc: 'Rearrange pages in a custom order', color: '#e879f9' },
  'images-to-pdf':{ title: 'Images to PDF',     desc: 'Convert one or more images into a single PDF document', color: '#fb923c' },
};

// ── Utilities ──

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icon = type === 'success' ? '✓' : '✕';
  toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    toast.style.transition = '0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function showLoading(show) {
  document.getElementById('loadingOverlay').classList.toggle('active', show);
}

async function downloadResponse(response, fallbackName) {
  if (!response.ok) {
    const err = await response.json().catch(() => ({ error: 'Request failed' }));
    throw new Error(err.error || 'Something went wrong');
  }
  const blob = await response.blob();
  const disposition = response.headers.get('Content-Disposition') || '';
  const match = disposition.match(/filename[^;=\n]*=(['"]?)([^'"\n]*?)\1/);
  const filename = match ? match[2] : fallbackName;

  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

// ── Navigation ──

function switchTool(tool) {
  document.querySelectorAll('.nav-item').forEach(t => {
    t.classList.toggle('active', t.dataset.tool === tool);
  });
  document.querySelectorAll('.tool-panel').forEach(p => p.classList.remove('active'));
  const panel = document.getElementById(`panel-${tool}`);
  if (panel) panel.classList.add('active');

  document.querySelectorAll('.mob-tab').forEach(t => {
    if (t.dataset.tool) t.classList.toggle('active', t.dataset.tool === tool);
  });

  const meta = TOOL_META[tool];
  if (meta) {
    document.documentElement.style.setProperty('--tool-accent', meta.color);
    document.documentElement.style.setProperty('--tool-glow', meta.color + '40');

    const titleEl = document.getElementById('pageTitle');
    const descEl = document.getElementById('pageDesc');
    titleEl.style.opacity = '0';
    descEl.style.opacity = '0';
    setTimeout(() => {
      titleEl.textContent = meta.title;
      descEl.textContent = meta.desc;
      titleEl.style.opacity = '1';
      descEl.style.opacity = '1';
    }, 150);
  }

  closeMobSheet();
}

document.querySelectorAll('.nav-item').forEach(tab => {
  tab.addEventListener('click', () => switchTool(tab.dataset.tool));
});

document.querySelectorAll('.mob-tab[data-tool]').forEach(tab => {
  tab.addEventListener('click', () => switchTool(tab.dataset.tool));
});

document.querySelectorAll('.mob-sheet-item').forEach(btn => {
  btn.addEventListener('click', () => switchTool(btn.dataset.tool));
});

const mobSheet = document.getElementById('mobSheet');
document.getElementById('mobMore').addEventListener('click', () => mobSheet.classList.add('open'));
document.getElementById('mobBackdrop').addEventListener('click', closeMobSheet);

function closeMobSheet() {
  mobSheet.classList.remove('open');
}

// ── Dropzone Setup ──

const toolIds = [
  'merge', 'split', 'rotate', 'compress',
  'extract-text', 'watermark', 'reorder', 'images-to-pdf',
];

toolIds.forEach(id => {
  const dropzone = document.getElementById(`dropzone-${id}`);
  const input = dropzone.querySelector('input[type="file"]');
  const multiple = dropzone.dataset.multiple === 'true';

  dropzone.addEventListener('click', e => {
    if (e.target.closest('.file-item-remove')) return;
    input.click();
  });

  dropzone.addEventListener('dragover', e => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));

  dropzone.addEventListener('drop', e => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    handleFiles(id, [...e.dataTransfer.files], multiple);
  });

  input.addEventListener('change', () => {
    handleFiles(id, [...input.files], multiple);
    input.value = '';
  });
});

function handleFiles(toolId, newFiles, multiple) {
  if (!multiple) {
    state.files[toolId] = newFiles.slice(0, 1);
  } else {
    state.files[toolId] = [...(state.files[toolId] || []), ...newFiles];
  }
  renderFileList(toolId);
  updateButtonState(toolId);
}

function renderFileList(toolId) {
  const list = document.getElementById(`filelist-${toolId}`);
  const files = state.files[toolId] || [];
  list.innerHTML = '';

  files.forEach((file, idx) => {
    const li = document.createElement('li');
    li.className = 'file-item';
    const isImage = file.type.startsWith('image/');
    li.innerHTML = `
      <div class="file-item-icon ${isImage ? 'image' : ''}">${isImage ? '🖼️' : '📄'}</div>
      <div class="file-item-info">
        <span class="file-item-name">${file.name}</span>
        <span class="file-item-size">${formatSize(file.size)}</span>
      </div>
      <button class="file-item-remove" data-tool="${toolId}" data-idx="${idx}" title="Remove">×</button>
    `;
    list.appendChild(li);
  });

  list.querySelectorAll('.file-item-remove').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      const t = btn.dataset.tool;
      const i = parseInt(btn.dataset.idx);
      state.files[t].splice(i, 1);
      renderFileList(t);
      updateButtonState(t);
    });
  });
}

function updateButtonState(toolId) {
  const files = state.files[toolId] || [];
  const btn = document.getElementById(`btn-${toolId}`);
  if (!btn) return;

  if (toolId === 'merge') {
    btn.disabled = files.length < 2;
  } else {
    btn.disabled = files.length < 1;
  }
}

// ── Rotation Buttons ──

document.querySelectorAll('#rotationGroup .btn-option').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#rotationGroup .btn-option').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.rotation = parseInt(btn.dataset.value);
  });
});

// ── API Actions ──

async function submitForm(endpoint, formData, fallbackName) {
  showLoading(true);
  try {
    const response = await fetch(endpoint, { method: 'POST', body: formData });
    await downloadResponse(response, fallbackName);
    showToast('Download started successfully!');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
}

document.getElementById('btn-merge').addEventListener('click', () => {
  const fd = new FormData();
  (state.files['merge'] || []).forEach(f => fd.append('files', f));
  submitForm('/api/merge', fd, 'merged.pdf');
});

document.getElementById('btn-split').addEventListener('click', () => {
  const fd = new FormData();
  fd.append('file', state.files['split'][0]);
  fd.append('ranges', document.getElementById('ranges').value);
  submitForm('/api/split', fd, 'split.pdf');
});

document.getElementById('btn-rotate').addEventListener('click', () => {
  const fd = new FormData();
  fd.append('file', state.files['rotate'][0]);
  fd.append('rotation', state.rotation);
  fd.append('pages', document.getElementById('rotate-pages').value);
  submitForm('/api/rotate', fd, 'rotated.pdf');
});

document.getElementById('btn-compress').addEventListener('click', () => {
  const fd = new FormData();
  fd.append('file', state.files['compress'][0]);
  submitForm('/api/compress', fd, 'compressed.pdf');
});

document.getElementById('btn-extract-text').addEventListener('click', () => {
  const fd = new FormData();
  fd.append('file', state.files['extract-text'][0]);
  submitForm('/api/extract-text', fd, 'extracted_text.txt');
});

document.getElementById('btn-watermark').addEventListener('click', () => {
  const fd = new FormData();
  fd.append('file', state.files['watermark'][0]);
  fd.append('watermark', document.getElementById('watermark-text').value);
  submitForm('/api/watermark', fd, 'watermarked.pdf');
});

document.getElementById('btn-reorder').addEventListener('click', () => {
  const order = document.getElementById('page-order').value.trim();
  if (!order) {
    showToast('Please enter a page order', 'error');
    return;
  }
  const fd = new FormData();
  fd.append('file', state.files['reorder'][0]);
  fd.append('order', order);
  submitForm('/api/reorder', fd, 'reordered.pdf');
});

document.getElementById('btn-images-to-pdf').addEventListener('click', () => {
  const fd = new FormData();
  (state.files['images-to-pdf'] || []).forEach(f => fd.append('files', f));
  submitForm('/api/images-to-pdf', fd, 'images.pdf');
});

// Page title transition
document.getElementById('pageTitle').style.transition = 'opacity 0.2s';
document.getElementById('pageDesc').style.transition = 'opacity 0.2s';

// ── Theme Toggle ──

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('pdf-studio-theme', theme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  setTheme(current === 'dark' ? 'light' : 'dark');
}

const savedTheme = localStorage.getItem('pdf-studio-theme');
if (savedTheme) setTheme(savedTheme);

document.getElementById('themeToggle')?.addEventListener('click', toggleTheme);
document.getElementById('themeToggleMobile')?.addEventListener('click', toggleTheme);

// Set initial tool accent
switchTool('merge');
