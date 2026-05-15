/**
 * BANGALY-AUTOPARK-BSG - Main Logic
 */
document.addEventListener('DOMContentLoaded', function() {
    
    // 1. BSG Dynamic Width Handler
    const setWidths = () => {
        document.querySelectorAll('[data-bsg-width]').forEach(el => {
            el.style.width = el.getAttribute('data-bsg-width');
        });
    };
    setWidths();
    
    // Re-run on HTMX swap
    document.body.addEventListener('htmx:afterSwap', setWidths);

    // 2. Sidebar Toggle (Mobile)
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    
    // Add mobile toggle if needed in the future
    
    // 3. Tooltips or other global initializations
    // ...
});
