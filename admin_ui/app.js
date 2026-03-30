let currentDraftGroup = "";
let currentDraftGroupName = "";
let selectedGroupKey = "ai";

document.addEventListener('DOMContentLoaded', () => {
    loadGroups();
    fetchHistory();
    document.getElementById('draft-btn').addEventListener('click', generateDraft);
    document.getElementById('topic-select').addEventListener('change', onGroupChange);
});

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
            // Store icon in data attribute for easy retrieval
            opt.dataset.icon = group.icon || "🌐";
            opt.textContent = group.name;
            if (group.key === selectedGroupKey) {
                opt.selected = true;
            }
            select.appendChild(opt);
        });

        // Initialize icon immediately
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
            // handle old records that used topic or topic_name
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

            // Update meta label
            const meta = document.getElementById('draft-meta');
            if (meta) {
                meta.innerHTML = `
                    <span class="meta-badge">${data.group_icon || "🌐"} ${currentDraftGroupName}</span>
                    <span class="meta-count">${data.drafts.length} options generated</span>
                `;
            }

            const container = document.getElementById('drafts-container');
            container.innerHTML = '';

            data.drafts.forEach((draftText, i) => {
                const card = document.createElement('div');
                card.className = 'draft-card';
                card.style.animationDelay = `${i * 0.1}s`;
                card.innerHTML = `
                    <div class="draft-header">
                        <span class="draft-label">Option ${i + 1}</span>
                        <span class="char-count" id="char-count-${i}">0 chars</span>
                    </div>
                    <textarea id="draft-textarea-${i}" class="glass-input" data-index="${i}">${draftText}</textarea>
                    <div class="draft-actions">
                        <button onclick="copyDraft(${i})" class="glass-btn copy-btn">📋 Copy</button>
                        <button onclick="publishDraft(${i})" id="publish-btn-${i}" class="glass-btn success-btn">✅ Publish</button>
                    </div>
                `;
                container.appendChild(card);

                // Wire up char counter
                const ta = document.getElementById(`draft-textarea-${i}`);
                const updateCount = () => {
                    document.getElementById(`char-count-${i}`).textContent = `${ta.value.length} chars`;
                };
                ta.addEventListener('input', updateCount);
                updateCount();
            });

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

// ─── Copy Draft ───────────────────────────────────────────────────────

window.copyDraft = function (index) {
    const content = document.getElementById(`draft-textarea-${index}`).value;
    navigator.clipboard.writeText(content).then(() => showToast('📋 Copied to clipboard!'));
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

    try {
        const res = await fetch('/api/publish', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, group: currentDraftGroup, group_name: currentDraftGroupName })
        });
        const data = await res.json();

        if (data.status === 'success') {
            showToast('✅ Published to LinkedIn!');
            discardDrafts();
            fetchHistory();
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
