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
        // Add cache-busting parameter to force fresh data
        const cacheBuster = `?t=${Date.now()}`;
        const paths = [
            `character-data/${seasonId}/characters/${characterId}/character.json${cacheBuster}`,
            `character-data/${seasonId}/${characterId}/character.json${cacheBuster}`,
            `data/${seasonId}/characters/${characterId}/character.json${cacheBuster}`,
            `data/${seasonId}/${characterId}/character.json${cacheBuster}`,
            `../data/${seasonId}/characters/${characterId}/character.json${cacheBuster}`,
            `../data/${seasonId}/${characterId}/character.json${cacheBuster}`,
        ];
        
        let loaded = false;
        let successfulPath = null;
        for (const path of paths) {
            try {
                console.log('Trying path:', path);
                response = await fetch(path, { cache: 'no-store' });
                console.log('Response status:', response.status, response.statusText);
                if (response.ok) {
                    characterData = await response.json();
                    successfulPath = path.replace(cacheBuster, ''); // Remove cache buster for base path
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
    // Convert characterId to different formats (hyphen to underscore, lowercase)
    const characterIdUnderscore = characterId.replace(/-/g, '_');
    const characterIdLower = characterId.toLowerCase();
    const characterIdUnderscoreLower = characterIdUnderscore.toLowerCase();
    
    // Also try using character name from JSON (converted to file format)
    const characterNameForFile = characterData.name 
        ? characterData.name.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')
        : null;
    
    const audioPatterns = [
        `${dataBasePath}/${characterIdUnderscoreLower}_audio_p225.wav`,
        `${dataBasePath}/${characterIdUnderscore}_audio_p225.wav`,
        `${dataBasePath}/${characterIdLower}_audio_p225.wav`,
        `${dataBasePath}/${characterId}_audio_p225.wav`,
    ];
    
    // Add character name-based patterns if available
    if (characterNameForFile) {
        audioPatterns.push(`${dataBasePath}/${characterNameForFile}_audio_p225.wav`);
    }
    
    // We'll try the first pattern and check if it exists
    const audioPath = audioPatterns[0];
    
    // Build audio source with multiple fallbacks
    const audioSources = audioPatterns.map(path => 
        `<source src="${path}" type="audio/wav">`
    ).join('');
    
    // Build audio paths for both male and female
    const femaleAudioPaths = [
        `${dataBasePath}/${characterIdUnderscoreLower}_audio_female.wav`,
        `${dataBasePath}/${characterIdUnderscore}_audio_female.wav`,
        `${dataBasePath}/${characterIdLower}_audio_female.wav`,
        `${dataBasePath}/${characterId}_audio_female.wav`,
        `${dataBasePath}/${characterIdUnderscoreLower}_audio_p225.wav`, // Old format
        `${dataBasePath}/${characterIdUnderscore}_audio_p225.wav`,
    ];
    
    const maleAudioPaths = [
        `${dataBasePath}/${characterIdUnderscoreLower}_audio_male.wav`,
        `${dataBasePath}/${characterIdUnderscore}_audio_male.wav`,
        `${dataBasePath}/${characterIdLower}_audio_male.wav`,
        `${dataBasePath}/${characterId}_audio_male.wav`,
        `${dataBasePath}/${characterIdUnderscoreLower}_audio_p226.wav`, // Old format
        `${dataBasePath}/${characterIdUnderscore}_audio_p226.wav`,
    ];
    
    if (characterNameForFile) {
        femaleAudioPaths.push(`${dataBasePath}/${characterNameForFile}_audio_female.wav`);
        femaleAudioPaths.push(`${dataBasePath}/${characterNameForFile}_audio_p225.wav`);
        maleAudioPaths.push(`${dataBasePath}/${characterNameForFile}_audio_male.wav`);
        maleAudioPaths.push(`${dataBasePath}/${characterNameForFile}_audio_p226.wav`);
    }
    
    let html = `
        <div class="mb-8">
            <h1 class="text-4xl font-bold text-primary mb-2 flex items-center gap-3 flex-wrap">
                ${characterData.name || characterId}
                <span class="flex items-center gap-2 text-lg">
                    <audio id="character-audio-male" preload="none" style="display: none;"></audio>
                    <button 
                        id="audio-play-btn-male"
                        onclick="toggleAudio('male')"
                        class="text-primary hover:text-primary-hover text-xl cursor-pointer flex items-center gap-1"
                        title="Play character story (Randolph - Male voice)"
                        style="display: none;"
                    >
                        <span class="text-sm">Randolph</span> 🔊
                    </button>
                    <audio id="character-audio-female" preload="none" style="display: none;"></audio>
                    <button 
                        id="audio-play-btn-female"
                        onclick="toggleAudio('female')"
                        class="text-primary hover:text-primary-hover text-xl cursor-pointer flex items-center gap-1"
                        title="Play character story (Lavinia - Female voice)"
                        style="display: none;"
                    >
                        <span class="text-sm">Lavinia</span> 🔊
                    </button>
                </span>
            </h1>
            ${characterData.motto ? `<p class="text-xl text-gray-300 italic mb-4">"${characterData.motto}"</p>` : ''}
            ${characterData.location ? `<p class="text-gray-400 mb-6">📍 ${typeof characterData.location === 'string' ? characterData.location : (characterData.location.original || 'Unknown')}</p>` : ''}
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
                class="w-full rounded border border-gray-700 shadow-lg cursor-pointer hover:opacity-90 transition-opacity"
                onclick="openCardModal('${frontCardPaths[0]}', 'Front Card', ['${frontCardPaths[1]}', '${frontCardPaths[2]}'])"
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
                class="w-full rounded border border-gray-700 shadow-lg cursor-pointer hover:opacity-90 transition-opacity"
                onclick="openCardModal('${backCardPaths[0]}', 'Back Card', ['${backCardPaths[1]}', '${backCardPaths[2]}', '${backCardPaths[3]}', '${backCardPaths[4]}', '${backCardPaths[5]}', '${backCardPaths[6]}', '${backCardPaths[7]}', '${backCardPaths[8]}'])"
                onerror="handleImageError(this, ['${backCardPaths[1]}', '${backCardPaths[2]}', '${backCardPaths[3]}', '${backCardPaths[4]}', '${backCardPaths[5]}', '${backCardPaths[6]}', '${backCardPaths[7]}', '${backCardPaths[8]}'])"
            />
        </div>
    `;
    
    html += '</div>';
    
    // Add modal HTML for card popup
    html += `
        <div id="card-modal" class="fixed inset-0 bg-black bg-opacity-75 z-50 hidden flex items-center justify-center p-4" onclick="closeCardModal(event)">
            <div class="bg-gray-800 rounded-lg max-w-6xl max-h-[95vh] overflow-auto relative" onclick="event.stopPropagation()">
                <button 
                    onclick="closeCardModal()" 
                    class="absolute top-4 right-4 text-gray-400 hover:text-white text-3xl font-bold z-10 bg-gray-800 rounded-full w-10 h-10 flex items-center justify-center"
                    title="Close (ESC)"
                >
                    ×
                </button>
                <div class="p-6">
                    <h3 id="modal-title" class="text-2xl font-bold text-primary mb-4"></h3>
                    <img 
                        id="modal-card-img" 
                        src="" 
                        alt="Card" 
                        class="w-full rounded border border-gray-700 shadow-lg"
                    />
                </div>
            </div>
        </div>
    `;
    
    // External links section
    const links = characterData.links || {};
    if (links.wikipedia || links.grokpedia || (links.other && links.other.length > 0)) {
        html += `
            <div class="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-8">
                <h2 class="text-2xl font-bold text-primary mb-4">External Links</h2>
                <div class="flex flex-wrap gap-3">
        `;
        
        if (links.wikipedia) {
            html += `
                <a href="${links.wikipedia}" target="_blank" rel="noopener noreferrer" 
                   class="text-primary hover:text-primary-hover border border-primary px-4 py-2 rounded transition-colors">
                    📖 Wikipedia
                </a>
            `;
        }
        
        if (links.grokpedia) {
            html += `
                <a href="${links.grokpedia}" target="_blank" rel="noopener noreferrer" 
                   class="text-primary hover:text-primary-hover border border-primary px-4 py-2 rounded transition-colors">
                    🔍 Grokpedia
                </a>
            `;
        }
        
        if (links.other && links.other.length > 0) {
            links.other.forEach(link => {
                const url = typeof link === 'string' ? link : link.url;
                const label = typeof link === 'string' ? 'Other' : (link.label || 'Other');
                html += `
                    <a href="${url}" target="_blank" rel="noopener noreferrer" 
                       class="text-primary hover:text-primary-hover border border-primary px-4 py-2 rounded transition-colors">
                        🔗 ${label}
                    </a>
                `;
            });
        }
        
        html += `
                </div>
            </div>
        `;
    }
    
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
    
    // Check if audio files exist and show/hide buttons (after DOM update)
    setTimeout(() => {
        // Check female audio
        const tryFemaleAudio = async (index) => {
            if (index >= femaleAudioPaths.length) {
                return; // No female audio found
            }
            
            const path = femaleAudioPaths[index];
            const response = await fetch(path, { method: 'HEAD' }).catch(() => null);
            
            if (response && response.ok) {
                const audio = document.getElementById('character-audio-female');
                const btn = document.getElementById('audio-play-btn-female');
                if (audio) {
                    audio.innerHTML = `<source src="${path}" type="audio/wav">`;
                }
                if (btn) {
                    btn.style.display = 'inline-block';
                }
            } else {
                tryFemaleAudio(index + 1);
            }
        };
        
        // Check male audio
        const tryMaleAudio = async (index) => {
            if (index >= maleAudioPaths.length) {
                return; // No male audio found
            }
            
            const path = maleAudioPaths[index];
            const response = await fetch(path, { method: 'HEAD' }).catch(() => null);
            
            if (response && response.ok) {
                const audio = document.getElementById('character-audio-male');
                const btn = document.getElementById('audio-play-btn-male');
                if (audio) {
                    audio.innerHTML = `<source src="${path}" type="audio/wav">`;
                }
                if (btn) {
                    btn.style.display = 'inline-block';
                }
            } else {
                tryMaleAudio(index + 1);
            }
        };
        
        tryFemaleAudio(0);
        tryMaleAudio(0);
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
    // Convert characterId to different formats
    const characterIdUnderscore = characterId.replace(/-/g, '_');
    const characterIdLower = characterId.toLowerCase();
    const characterIdUnderscoreLower = characterIdUnderscore.toLowerCase();
    
    const audioFiles = [
        `${basePath}/${characterIdUnderscoreLower}_audio_p225.wav`,
        `${basePath}/${characterIdUnderscore}_audio_p225.wav`,
        `${basePath}/${characterIdLower}_audio_p225.wav`,
        `${basePath}/${characterId}_audio_p225.wav`,
        `${basePath}/${characterIdUnderscoreLower}_audio.wav`,
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

// Card modal functions
window.openCardModal = function(imageSrc, title, fallbackPaths = []) {
    const modal = document.getElementById('card-modal');
    const modalImg = document.getElementById('modal-card-img');
    const modalTitle = document.getElementById('modal-title');
    
    if (!modal || !modalImg || !modalTitle) return;
    
    modalTitle.textContent = title;
    modalImg.src = imageSrc;
    modalImg.onerror = function() {
        if (fallbackPaths && fallbackPaths.length > 0) {
            const nextPath = fallbackPaths.shift();
            modalImg.src = nextPath;
            if (fallbackPaths.length > 0) {
                modalImg.onerror = arguments.callee;
            }
        }
    };
    
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
};

window.closeCardModal = function(event) {
    // If event is provided and it's not a click on the modal content, close
    if (event && event.target.id !== 'card-modal') {
        return;
    }
    
    const modal = document.getElementById('card-modal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = ''; // Restore scrolling
    }
};

// Close modal on ESC key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeCardModal();
    }
});

// Toggle audio playback
window.toggleAudio = function(gender) {
    const audioId = gender === 'male' ? 'character-audio-male' : 'character-audio-female';
    const btnId = gender === 'male' ? 'audio-play-btn-male' : 'audio-play-btn-female';
    const speakerName = gender === 'male' ? 'Randolph' : 'Lavinia';
    
    const audio = document.getElementById(audioId);
    const btn = document.getElementById(btnId);
    
    if (!audio || !btn) return;
    
    // Stop the other audio if playing
    const otherGender = gender === 'male' ? 'female' : 'male';
    const otherAudioId = otherGender === 'male' ? 'character-audio-male' : 'character-audio-female';
    const otherBtnId = otherGender === 'male' ? 'audio-play-btn-male' : 'audio-play-btn-female';
    const otherAudio = document.getElementById(otherAudioId);
    const otherBtn = document.getElementById(otherBtnId);
    
    if (otherAudio && !otherAudio.paused) {
        otherAudio.pause();
        otherAudio.currentTime = 0;
        if (otherBtn) {
            const otherSpeakerName = otherGender === 'male' ? 'Randolph' : 'Lavinia';
            otherBtn.innerHTML = `<span class="text-sm">${otherSpeakerName}</span> 🔊`;
        }
    }
    
    if (audio.paused) {
        audio.play();
        btn.innerHTML = `<span class="text-sm">${speakerName}</span> ⏸️`;
        btn.title = `Pause audio (${speakerName} - ${gender === 'male' ? 'Male' : 'Female'} voice)`;
    } else {
        audio.pause();
        audio.currentTime = 0;
        btn.innerHTML = `<span class="text-sm">${speakerName}</span> 🔊`;
        btn.title = `Play character story (${speakerName} - ${gender === 'male' ? 'Male' : 'Female'} voice)`;
    }
    
    audio.onended = () => {
        btn.innerHTML = `<span class="text-sm">${speakerName}</span> 🔊`;
        btn.title = `Play character story (${speakerName} - ${gender === 'male' ? 'Male' : 'Female'} voice)`;
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
        
        // Add cache-busting parameter to ensure fresh data
        let response = await fetch(`data/seasons.json?t=${Date.now()}`);
        if (!response.ok) {
            response = await fetch(`/data/seasons.json?t=${Date.now()}`);
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

