$(document).ready(function() {
    // Tab handling
    $('#dbTabs a').on('click', function(e) {
        e.preventDefault();
        $(this).tab('show');
    });

    // Conversation selection
    $('.conversation-item').click(function(e) {
        e.preventDefault();
        $('.conversation-item').removeClass('active');
        $(this).addClass('active');
        
        const conversationId = $(this).data('conversation-id');
        loadConversationDetails(conversationId);
    });

    // Load conversation details
    function loadConversationDetails(conversationId) {
        $('#conversation-detail').html('<div class="text-center"><div class="spinner-border" role="status"></div></div>');
        
        $.ajax({
            url: `/api/conversations/${conversationId}`,
            type: 'GET',
            success: function(data) {
                if (!data.messages || data.messages.length === 0) {
                    $('#conversation-detail').html(
                        '<div class="text-center text-muted"><p>No messages in this conversation</p></div>'
                    );
                    return;
                }
                
                let html = '';
                data.messages.forEach(function(msg) {
                    html += `
                        <div class="user-message mb-3">
                            <div class="d-flex justify-content-between">
                                <strong>User</strong>
                                <small>${new Date(msg.timestamp).toLocaleString()}</small>
                            </div>
                            <p class="mb-0">${escapeHtml(msg.user)}</p>
                        </div>
                        <div class="bot-message mb-3">
                            <div class="d-flex justify-content-between">
                                <strong>Bot</strong>
                                <small>${new Date(msg.timestamp).toLocaleString()}</small>
                            </div>
                            <p class="mb-0">${escapeHtml(msg.bot)}</p>
                        </div>
                    `;
                });
                
                $('#conversation-detail').html(html);
                
                // Scroll to the bottom of the conversation
                const detail = document.getElementById('conversation-detail');
                detail.scrollTop = detail.scrollHeight;
            },
            error: function() {
                $('#conversation-detail').html(
                    '<div class="alert alert-danger">Error loading conversation</div>'
                );
            }
        });
    }

    // Helper function to escape HTML
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/<//g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Delete conversation
    $('.delete-conversation').click(function() {
        const id = $(this).data('id');
        if (confirm('Are you sure you want to delete this conversation?')) {
            $.ajax({
                url: `/api/conversations/${id}`,
                type: 'DELETE',
                success: function() {
                    location.reload();
                },
                error: function() {
                    alert('Error deleting conversation');
                }
            });
        }
    });

    // Auto-refresh data every 30 seconds
    setInterval(function() {
        const activeConversation = $('.conversation-item.active');
        if (activeConversation.length) {
            loadConversationDetails(activeConversation.data('conversation-id'));
        }
    }, 30000);

    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();
});