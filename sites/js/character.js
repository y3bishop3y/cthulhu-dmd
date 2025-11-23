// Character detail page JavaScript

// Theme management (use themes from app.js which is loaded first)
// Don't redeclare const - just use window.themes directly
if (!window.themes) {
    window.themes = {
        green: 'theme-green',
        yellow: 'theme-yellow',
        purple: 'theme-purple',
        red: 'theme-red',
        blue: 'theme-blue',
        cyan: 'theme-cyan'
    };
}
// Use window.themes directly instead of creating a const alias

// Initialize theme
function initializeTheme() {
    const savedTheme = localStorage.getItem('cthulhu-theme') || 'green';
    const body = document.body;
    body.className = body.className.replace(/theme-\w+/g, '');
    if (window.themes && window.themes[savedTheme]) {
        body.classList.add(window.themes[savedTheme]);
    } else {
        body.classList.add('theme-green');
    }
}

// Render breadcrumbs
function renderBreadcrumbs(items) {
    let html = '<nav class="mb-6 text-sm"><ol class="flex items-center space-x-2">';
    
    items.forEach((item, index) => {
        const isLast = index === items.length - 1;
        html += '<li class="flex items-center">';
        
        if (!isLast && item.url) {
            html += `<a href="${item.url}" class="text-primary hover:text-primary-hover">${item.label}</a>`;
        } else {
            html += `<span class="${isLast ? 'text-gray-300 font-semibold' : 'text-gray-400'}">${item.label}</span>`;
        }
        
        if (!isLast) {
            html += '<span class="mx-2 text-gray-500">›</span>';
        }
        
        html += '</li>';
    });
    
    html += '</ol></nav>';
    return html;
}

