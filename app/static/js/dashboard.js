// Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard components
    initDashboard();
    
    // Setup sidebar toggle for mobile
    setupSidebarToggle();
    
    // Setup notifications
    setupNotifications();
});

function initDashboard() {
    // Load dashboard statistics
    loadDashboardStats();
    
    // Load recent activity
    loadRecentActivity();
}

function loadDashboardStats() {
    const userRole = document.body.dataset.userRole || '';
    let apiEndpoint = '/api/dashboard/stats';
    
    if (userRole) {
        apiEndpoint += `?role=${userRole}`;
    }
    
    fetch(apiEndpoint)
        .then(response => response.json())
        .then(data => {
            if (data.stats) {
                updateStatsDisplay(data.stats);
            }
        })
        .catch(error => {
            console.error('Error loading dashboard stats:', error);
        });
}

function updateStatsDisplay(stats) {
    // Update each stat card with the data
    const statCards = document.querySelectorAll('.stat-card');
    
    statCards.forEach(card => {
        const statKey = card.dataset.stat;
        if (stats[statKey] !== undefined) {
            const valueElement = card.querySelector('.stat-value');
            if (valueElement) {
                valueElement.textContent = stats[statKey];
            }
        }
    });
}

function loadRecentActivity() {
    fetch('/api/dashboard/activity')
        .then(response => response.json())
        .then(data => {
            if (data.activities) {
                updateActivityList(data.activities);
            }
        })
        .catch(error => {
            console.error('Error loading recent activity:', error);
        });
}

function updateActivityList(activities) {
    const activityList = document.querySelector('.activity-list');
    
    if (!activityList) return;
    
    // Clear existing items
    activityList.innerHTML = '';
    
    if (activities.length === 0) {
        activityList.innerHTML = '<li class="activity-item">No recent activity</li>';
        return;
    }
    
    // Add activity items
    activities.forEach(activity => {
        const li = document.createElement('li');
        li.className = 'activity-item';
        
        const time = document.createElement('div');
        time.className = 'time';
        time.textContent = formatActivityTime(activity.timestamp);
        
        const description = document.createElement('div');
        description.className = 'description';
        description.textContent = activity.description;
        
        li.appendChild(time);
        li.appendChild(description);
        activityList.appendChild(li);
    });
}

function formatActivityTime(timestamp) {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    
    // If today, show only time
    if (date.toDateString() === now.toDateString()) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // If this year, show date without year
    if (date.getFullYear() === now.getFullYear()) {
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' }) + ' ' + 
               date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // Otherwise show full date
    return date.toLocaleDateString() + ' ' + 
           date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function setupSidebarToggle() {
    const toggleBtn = document.querySelector('.mobile-menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (!toggleBtn || !sidebar) return;
    
    toggleBtn.addEventListener('click', function() {
        sidebar.classList.toggle('active');
    });
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        if (sidebar.classList.contains('active') && 
            !sidebar.contains(event.target) && 
            event.target !== toggleBtn) {
            sidebar.classList.remove('active');
        }
    });
}

function setupNotifications() {
    // Check for new notifications periodically
    setInterval(checkNotifications, 60000); // Check every minute
    
    // Initial check
    checkNotifications();
}

function checkNotifications() {
    fetch('/api/notifications')
        .then(response => response.json())
        .then(data => {
            if (data.notifications && data.notifications.length > 0) {
                updateNotificationBadge(data.notifications.length);
                
                // Show notification for new items
                if (data.new_notifications > 0) {
                    showNotification(`You have ${data.new_notifications} new notification(s)`, 'info');
                }
            } else {
                updateNotificationBadge(0);
            }
        })
        .catch(error => {
            console.error('Error checking notifications:', error);
        });
}

function updateNotificationBadge(count) {
    const badge = document.querySelector('.notification-badge');
    
    if (!badge) return;
    
    if (count > 0) {
        badge.textContent = count;
        badge.style.display = 'block';
    } else {
        badge.style.display = 'none';
    }
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 500);
    }, 3000);
}
