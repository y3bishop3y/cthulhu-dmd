// Main application JavaScript
window.seasonsData = window.seasonsData || {};
let seasonsData = window.seasonsData; // Local reference
let currentSeason = null;

// Theme management (make it globally available)
window.themes = {
    green: 'theme-green',
    yellow: 'theme-yellow',
    purple: 'theme-purple',
    red: 'theme-red',
    blue: 'theme-blue',
    cyan: 'theme-cyan'
};
const themes = window.themes; // Local reference for this file

// Initialize the application (only on index.html)
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    // Only load seasons on index.html, not character.html
    if (!window.location.pathname.includes('character.html')) {
        loadSeasons();
    }
});

// Initialize theme from localStorage or default to green
function initializeTheme() {
    const savedTheme = localStorage.getItem('cthulhu-theme') || 'green';
    
    // Remove all theme classes from body
    const body = document.body;
    body.className = body.className.replace(/theme-\w+/g, '');
    
    // Add saved theme class
    if (themes[savedTheme]) {
        body.classList.add(themes[savedTheme]);
    } else {
        body.classList.add('theme-green'); // Default fallback
    }
    
    // Set dropdown value
    const selector = document.getElementById('theme-selector');
    if (selector) {
        selector.value = savedTheme;
    }
}

// Change theme (global function for inline onclick)
window.changeTheme = function(themeName) {
    console.log(`Changing theme to: ${themeName}`);
    
    // Remove all theme classes from body
    const body = document.body;
    const currentClasses = body.className.split(' ');
    const filteredClasses = currentClasses.filter(cls => !cls.startsWith('theme-'));
    body.className = filteredClasses.join(' ').trim();
    
    // Add new theme class
    if (themes[themeName]) {
        body.classList.add(themes[themeName]);
        localStorage.setItem('cthulhu-theme', themeName);
        
        // Update dropdown value
        const selector = document.getElementById('theme-selector');
        if (selector) {
            selector.value = themeName;
        }
        
        console.log(`Theme changed to: ${themeName}, body classes:`, body.className);
    } else {
        console.error(`Unknown theme: ${themeName}`);
    }
};