// Format season name
function formatSeasonName(seasonId) {
    if (seasonId.startsWith('season')) {
        const num = seasonId.replace('season', '');
        return `Season ${num}`;
    }
    // Convert kebab-case to Title Case
    return seasonId.split('-').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

// Load character data
async function loadCharacter() {
    console.log('loadCharacter called');
    
    // Get parameters from URL
    const params = new URLSearchParams(window.location.search);
    const seasonId = params.get('season');
    const characterId = params.get('character');
    
    console.log('Season:', seasonId, 'Character:', characterId);
    
    if (!seasonId || !characterId) {
        const content = document.getElementById('content');
        if (content) {
            content.innerHTML = '<p class="text-red-400">Missing season or character parameter</p>';
        } else {
            console.error('Content element not found!');
        }
        return;
    }
    
    // Check if running from file:// protocol
    if (window.location.protocol === 'file:') {
        const content = document.getElementById('content');
        if (content) {
            content.innerHTML = `
                <div class="bg-yellow-900/20 border border-yellow-700 rounded-lg p-6">
                    <h2 class="text-2xl font-bold text-yellow-400 mb-4">⚠️ Please use HTTP server</h2>
                    <p class="text-gray-300 mb-2">This page requires a web server to load data files.</p>
                    <p class="text-gray-300 mb-4">Please access via: <code class="bg-gray-700 px-2 py-1 rounded">http://localhost:8000</code></p>
                    <p class="text-sm text-gray-400">Run: <code class="bg-gray-700 px-1 rounded">make site-up</code></p>
                </div>
            `;
        }
        return;
    }
    
    try {
        // Load character JSON - try multiple path patterns
        let response;
        let characterData;
        
        // Try relative path first (from sites/ directory)
        // Character data is symlinked as character-data/
        // Support both old structure (season1/adam/) and new structure (season1/characters/adam/)
        const paths = [
            `character-data/${seasonId}/characters/${characterId}/character.json`,
            `character-data/${seasonId}/${characterId}/character.json`,
            `data/${seasonId}/characters/${characterId}/character.json`,
            `data/${seasonId}/${characterId}/character.json`,
            `../data/${seasonId}/characters/${characterId}/character.json`,
            `../data/${seasonId}/${characterId}/character.json`,
        ];
        
        let loaded = false;
        let successfulPath = null;
        for (const path of paths) {
            try {
                console.log('Trying path:', path);
                response = await fetch(path);
                console.log('Response status:', response.status, response.statusText);
                if (response.ok) {
                    characterData = await response.json();
                    successfulPath = path;
                    loaded = true;
                    console.log('Successfully loaded character data:', characterData.name);
                    break;
                } else {
                    console.warn('Path failed:', path, response.status);
                }
            } catch (e) {
                console.warn('Error fetching path:', path, e);
                continue;
            }
        }
        
        if (!loaded) {
            const errorMsg = `Could not load character.json from any path. Tried: ${paths.join(', ')}`;
            console.error(errorMsg);
            const content = document.getElementById('content');
            if (content) {
                content.innerHTML = `
                    <div class="bg-red-900/20 border border-red-700 rounded-lg p-6">
                        <h2 class="text-2xl font-bold text-red-400 mb-4">Error Loading Character</h2>
                        <p class="text-gray-300 mb-2">${errorMsg}</p>
                        <p class="text-sm text-gray-400">Season: ${seasonId}, Character: ${characterId}</p>
                    </div>
                `;
            }
            return;
        }
        
        // Render breadcrumbs
        const breadcrumbs = [
            { label: 'Seasons', url: 'index.html' },
            { label: formatSeasonName(seasonId), url: `index.html?season=${seasonId}` },
            { label: 'Character', url: null },
            { label: characterData.name || characterId, url: null }
        ];
        const breadcrumbsEl = document.getElementById('breadcrumbs');
        if (breadcrumbsEl) {
            breadcrumbsEl.innerHTML = renderBreadcrumbs(breadcrumbs);
        }
        
        // Render character page - use the successful path, removing '/character.json'
        const basePath = successfulPath.replace('/character.json', '');
        renderCharacterPage(seasonId, characterId, characterData, basePath);
        
    } catch (error) {
        console.error('Error loading character:', error);
        const content = document.getElementById('content');
        if (content) {
            content.innerHTML = `
                <div class="bg-red-900/20 border border-red-700 rounded-lg p-6">
                    <h2 class="text-2xl font-bold text-red-400 mb-4">Error Loading Character</h2>
                    <p class="text-gray-300 mb-2">Could not load character data: ${error.message}</p>
                    <p class="text-sm text-gray-400">Season: ${seasonId || 'unknown'}, Character: ${characterId || 'unknown'}</p>
                    <p class="text-sm text-gray-400 mt-2">Check browser console for more details.</p>
                </div>
            `;
        }
    }
}

// Render character page
function renderCharacterPage(seasonId, characterId, characterData, basePath) {
    console.log('[renderCharacterPage] Called with:', { seasonId, characterId, basePath, hasData: !!characterData });
    const content = document.getElementById('content');
    if (!content) {
        console.error('[renderCharacterPage] Content element not found!');
        alert('Error: Content element not found on page');
        return;
    }
    console.log('[renderCharacterPage] Content element found');
    
    // Determine base path for images/audio
    // basePath comes from the character.json path, so we can derive the image path from it
    // Support both old structure (season1/adam/) and new structure (season1/characters/adam/)
    let dataBasePath = basePath;
    if (!dataBasePath || !dataBasePath.includes('character-data')) {
        // Try new structure first, then fall back to old structure
        dataBasePath = `character-data/${seasonId}/characters/${characterId}`;
    }
    
    // If basePath doesn't end with characterId, try to fix it
    if (!dataBasePath.endsWith(characterId)) {
        // Try both structures
        const newPath = `character-data/${seasonId}/characters/${characterId}`;
        const oldPath = `character-data/${seasonId}/${characterId}`;
        // We'll try both in the image paths
    }
    
    // Try to find audio file - check common patterns
    const audioPatterns = [
        `${dataBasePath}/${characterId}_audio_p225.wav`,
        `${dataBasePath}/*_audio*.wav`,
        `${dataBasePath}/*audio*.wav`,
    ];
    
    // We'll try the first pattern and check if it exists
    const audioPath = audioPatterns[0];
    
    let html = `
        <div class="mb-8">
            <h1 class="text-4xl font-bold text-primary mb-2 flex items-center gap-3">
                ${characterData.name || characterId}
                <audio id="character-audio" preload="none" style="display: none;">
                    <source src="${audioPath}" type="audio/wav">
                </audio>
                <button 
                    id="audio-play-btn"
                    onclick="toggleAudio()"
                    class="text-primary hover:text-primary-hover text-2xl cursor-pointer"
                    title="Play character story"
                    style="display: none;"
                >
                    🔊
                </button>
            </h1>
            ${characterData.motto ? `<p class="text-xl text-gray-300 italic mb-4">"${characterData.motto}"</p>` : ''}
            ${characterData.location ? `<p class="text-gray-400 mb-6">📍 ${characterData.location}</p>` : ''}
        </div>
    `;
    
    // Character cards
    html += '<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">';
    
    // Front card - try webp first, then jpg, then png
    const frontCardPaths = [
        `${dataBasePath}/front.webp`,
        `${dataBasePath}/front.jpg`,
        `${dataBasePath}/front.png`,
    ];
    html += `
        <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <h3 class="text-lg font-semibold text-primary mb-4">Front Card</h3>
            <img 
                id="front-card-img"
                src="${frontCardPaths[0]}" 
                alt="Front card"
                class="w-full rounded border border-gray-700 shadow-lg"
                onerror="handleImageError(this, ['${frontCardPaths[1]}', '${frontCardPaths[2]}'])"
            />
        </div>
    `;
    
    // Back card - support both structures
    const backCardPaths = [
        `${dataBasePath}/back.webp`,
        `character-data/${seasonId}/characters/${characterId}/back.webp`,
        `character-data/${seasonId}/${characterId}/back.webp`,
        `${dataBasePath}/back.jpg`,
        `character-data/${seasonId}/characters/${characterId}/back.jpg`,
        `character-data/${seasonId}/${characterId}/back.jpg`,
        `${dataBasePath}/back.png`,
        `character-data/${seasonId}/characters/${characterId}/back.png`,
        `character-data/${seasonId}/${characterId}/back.png`,
    ];
    html += `
        <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <h3 class="text-lg font-semibold text-primary mb-4">Back Card</h3>
            <img 
                id="back-card-img"
                src="${backCardPaths[0]}" 
                alt="Back card"
                class="w-full rounded border border-gray-700 shadow-lg"
                onerror="handleImageError(this, ['${backCardPaths[1]}', '${backCardPaths[2]}'])"
            />
        </div>
    `;
    
    html += '</div>';
    
    // Story section
    if (characterData.story) {
        html += `
            <div class="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-8">
                <h2 class="text-2xl font-bold text-primary mb-4">Story</h2>
                <p class="text-gray-300 leading-relaxed">${characterData.story}</p>
            </div>
        `;
    }
    
    console.log('[renderCharacterPage] Setting innerHTML, length:', html.length);
    try {
        content.innerHTML = html;
        console.log('[renderCharacterPage] Successfully rendered character page');
    } catch (e) {
        console.error('[renderCharacterPage] Error:', e);
        content.innerHTML = `<div class="bg-red-900/20 border border-red-700 rounded-lg p-6">
            <h2 class="text-2xl font-bold text-red-400">Error Rendering</h2>
            <p class="text-gray-300">${e.message}</p>
        </div>`;
    }
    
    // Check if audio file exists and show/hide button (after DOM update)
    setTimeout(() => {
        checkAudioFile(audioPath, characterId);
    }, 100);
}

// Handle image error fallback
window.handleImageError = function(img, fallbackPaths) {
    if (fallbackPaths && fallbackPaths.length > 0) {
        const nextPath = fallbackPaths.shift();
        img.onerror = null; // Reset error handler
        img.src = nextPath;
        if (fallbackPaths.length > 0) {
            img.onerror = function() {
                handleImageError(img, fallbackPaths);
            };
        }
    }
};

// Check if audio file exists
async function checkAudioFile(audioPath, characterId) {
    const btn = document.getElementById('audio-play-btn');
    if (!btn) return;
    
    try {
        const response = await fetch(audioPath, { method: 'HEAD' });
        if (response.ok) {
            // Audio exists, show button
            btn.style.display = 'inline-block';
            return;
        }
    } catch (error) {
        // Try alternative patterns
    }
    
    // Try alternative audio file patterns
    const basePath = audioPath.substring(0, audioPath.lastIndexOf('/'));
    const altPatterns = [
        `${basePath}/${characterId}_audio.wav`,
        `${basePath}/*_audio*.wav`,
    ];
    
    // Try to find any audio file by checking common patterns
    const audioFiles = [
        `${basePath}/${characterId}_audio_p225.wav`,
        `${basePath}/${characterId}_audio.wav`,
    ];
    
    for (const altPath of audioFiles) {
        try {
            const response = await fetch(altPath, { method: 'HEAD' });
            if (response.ok) {
                // Update audio source
                const audio = document.getElementById('character-audio');
                if (audio) {
                    audio.innerHTML = `<source src="${altPath}" type="audio/wav">`;
                }
                btn.style.display = 'inline-block';
                return;
            }
        } catch (e) {
            continue;
        }
    }
    
    // No audio found, hide button
    btn.style.display = 'none';
}

// Toggle audio playback
window.toggleAudio = function() {
    const audio = document.getElementById('character-audio');
    const btn = document.getElementById('audio-play-btn');
    
    if (!audio) return;
    
    if (audio.paused) {
        audio.play();
        btn.textContent = '⏸️';
        btn.title = 'Pause audio';
    } else {
        audio.pause();
        btn.textContent = '🔊';
        btn.title = 'Play character story';
    }
    
    audio.onended = () => {
        btn.textContent = '🔊';
        btn.title = 'Play character story';
    };
};

// Load seasons from data (use shared seasonsData from app.js)
// Don't redeclare - use window.seasonsData directly
if (!window.seasonsData) {
    window.seasonsData = {};
}

async function loadSeasons() {
    // Only load seasons for sidebar, don't interfere with content
    console.log('[character.js] loadSeasons called');
    try {
        // Check if running from file:// protocol
        if (window.location.protocol === 'file:') {
            const submenu = document.getElementById('seasons-submenu');
            if (submenu) {
                submenu.innerHTML = `
                    <div class="p-2 text-yellow-400 text-sm">
                        <p class="font-semibold mb-1">⚠️ Please use HTTP server</p>
                        <p class="text-xs">Open via: <code class="bg-gray-700 px-1 rounded">http://localhost:8000</code></p>
                    </div>
                `;
            }
            return;
        }
        
        let response = await fetch('data/seasons.json');
        if (!response.ok) {
            response = await fetch('/data/seasons.json');
        }
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        window.seasonsData = await response.json();
        renderSeasons();
    } catch (error) {
        console.error('Error loading seasons:', error);
        const submenu = document.getElementById('seasons-submenu');
        if (submenu) {
            submenu.innerHTML = `
                <div class="p-2 text-red-400 text-sm">
                    <p class="font-semibold mb-1">Error loading seasons</p>
                    <p class="text-xs">${error.message}</p>
                </div>
            `;
        }
    }
}

// Render seasons in sidebar
function renderSeasons() {
    const submenu = document.getElementById('seasons-submenu');
    if (!submenu) return;
    
    submenu.innerHTML = '';
    
    if (!window.seasonsData.seasons || window.seasonsData.seasons.length === 0) {
        submenu.innerHTML = '<p class="text-gray-500 text-sm p-2">No seasons found</p>';
        return;
    }
    
    window.seasonsData.seasons.forEach(season => {
        const item = document.createElement('a');
        item.href = `index.html?season=${season.id}`;
        item.className = 'sidebar-item block p-2 rounded text-gray-300 hover:text-white';
        item.textContent = season.name;
        submenu.appendChild(item);
    });
}

// Toggle submenu (shared with app.js)
window.toggleSubmenu = function(submenuId, toggleId) {
    const submenu = document.getElementById(submenuId);
    const arrow = document.getElementById(submenuId.replace('-submenu', '-arrow'));
    
    if (submenu.classList.contains('open')) {
        submenu.classList.remove('open');
        arrow.textContent = '▶';
    } else {
        submenu.classList.add('open');
        arrow.textContent = '▼';
    }
};

// Change theme (global function for inline onclick)
window.changeTheme = function(themeName) {
    console.log(`Changing theme to: ${themeName}`);
    
    const body = document.body;
    const currentClasses = body.className.split(' ');
    const filteredClasses = currentClasses.filter(cls => !cls.startsWith('theme-'));
    body.className = filteredClasses.join(' ').trim();
    
    if (window.themes && window.themes[themeName]) {
        body.classList.add(window.themes[themeName]);
        localStorage.setItem('cthulhu-theme', themeName);
        
        const selector = document.getElementById('theme-selector');
        if (selector) {
            selector.value = themeName;
        }
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('[character.js] DOMContentLoaded - Initializing character page');
    initializeTheme();
    
    // Load seasons for sidebar (async, don't wait)
    loadSeasons().catch(err => console.error('[character.js] Error loading seasons:', err));
    
    // Load character data
    console.log('[character.js] Calling loadCharacter...');
    loadCharacter().catch(err => {
        console.error('[character.js] Error in loadCharacter:', err);
        const content = document.getElementById('content');
        if (content) {
            content.innerHTML = `<div class="bg-red-900/20 border border-red-700 rounded-lg p-6">
                <h2 class="text-2xl font-bold text-red-400 mb-4">Error</h2>
                <p class="text-gray-300">${err.message}</p>
            </div>`;
        }
    });
});

