let currentDraftGroup = "";
let currentDraftGroupName = "";
let selectedGroupKey = "ai";
let isPreviewMode = false;
let cachedArticles = [];

document.addEventListener('DOMContentLoaded', () => {
    loadGroups();
    loadStats();
    fetchHistory();
    document.getElementById('draft-btn').addEventListener('click', generateDraft);
    document.getElementById('topic-select').addEventListener('change', onGroupChange);

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            // Find the focused textarea and publish its draft
            const focused = document.activeElement;
            if (focused && focused.classList.contains('glass-input')) {
                const index = focused.dataset.index;
                if (index !== undefined) publishDraft(parseInt(index));
            }
        }
    });
});

// ─── Stats ────────────────────────────────────────────────────────────

async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        const stats = await res.json();

        document.getElementById('stat-total').textContent = stats.total_posts || 0;
        document.getElementById('stat-categories').textContent = (stats.categories || []).length;

        if (stats.last_posted) {
            const ago = timeAgo(new Date(stats.last_posted));
            document.getElementById('stat-last-posted').textContent = ago;
        } else {
            document.getElementById('stat-last-posted').textContent = 'Never';
        }
    } catch (e) {
        console.error('Failed to load stats', e);
    }
}

function timeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    if (seconds < 60) return 'Just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
}

// ─── Groups Dropdown ──────────────────────────────────────────────────

async function loadGroups() {
    try {
        const res = await fetch('/api/groups');
        const groups = await res.json();

        const select = document.getElementById('topic-select');
        select.innerHTML = '';

        groups.forEach(group => {
            const opt = document.createElement('option');
            opt.value = group.key;
            opt.dataset.icon = group.icon || "🌐";
            opt.textContent = group.name;
            if (group.key === selectedGroupKey) {
                opt.selected = true;
            }
            select.appendChild(opt);
        });

        updateSelectIcon();
    } catch (e) {
        console.error('Failed to load groups', e);
    }
}

function onGroupChange() {
    selectedGroupKey = document.getElementById('topic-select').value;
    updateSelectIcon();
}

function updateSelectIcon() {
    const select = document.getElementById('topic-select');
    const iconSpan = document.getElementById('select-icon');
    if (select.selectedIndex >= 0 && iconSpan) {
        const selectedOption = select.options[select.selectedIndex];
        iconSpan.textContent = selectedOption.dataset.icon || "🌐";
    }
}

// ─── History ─────────────────────────────────────────────────────────

async function fetchHistory() {
    const container = document.getElementById('history-container');
    try {
        const res = await fetch('/api/history');
        const data = await res.json();

        container.innerHTML = '';
        if (!data.length) {
            container.innerHTML = `<div class="empty-state">No posts yet. Choose a category and click "Draft New Options" to create one!</div>`;
            return;
        }

        data.forEach(item => {
            const date = new Date(item.timestamp).toLocaleString();
            const card = document.createElement('div');
            card.className = 'history-card';
            const badgeLabel = item.group_name || item.group || item.topic_name || item.topic;
            card.innerHTML = `
                <div class="card-header">
                    <span class="topic-badge">${badgeLabel}</span>
                    <span class="date">${date}</span>
                </div>
                <div class="card-content">${item.content.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>
            `;
            container.appendChild(card);
        });
    } catch (e) {
        showToast('Error loading history');
    }
}

// ─── LinkedIn Preview ─────────────────────────────────────────────────

function togglePreview() {
    isPreviewMode = !isPreviewMode;
    const btn = document.getElementById('preview-toggle');
    const container = document.getElementById('drafts-container');

    if (isPreviewMode) {
        btn.classList.add('active');
        container.classList.add('preview-mode');
    } else {
        btn.classList.remove('active');
        container.classList.remove('preview-mode');
    }

    // Re-render drafts in current mode
    const textareas = container.querySelectorAll('.glass-input');
    const cards = container.querySelectorAll('.draft-card');
    cards.forEach((card, i) => {
        const ta = card.querySelector('.glass-input');
        const previewEl = card.querySelector('.linkedin-preview');
        if (isPreviewMode) {
            if (ta) ta.style.display = 'none';
            if (previewEl) {
                previewEl.style.display = 'block';
                previewEl.innerHTML = renderLinkedInPreview(ta.value);
            }
        } else {
            if (ta) ta.style.display = '';
            if (previewEl) previewEl.style.display = 'none';
        }
    });
}

function renderLinkedInPreview(text) {
    const escaped = text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const charCount = text.length;
    const limitClass = charCount > 3000 ? 'over-limit' : charCount > 2700 ? 'near-limit' : '';

    return `
        <div class="li-card">
            <div class="li-header">
                <div class="li-avatar"></div>
                <div class="li-meta">
                    <div class="li-name">Your Name</div>
                    <div class="li-subtitle">Senior Engineer · 1m</div>
                </div>
            </div>
            <div class="li-body">${escaped}</div>
            <div class="li-char-indicator ${limitClass}">
                ${charCount} / 3,000 characters
            </div>
            <div class="li-actions">
                <span>👍 Like</span>
                <span>💬 Comment</span>
                <span>🔄 Repost</span>
                <span>📤 Send</span>
            </div>
        </div>
    `;
}