// Load seasons from data
async function loadSeasons() {
    try {
        // Check if running from file:// protocol
        if (window.location.protocol === 'file:') {
            const submenu = document.getElementById('seasons-submenu');
            if (submenu) {
                submenu.innerHTML = `
                    <div class="p-2 text-yellow-400 text-sm">
                        <p class="font-semibold mb-1">⚠️ Please use HTTP server</p>
                        <p class="text-xs">Open via: <code class="bg-gray-700 px-1 rounded">http://localhost:8000</code></p>
                        <p class="text-xs mt-1">Run: <code class="bg-gray-700 px-1 rounded">make site-up</code></p>
                    </div>
                `;
            }
            return;
        }
        
        // Try relative path first (for local development)
        let response = await fetch('data/seasons.json');
        if (!response.ok) {
            // Try absolute path
            response = await fetch('/data/seasons.json');
        }
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        window.seasonsData = await response.json();
        seasonsData = window.seasonsData; // Update local reference
        renderSeasons();
    } catch (error) {
        console.error('Error loading seasons:', error);
        // Show error message
        const submenu = document.getElementById('seasons-submenu');
        if (submenu) {
            submenu.innerHTML = `
                <div class="p-2 text-red-400 text-sm">
                    <p class="font-semibold mb-1">Error loading seasons</p>
                    <p class="text-xs">${error.message}</p>
                    <p class="text-xs mt-1">Make sure you're accessing via: <code class="bg-gray-700 px-1 rounded">http://localhost:8000</code></p>
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
        item.href = '#';
        item.className = 'sidebar-item block p-2 rounded text-gray-300 hover:text-white';
        item.textContent = season.name;
        item.onclick = (e) => {
            e.preventDefault();
            loadSeason(season.id);
        };
        submenu.appendChild(item);
    });
}

// Toggle submenu
function toggleSubmenu(submenuId, toggleId) {
    const submenu = document.getElementById(submenuId);
    const arrow = document.getElementById(submenuId.replace('-submenu', '-arrow'));
    
    if (submenu.classList.contains('open')) {
        submenu.classList.remove('open');
        arrow.textContent = '▶';
    } else {
        submenu.classList.add('open');
        arrow.textContent = '▼';
    }
}

// Load season data
async function loadSeason(seasonId) {
    // Don't run on character.html pages
    if (window.location.pathname.includes('character.html')) {
        return;
    }
    
    currentSeason = seasonId;
    
    // Update URL without reload (only if we're on index.html)
    if (window.location.pathname.endsWith('index.html') || window.location.pathname === '/' || window.location.pathname.endsWith('/')) {
        window.history.pushState({season: seasonId}, '', `?season=${seasonId}`);
    }
    
    try {
        const response = await fetch(`data/seasons/${seasonId}.json`);
        const seasonData = await response.json();
        renderSeasonPage(seasonData);
    } catch (error) {
        console.error(`Error loading season ${seasonId}:`, error);
        const content = document.getElementById('content');
        if (content) {
            content.innerHTML = `
                <h2 class="text-3xl font-bold mb-6 text-primary">Error</h2>
                <p class="text-red-400">Could not load season data.</p>
            `;
        }
    }
}

// Handle browser back/forward (only on index.html)
window.addEventListener('popstate', (event) => {
    // Only handle popstate on index.html, not character.html
    if (window.location.pathname.includes('character.html')) {
        return;
    }
    
    const params = new URLSearchParams(window.location.search);
    const seasonId = params.get('season');
    if (seasonId) {
        loadSeason(seasonId);
    } else {
        // Show welcome page (only on index.html)
        if (window.location.pathname.includes('character.html')) {
            return;
        }
        const content = document.getElementById('content');
        if (content) {
            content.innerHTML = `
                <h2 class="text-3xl font-bold mb-6 text-primary">Welcome</h2>
                <p class="text-gray-300">Select a season from the sidebar to view characters.</p>
            `;
        }
    }
});

// Check for season parameter on page load (only on index.html)
document.addEventListener('DOMContentLoaded', () => {
    // Only run on index.html, not character.html
    if (window.location.pathname.includes('character.html')) {
        return;
    }
    
    const params = new URLSearchParams(window.location.search);
    const seasonId = params.get('season');
    if (seasonId) {
        // Small delay to ensure seasons are loaded
        setTimeout(() => loadSeason(seasonId), 100);
    }
});

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

// Render season page with characters in a table
function renderSeasonPage(seasonData) {
    // Don't render on character.html pages
    if (window.location.pathname.includes('character.html')) {
        console.warn('[app.js] renderSeasonPage called on character.html, ignoring');
        return;
    }
    
    const content = document.getElementById('content');
    if (!content) {
        console.warn('[app.js] Content element not found');
        return;
    }
    
    // Breadcrumbs
    const breadcrumbs = [
        { label: 'Seasons', url: '#' },
        { label: seasonData.name, url: null }
    ];
    
    let html = renderBreadcrumbs(breadcrumbs);
    
    // Season header with purchase link
    html += `<div class="flex items-center justify-between mb-6">`;
    html += `<h2 class="text-3xl font-bold text-primary">${seasonData.name}</h2>`;
    if (seasonData.amazon_link) {
        html += `<a href="${seasonData.amazon_link}" target="_blank" rel="noopener noreferrer" 
                    class="text-sm text-gray-400 hover:text-primary transition-colors">
                    Purchase →
                </a>`;
    }
    html += `</div>`;
    
    if (seasonData.characters && seasonData.characters.length > 0) {
        html += `
            <div class="overflow-x-auto">
                <table id="character-table" class="w-full border-collapse">
                    <thead>
                        <tr class="border-b border-gray-700">
                            <th class="text-left p-4 text-primary font-semibold cursor-pointer hover:text-primary-hover select-none" 
                                onclick="sortTable('name')">
                                Character <span class="sort-indicator" id="sort-name">↕</span>
                            </th>
                            <th class="text-left p-4 text-primary font-semibold">Motto</th>
                            <th class="text-left p-4 text-primary font-semibold">Common Powers</th>
                            <th class="text-left p-4 text-primary font-semibold cursor-pointer hover:text-primary-hover select-none" 
                                onclick="sortTable('location')">
                                Location <span class="sort-indicator" id="sort-location">↕</span>
                            </th>
                            <th class="text-left p-4 text-primary font-semibold">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="character-table-body">
        `;
        
        seasonData.characters.forEach((character, index) => {
            const rowClass = index % 2 === 0 ? 'bg-gray-800' : 'bg-gray-800/50';
            const commonPowers = character.common_powers && character.common_powers.length > 0 
                ? character.common_powers.join(', ') 
                : '—';
            const characterUrl = `character.html?season=${encodeURIComponent(seasonData.id)}&character=${encodeURIComponent(character.id)}`;
            html += `
                <tr class="${rowClass} border-b border-gray-700 hover:bg-gray-700 transition-colors" 
                    data-name="${(character.name || 'Unknown').toLowerCase()}" 
                    data-location="${(character.location || '').toLowerCase()}">
                    <td class="p-4">
                        <a href="${characterUrl}" 
                           class="text-primary hover:text-primary-hover font-semibold block">
                            ${character.name || 'Unknown'}
                        </a>
                    </td>
                    <td class="p-4 text-gray-300 italic">${character.motto || '—'}</td>
                    <td class="p-4 text-gray-300">${commonPowers}</td>
                    <td class="p-4 text-gray-400">${character.location || '—'}</td>
                    <td class="p-4">
                        <a href="${characterUrl}" 
                           class="text-primary hover:text-primary-hover text-sm inline-block">
                            View Details →
                        </a>
                    </td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        // Add world map with location pins
        html += `
            <div class="mt-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h3 class="text-2xl font-bold text-primary mb-4">Character Locations</h3>
                <div id="character-map" style="height: 250px; width: 100%;" class="rounded border border-gray-700"></div>
            </div>
        `;
    } else {
        html += '<p class="text-gray-400">No characters found.</p>';
    }
    
    content.innerHTML = html;
    
    // Store season data for sorting reset
    window.currentSeasonData = seasonData;
    
    // Initialize map if characters exist
    if (seasonData.characters && seasonData.characters.length > 0) {
        setTimeout(() => {
            initializeCharacterMap(seasonData.characters);
        }, 100);
    }
}

// Table sorting functionality
let sortDirection = { name: null, location: null };

window.sortTable = function(column) {
    const tbody = document.getElementById('character-table-body');
    if (!tbody) return;
    
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Toggle sort direction
    if (sortDirection[column] === 'asc') {
        sortDirection[column] = 'desc';
    } else if (sortDirection[column] === 'desc') {
        sortDirection[column] = null; // Reset to original order
    } else {
        sortDirection[column] = 'asc';
    }
    
    // Reset other column indicators
    Object.keys(sortDirection).forEach(key => {
        if (key !== column) {
            sortDirection[key] = null;
        }
    });
    
    // Update sort indicators
    document.querySelectorAll('.sort-indicator').forEach(ind => {
        ind.textContent = '↕';
    });
    
    const nameIndicator = document.getElementById('sort-name');
    const locationIndicator = document.getElementById('sort-location');
    
    if (sortDirection[column] === null) {
        // Reset to original order
        if (column === 'name') nameIndicator.textContent = '↕';
        if (column === 'location') locationIndicator.textContent = '↕';
        
        // Re-render table in original order
        const content = document.getElementById('content');
        const seasonData = window.currentSeasonData;
        if (seasonData) {
            renderSeasonPage(seasonData);
        }
        return;
    }
    
    // Show sort direction
    if (column === 'name') {
        nameIndicator.textContent = sortDirection[column] === 'asc' ? '↑' : '↓';
    }
    if (column === 'location') {
        locationIndicator.textContent = sortDirection[column] === 'asc' ? '↑' : '↓';
    }
    
    // Sort rows
    rows.sort((a, b) => {
        let aVal, bVal;
        
        if (column === 'name') {
            aVal = a.dataset.name || '';
            bVal = b.dataset.name || '';
        } else if (column === 'location') {
            aVal = a.dataset.location || '';
            bVal = b.dataset.location || '';
        } else {
            return 0;
        }
        
        const comparison = aVal.localeCompare(bVal);
        return sortDirection[column] === 'asc' ? comparison : -comparison;
    });
    
    // Re-append sorted rows
    rows.forEach((row, index) => {
        row.className = index % 2 === 0 ? 'bg-gray-800 border-b border-gray-700 hover:bg-gray-700 transition-colors' : 'bg-gray-800/50 border-b border-gray-700 hover:bg-gray-700 transition-colors';
        tbody.appendChild(row);
    });
};

// Initialize character location map
function initializeCharacterMap(characters) {
    const mapDiv = document.getElementById('character-map');
    if (!mapDiv || typeof L === 'undefined') {
        console.warn('Leaflet not loaded or map div not found');
        return;
    }
    
    // Initialize map centered on world
    const map = L.map('character-map').setView([20, 0], 2);
    
    // Add lighter tile layer (positron style)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(map);
    
    // Geocode locations and add markers
    const locations = {};
    characters.forEach(char => {
        if (char.location) {
            const loc = char.location.toUpperCase();
            if (!locations[loc]) {
                locations[loc] = [];
            }
            locations[loc].push(char);
        }
    });
    
    // Simple location to coordinates mapping (you can expand this)
    const locationCoords = {
        'MANCHESTER, ENGLAND': [53.4808, -2.2426],
        'MERSIN, TURKEY': [36.8121, 34.6415],
        'FALL RIVER, MASSACHUSETTS': [41.7015, -71.1550],
        'LONDON, ENGLAND': [51.5074, -0.1278],
        'ALEXANDRIA, EGYPT': [31.2001, 29.9187],
        'BOGOTA, COLOMBIA': [4.7110, -74.0721],
        'FORT WAYNE, INDIANA': [41.0793, -85.1394],
        'JONESBORO, MAINE': [44.6628, -69.6298],
        'MOSCOW, RUSSIA': [55.7558, 37.6173],
        'ARKHAM, MASSACHUSETTS': [42.6526, -70.8450],
        'NEW YORK, NEW YORK': [40.7128, -74.0060],
        'BOSTON, MASSACHUSETTS': [42.3601, -71.0589],
        'PARIS, FRANCE': [48.8566, 2.3522],
        'CAIRO, EGYPT': [30.0444, 31.2357],
        'TOKYO, JAPAN': [35.6762, 139.6503],
        'UNKNOWN': null, // Skip unknown locations
    };
    
    // Add markers for all locations
    const markers = [];
    Object.keys(locations).forEach(loc => {
        const coords = locationCoords[loc];
        if (coords) {
            const chars = locations[loc];
            const popupContent = chars.map(char => 
                `<strong class="text-primary">${char.name}</strong><br>${char.motto || ''}`
            ).join('<hr>');
            
            const marker = L.marker(coords)
                .addTo(map)
                .bindPopup(popupContent);
            markers.push(marker);
        } else if (loc !== 'UNKNOWN') {
            // Log missing locations for debugging
            console.warn(`Location not mapped: ${loc}`);
        }
    });
    
    // Fit map bounds to show all markers if we have any
    if (markers.length > 0) {
        const group = new L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

