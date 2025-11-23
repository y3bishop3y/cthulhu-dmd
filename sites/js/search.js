// Search functionality using inverted indexes

let searchIndexes = {
    powers: null,
    locations: null,
    seasons: null,
    characters: null
};

// Load search indexes
async function loadSearchIndexes() {
    try {
        const [powersRes, locationsRes, seasonsRes, charactersRes] = await Promise.all([
            fetch('character-data/indexes/powers.json').catch(() => fetch('data/indexes/powers.json')),
            fetch('character-data/indexes/locations.json').catch(() => fetch('data/indexes/locations.json')),
            fetch('character-data/indexes/seasons_index.json').catch(() => fetch('data/indexes/seasons_index.json')),
            fetch('character-data/indexes/characters.json').catch(() => fetch('data/indexes/characters.json'))
        ]);

        if (powersRes.ok) searchIndexes.powers = await powersRes.json();
        if (locationsRes.ok) searchIndexes.locations = await locationsRes.json();
        if (seasonsRes.ok) searchIndexes.seasons = await seasonsRes.json();
        if (charactersRes.ok) searchIndexes.characters = await charactersRes.json();

        console.log('Search indexes loaded:', {
            powers: !!searchIndexes.powers,
            locations: !!searchIndexes.locations,
            seasons: !!searchIndexes.seasons,
            characters: !!searchIndexes.characters
        });
    } catch (error) {
        console.error('Error loading search indexes:', error);
    }
}