// ─── Draft Generation ─────────────────────────────────────────────────

async function generateDraft() {
    const btn = document.getElementById('draft-btn');
    const originalHtml = btn.innerHTML;

    const select = document.getElementById('topic-select');
    const groupName = select.options[select.selectedIndex]?.textContent || selectedGroupKey;

    btn.innerHTML = '<span class="icon spin">⌛</span> Drafting...';
    btn.disabled = true;
    showToast(`Fetching & ranking articles for "${groupName.trim()}"...`, 30000);

    try {
        const res = await fetch('/api/draft', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ group: selectedGroupKey })
        });
        const data = await res.json();

        if (data.status === 'success') {
            currentDraftGroup = data.group;
            currentDraftGroupName = data.group_name || data.group;

            const meta = document.getElementById('draft-meta');
            if (meta) {
                const articlesInfo = data.articles_count ? ` · ${data.articles_count} articles analyzed` : '';
                meta.innerHTML = `
                    <span class="meta-badge">${data.group_icon || "🌐"} ${currentDraftGroupName}</span>
                    <span class="meta-count">${data.drafts.length} options generated${articlesInfo}</span>
                `;
            }

            renderDraftCards(data.drafts);

            document.getElementById('draft-section').classList.remove('hidden');
            document.getElementById('draft-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
            showToast('✅ Drafts ready — pick your favorite and publish!');
        } else {
            showToast('⚠️ Error: ' + data.message, 6000);
        }
    } catch (e) {
        showToast('❌ Failed to contact the backend.', 5000);
    } finally {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
    }
}

function renderDraftCards(drafts) {
    const container = document.getElementById('drafts-container');
    container.innerHTML = '';
    container.classList.remove('preview-mode');
    isPreviewMode = false;
    const previewBtn = document.getElementById('preview-toggle');
    if (previewBtn) previewBtn.classList.remove('active');

    drafts.forEach((draftData, i) => {
        const isObj = typeof draftData === 'object' && draftData !== null;
        const draftText = isObj ? draftData.post : draftData;
        const score = isObj ? draftData.score : null;
        const reasoning = isObj ? draftData.reasoning : null;
        
        let scoreHtml = '';
        if (score) {
            let colorIcon = score >= 8 ? '🔥' : '📈';
            scoreHtml = `<div class="draft-score"><span class="score-badge">${colorIcon} Virality: ${score}/10</span> <span class="score-reason">${reasoning}</span></div>`;
        }

        const card = document.createElement('div');
        card.className = 'draft-card';
        card.style.animationDelay = `${i * 0.1}s`;
        card.innerHTML = `
            <div class="draft-header">
                <span class="draft-label">Option ${i + 1}</span>
                <span class="char-count" id="char-count-${i}">0 chars</span>
            </div>
            ${scoreHtml}
            <textarea id="draft-textarea-${i}" class="glass-input auto-expand" data-index="${i}">${draftText}</textarea>
            <div id="image-preview-container-${i}" class="image-preview" style="display:none;">
                <img id="image-preview-img-${i}" src="" alt="Draft Cover" />
            </div>
            <div class="linkedin-preview" style="display:none;"></div>
            <div class="draft-toolbar">
                <button onclick="selectAllDraft(${i})" class="icon-btn" title="Select All">✍️ Select</button>
                <button onclick="pasteDraft(${i})" class="icon-btn" title="Paste Over">📥 Paste</button>
                <button onclick="copyDraft(${i})" class="icon-btn" title="Copy">📋 Copy</button>
                <button onclick="regenerateSingle(${i})" id="regen-btn-${i}" class="icon-btn" title="Regenerate this draft">🔄 Regen</button>
                <button onclick="generateImage(${i})" id="img-btn-${i}" class="icon-btn" title="Generate AI Cover Image">🖼️ Img</button>
            </div>
            <button onclick="publishDraft(${i})" id="publish-btn-${i}" class="glass-btn success-btn publish-btn">✅ Publish to LinkedIn</button>
        `;
        container.appendChild(card);

        const ta = document.getElementById(`draft-textarea-${i}`);
        const updateCount = () => {
            const count = ta.value.length;
            const el = document.getElementById(`char-count-${i}`);
            el.textContent = `${count} chars`;
            el.className = 'char-count' + (count > 3000 ? ' over-limit' : count > 2700 ? ' near-limit' : '');
            
            ta.style.height = 'auto';
            ta.style.height = (ta.scrollHeight) + 'px';
        };
        ta.addEventListener('input', updateCount);
        setTimeout(updateCount, 10);
    });
}

