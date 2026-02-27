// Portfolio Interactions & Utilities
// Handles active nav, animations, and UI enhancements

// ============================================
// ACTIVE NAV LINK HIGHLIGHTING (URL-based)
// ============================================

/**
 * Maps URL pathnames to nav link hrefs.
 * Updates the active class on nav links based on current URL.
 */
function updateActiveNavLink() {
    const path = window.location.pathname;
    const navLinks = document.querySelectorAll('nav a.nav-link');

    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        link.classList.remove('active');

        // Exact match or root "/"
        if (href === path) {
            link.classList.add('active');
        }
        // Handle path prefixes for sub-routes (e.g., /projects/slug still highlights Projects)
        else if (href !== '/' && path.startsWith(href)) {
            link.classList.add('active');
        }
    });
}

// Run on initial page load
document.addEventListener('DOMContentLoaded', updateActiveNavLink);

// Run after every HTMX content swap
document.body.addEventListener('htmx:afterSettle', updateActiveNavLink);


// ============================================
// SCROLL ANIMATIONS
// ============================================

const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver(function (entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-fade-in');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observe all cards and sections (and re-observe after HTMX swaps)
function observeAnimationTargets() {
    document.querySelectorAll('.card, section').forEach(el => {
        observer.observe(el);
    });
}

document.addEventListener('DOMContentLoaded', observeAnimationTargets);
document.body.addEventListener('htmx:afterSettle', observeAnimationTargets);


// ============================================
// COPY TO CLIPBOARD UTILITY
// ============================================

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showToast('Failed to copy', 'error');
    });
}


// ============================================
// TOAST NOTIFICATIONS
// ============================================

function showToast(message, type = 'info') {
    // Remove any existing toasts
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type} fixed bottom-6 right-6 z-50 px-6 py-4 rounded-xl shadow-2xl animate-slide-up`;

    const colors = {
        success: 'bg-accent-green/20 border-accent-green text-accent-green',
        error: 'bg-red-500/20 border-red-500 text-red-400',
        info: 'bg-accent-cyan/20 border-accent-cyan text-accent-cyan'
    };

    toast.className += ` ${colors[type]} border-2`;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('animate-slide-down');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}


// ============================================
// LOADING INDICATOR
// ============================================

function showLoading() {
    const loader = document.createElement('div');
    loader.id = 'global-loader';
    loader.className = 'fixed inset-0 z-50 bg-dark-deep/80 backdrop-blur-sm flex items-center justify-center';
    loader.innerHTML = `
        <div class="flex flex-col items-center gap-4">
            <div class="w-16 h-16 border-4 border-accent-cyan/20 border-t-accent-cyan rounded-full animate-spin"></div>
            <p class="text-text-secondary">Loading...</p>
        </div>
    `;
    document.body.appendChild(loader);
}

function hideLoading() {
    const loader = document.getElementById('global-loader');
    if (loader) {
        loader.remove();
    }
}


// ============================================
// HTMX EVENT HANDLERS
// ============================================

// Handle HTMX errors
document.body.addEventListener('htmx:responseError', function (event) {
    hideLoading();
    showToast('Something went wrong. Please try again.', 'error');
});


// ============================================
// KEYBOARD SHORTCUTS
// ============================================

document.addEventListener('keydown', function (e) {
    // ESC to close modals
    if (e.key === 'Escape') {
        // Close chat if open
        const chatModal = document.getElementById('chat-modal');
        if (chatModal && !chatModal.classList.contains('hidden')) {
            closeChat();
        }

        // Close project modal if open
        const projectModal = document.getElementById('project-detail-modal-wrapper');
        if (projectModal && !projectModal.classList.contains('hidden')) {
            projectModal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    }

    // Ctrl/Cmd + K to open chat
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        openChat();
    }
});


// ============================================
// FORM VALIDATION HELPERS
// ============================================

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validateForm(formElement) {
    const inputs = formElement.querySelectorAll('[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('border-red-500');
            isValid = false;
        } else {
            input.classList.remove('border-red-500');
        }

        if (input.type === 'email' && !validateEmail(input.value)) {
            input.classList.add('border-red-500');
            isValid = false;
        }
    });

    return isValid;
}


// ============================================
// PERFORMANCE MONITORING
// ============================================

window.addEventListener('load', function () {
    if (window.performance) {
        const perfData = window.performance.timing;
        const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
        console.log(`Page loaded in ${pageLoadTime}ms`);
    }
});


// ============================================
// EXPORT UTILITIES
// ============================================

window.portfolioUtils = {
    copyToClipboard,
    showToast,
    showLoading,
    hideLoading,
    validateEmail,
    validateForm
};


console.log('✨ Portfolio interactions loaded successfully');