// Format season name
function formatSeasonName(seasonId) {
    if (seasonId.startsWith('season')) {
        const num = seasonId.replace('season', '');
        return `Season ${num}`;
    }
    return seasonId.split('-').map(word =>
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

// Perform search
async function performSearch() {
    const query = document.getElementById('search-input').value.trim().toLowerCase();
    
    if (!query) {
        clearSearch();
        return;
    }

    // Ensure indexes are loaded
    if (!searchIndexes.powers || !searchIndexes.seasons) {
        await loadSearchIndexes();
    }

    const results = [];
    const matchedCharacterIds = new Set();

    // Search in powers
    if (searchIndexes.powers) {
        Object.keys(searchIndexes.powers).forEach(power => {
            if (power.toLowerCase().includes(query)) {
                searchIndexes.powers[power].forEach(charId => {
                    matchedCharacterIds.add(charId);
                });
            }
        });
    }

    // Search in character names (from characters index)
    if (searchIndexes.characters) {
        searchIndexes.characters.forEach(char => {
            const name = (char.name || '').toLowerCase();
            if (name.includes(query)) {
                matchedCharacterIds.add(char.id);
            }
        });
    }

    // Search in locations
    if (searchIndexes.locations) {
        // Search in cities
        if (searchIndexes.locations.cities) {
            Object.keys(searchIndexes.locations.cities).forEach(city => {
                if (city.toLowerCase().includes(query)) {
                    searchIndexes.locations.cities[city].forEach(charId => {
                        matchedCharacterIds.add(charId);
                    });
                }
            });
        }
        // Search in countries
        if (searchIndexes.locations.countries) {
            Object.keys(searchIndexes.locations.countries).forEach(country => {
                if (country.toLowerCase().includes(query)) {
                    searchIndexes.locations.countries[country].forEach(charId => {
                        matchedCharacterIds.add(charId);
                    });
                }
            });
        }
        // Search in regions
        if (searchIndexes.locations.regions) {
            Object.keys(searchIndexes.locations.regions).forEach(region => {
                if (region.toLowerCase().includes(query)) {
                    searchIndexes.locations.regions[region].forEach(charId => {
                        matchedCharacterIds.add(charId);
                    });
                }
            });
        }
    }

    // Group results by season
    const resultsBySeason = {};
    
    if (searchIndexes.seasons && matchedCharacterIds.size > 0) {
        Object.keys(searchIndexes.seasons).forEach(seasonId => {
            const seasonChars = searchIndexes.seasons[seasonId] || [];
            const matched = seasonChars.filter(charId => matchedCharacterIds.has(charId));
            
            if (matched.length > 0) {
                resultsBySeason[seasonId] = matched;
            }
        });
    }

    // Load full character data for matched characters
    await loadSearchResults(resultsBySeason, query);
}

// Load full character data and render results
async function loadSearchResults(resultsBySeason, query) {
    const content = document.getElementById('content');
    if (!content) return;

    if (Object.keys(resultsBySeason).length === 0) {
        content.innerHTML = `
            <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h2 class="text-2xl font-bold text-primary mb-4">No Results Found</h2>
                <p class="text-gray-300">No characters found matching "${query}"</p>
                <p class="text-sm text-gray-400 mt-2">Try searching for a power (e.g., "Marksman"), location, or character name.</p>
            </div>
        `;
        return;
    }

    let html = `
        <div class="mb-6">
            <h2 class="text-3xl font-bold text-primary mb-2">Search Results</h2>
            <p class="text-gray-400">Found ${Object.values(resultsBySeason).reduce((sum, arr) => sum + arr.length, 0)} character(s) matching "${query}"</p>
        </div>
    `;

    // Load character data for each season
    const seasonPromises = Object.keys(resultsBySeason).map(async (seasonId) => {
        try {
            // Try to load season.json first (has purchase links)
            let seasonData;
            try {
                const seasonRes = await fetch(`character-data/${seasonId}/season.json`).catch(() => 
                    fetch(`data/${seasonId}/season.json`)
                );
                if (seasonRes.ok) {
                    seasonData = await seasonRes.json();
                }
            } catch (e) {
                // Fall back to old format
                const oldRes = await fetch(`data/seasons/${seasonId}.json`);
                if (oldRes.ok) {
                    seasonData = await oldRes.json();
                }
            }

            if (!seasonData) return null;

            // Filter characters to only matched ones
            const matchedIds = resultsBySeason[seasonId];
            const matchedCharacters = (seasonData.characters || []).filter(char =>
                matchedIds.includes(char.id)
            );

            if (matchedCharacters.length === 0) return null;

            return {
                seasonId,
                seasonName: seasonData.name || formatSeasonName(seasonId),
                purchaseLinks: seasonData.purchase_links || {},
                characters: matchedCharacters
            };
        } catch (error) {
            console.error(`Error loading season ${seasonId}:`, error);
            return null;
        }
    });

    const seasonResults = (await Promise.all(seasonPromises)).filter(s => s !== null);

    // Render results grouped by season
    if (seasonResults.length === 0) {
        html += '<p class="text-gray-400">Could not load character details.</p>';
    } else {
        html += `
            <div class="overflow-x-auto">
                <table class="w-full border-collapse">
                    <thead>
                        <tr class="border-b border-gray-700">
                            <th class="text-left p-4 text-primary font-semibold">Season</th>
                            <th class="text-left p-4 text-primary font-semibold">Character</th>
                            <th class="text-left p-4 text-primary font-semibold">Motto</th>
                            <th class="text-left p-4 text-primary font-semibold">Common Powers</th>
                            <th class="text-left p-4 text-primary font-semibold">Location</th>
                            <th class="text-left p-4 text-primary font-semibold">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        seasonResults.forEach(({ seasonId, seasonName, purchaseLinks, characters }) => {
            characters.forEach((character, index) => {
                const rowClass = index % 2 === 0 ? 'bg-gray-800' : 'bg-gray-800/50';
                const commonPowers = character.common_powers && character.common_powers.length > 0
                    ? character.common_powers.join(', ')
                    : '—';
                const location = character.location || (character.location && character.location.original) || '—';
                const characterUrl = `character.html?season=${encodeURIComponent(seasonId)}&character=${encodeURIComponent(character.id)}`;

                html += `
                    <tr class="${rowClass} border-b border-gray-700 hover:bg-gray-700 transition-colors">
                        <td class="p-4">
                            <div class="flex items-center gap-2">
                                <span class="text-gray-300 font-semibold">${seasonName}</span>
                                ${purchaseLinks.amazon ? `
                                    <a href="${purchaseLinks.amazon}" target="_blank" rel="noopener noreferrer" 
                                       class="text-xs text-primary hover:text-primary-hover" title="Purchase on Amazon">
                                        🛒
                                    </a>
                                ` : ''}
                            </div>
                        </td>
                        <td class="p-4">
                            <a href="${characterUrl}" 
                               class="text-primary hover:text-primary-hover font-semibold block">
                                ${character.name || 'Unknown'}
                            </a>
                        </td>
                        <td class="p-4 text-gray-300 italic">${character.motto || '—'}</td>
                        <td class="p-4 text-gray-300">${commonPowers}</td>
                        <td class="p-4 text-gray-400">${location}</td>
                        <td class="p-4">
                            <a href="${characterUrl}" 
                               class="text-primary hover:text-primary-hover text-sm inline-block">
                                View Details →
                            </a>
                        </td>
                    </tr>
                `;
            });
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;
    }

    content.innerHTML = html;
    document.getElementById('clear-search-btn').style.display = 'inline-block';
}

// Handle search input (Enter key)
window.handleSearchInput = function(event) {
    if (event.key === 'Enter') {
        performSearch();
    }
};

// Clear search
window.clearSearch = function() {
    document.getElementById('search-input').value = '';
    document.getElementById('clear-search-btn').style.display = 'none';
    
    // Reset to welcome page
    const content = document.getElementById('content');
    if (content) {
        content.innerHTML = `
            <h2 class="text-3xl font-bold mb-6 text-primary">Welcome</h2>
            <p class="text-gray-300">Select a season from the sidebar to view characters, or use the search above.</p>
        `;
    }

    // Clear URL params
    if (window.location.search) {
        window.history.pushState({}, '', 'index.html');
    }
};

// Initialize search on page load
document.addEventListener('DOMContentLoaded', () => {
    if (!window.location.pathname.includes('character.html')) {
        loadSearchIndexes();
    }
});