// ─── Regenerate Single Draft ──────────────────────────────────────────

window.draftImageBase64 = {};

window.regenerateSingle = async function(index) {
    const btn = document.getElementById(`regen-btn-${index}`);
    const originalHtml = btn.innerHTML;
    btn.innerHTML = '<span class="spin">⏳</span>';
    btn.disabled = true;

    // Collect all other drafts
    const allTextareas = document.querySelectorAll('.glass-input');
    const existingDrafts = [];
    allTextareas.forEach((ta, i) => {
        if (i !== index) existingDrafts.push(ta.value);
    });

    try {
        const res = await fetch('/api/regenerate-single', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                group: currentDraftGroup,
                existing_drafts: existingDrafts
            })
        });
        const data = await res.json();

        if (data.status === 'success') {
            const ta = document.getElementById(`draft-textarea-${index}`);
            ta.value = data.draft;
            ta.dispatchEvent(new Event('input'));

            // Flash animation
            const card = ta.closest('.draft-card');
            card.classList.add('regen-flash');
            setTimeout(() => card.classList.remove('regen-flash'), 600);

            showToast('🔄 Draft regenerated!');
        } else {
            showToast('⚠️ ' + data.message, 5000);
        }
    } catch (e) {
        showToast('❌ Regeneration failed.', 5000);
    } finally {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
    }
};

// ─── Utility Actions (Select All, Paste, Copy) ──────────────────────

window.selectAllDraft = function (index) {
    const ta = document.getElementById(`draft-textarea-${index}`);
    ta.focus();
    ta.setSelectionRange(0, ta.value.length);
};

window.pasteDraft = async function (index) {
    try {
        const text = await navigator.clipboard.readText();
        const ta = document.getElementById(`draft-textarea-${index}`);
        ta.value = text;
        ta.dispatchEvent(new Event('input')); // trigger autogrow and count
        showToast('📥 Pasted from clipboard!');
    } catch (err) {
        showToast('⚠️ Unable to paste. Please allow clipboard permissions.', 4000);
    }
};

window.copyDraft = function (index) {
    const content = document.getElementById(`draft-textarea-${index}`).value;
    navigator.clipboard.writeText(content).then(() => showToast('📋 Copied to clipboard!'));
};

window.generateImage = async function (index) {
    const btn = document.getElementById(`img-btn-${index}`);
    const ta = document.getElementById(`draft-textarea-${index}`);
    btn.disabled = true;
    btn.innerHTML = '<span class="spin">⏳</span>...';
    
    try {
        const response = await fetch('/api/generate-image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                draft: ta.value,
                group: currentDraftGroup,
                group_name: currentDraftGroupName
            })
        });
        const data = await response.json();
        if (data.status === 'success') {
            window.draftImageBase64[index] = data.image_base64;
            const container = document.getElementById(`image-preview-container-${index}`);
            const img = document.getElementById(`image-preview-img-${index}`);
            img.src = "data:image/jpeg;base64," + data.image_base64;
            container.style.display = "block";
            showToast('🖼️ Image Generated!');
        } else {
            showToast('⚠️ Image generation failed: ' + data.message, 4000);
        }
    } catch (e) {
        showToast('⚠️ API Exception: ' + e.message, 4000);
    }
    btn.disabled = false;
    btn.innerHTML = '🖼️ Img';
};

// ─── Discard ──────────────────────────────────────────────────────────

function discardDrafts() {
    document.getElementById('draft-section').classList.add('hidden');
    document.getElementById('drafts-container').innerHTML = '';
    showToast('🗑️ Drafts discarded.');
}
window.discardDrafts = discardDrafts;

// ─── Publish ──────────────────────────────────────────────────────────

window.publishDraft = async function (index) {
    const btn = document.getElementById(`publish-btn-${index}`);
    const content = document.getElementById(`draft-textarea-${index}`).value;
    if (!content.trim()) return;

    btn.innerHTML = 'Publishing...';
    btn.disabled = true;

    const image_base64 = window.draftImageBase64[index] || null;

    try {
        const res = await fetch('/api/publish', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                content, 
                group: currentDraftGroup, 
                group_name: currentDraftGroupName,
                image_base64: image_base64
            })
        });
        const data = await res.json();

        if (data.status === 'success') {
            showToast('✅ Published to LinkedIn!');
            discardDrafts();
            fetchHistory();
            loadStats();
        } else {
            showToast('⚠️ ' + data.message, 5000);
            btn.innerHTML = `✅ Publish`;
            btn.disabled = false;
        }
    } catch (e) {
        showToast('❌ Publish failed.', 5000);
        btn.innerHTML = `✅ Publish`;
        btn.disabled = false;
    }
};

// ─── Toast ────────────────────────────────────────────────────────────

let toastTimer = null;
function showToast(message, duration = 4000) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.remove('hidden');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.add('hidden'), duration);
}
