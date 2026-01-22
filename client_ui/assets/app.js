/**
 * OWASP API Security Lab - Shared JavaScript Utilities
 * =====================================================
 * Common helper functions for the security lab UI
 */

/**
 * Fetch wrapper with error handling
 * @param {string} url - API endpoint URL
 * @param {object} options - Fetch options
 * @returns {Promise<object>} Response data
 */
async function apiFetch(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Fetch Error:', error);
        throw error;
    }
}

/**
 * Pretty print JSON with syntax highlighting
 * @param {object} data - JSON data to display
 * @returns {string} Formatted JSON string
 */
function prettyPrintJSON(data) {
    return JSON.stringify(data, null, 2);
}

/**
 * Escape HTML to prevent XSS (client-side utility)
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format timestamp to readable string
 * @param {string} timestamp - ISO timestamp
 * @returns {string} Formatted timestamp
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

/**
 * Show notification toast (simple implementation)
 * @param {string} message - Message to display
 * @param {string} type - Type: success, error, warning, info
 */
function showNotification(message, type = 'info') {
    // Simple console notification for now
    // Can be enhanced with a toast library
    const emoji = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    
    console.log(`${emoji[type] || 'ℹ️'} ${message}`);
}

/**
 * Debounce function to limit rate of function calls
 * @param {function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>} Success status
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('Copied to clipboard!', 'success');
        return true;
    } catch (error) {
        console.error('Copy failed:', error);
        showNotification('Failed to copy', 'error');
        return false;
    }
}

/**
 * Download text as file
 * @param {string} content - File content
 * @param {string} filename - Filename
 * @param {string} mimeType - MIME type
 */
function downloadAsFile(content, filename, mimeType = 'text/plain') {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

/**
 * Check if APIs are reachable
 * @returns {Promise<object>} Health status of APIs
 */
async function checkAPIHealth() {
    const results = {
        vendor: false,
        consumer: false
    };
    
    try {
        const vendorResponse = await fetch('http://localhost:8000/health', { timeout: 2000 });
        results.vendor = vendorResponse.ok;
    } catch (error) {
        console.warn('Vendor API unreachable:', error);
    }
    
    try {
        const consumerResponse = await fetch('http://localhost:8001/health', { timeout: 2000 });
        results.consumer = consumerResponse.ok;
    } catch (error) {
        console.warn('Consumer API unreachable:', error);
    }
    
    return results;
}

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        apiFetch,
        prettyPrintJSON,
        escapeHTML,
        formatTimestamp,
        showNotification,
        debounce,
        copyToClipboard,
        downloadAsFile,
        checkAPIHealth
    };
}
