function popover_on_click_trigger(event) {
    const popover = $(".popover-body");
    if (!popover.is(event.target) && popover.has(event.target).length === 0) {
        $('[data-toggle=popover]').popover('hide');
    }

}

function get_popover_settings() {
    return {
        html: true,
        container: 'body',
        content: $('#notification_popover_content').html(),
        template: '<div class="popover w-100" role="tooltip"><div class="arrow"></div><div class="popover-body p-0"></div></div>',
        trigger: 'click'
    }
}

function set_popover_listeners_on_shown() {
    $('[data-toggle=popover]').on('shown.bs.popover', function () {
        $(document).click(popover_on_click_trigger); // So that popover closes when clicking on rest of page
        $('.mark_read_noti').click(function (event) { // Handles notification "mark as read"
            event.preventDefault();
            $.post(event.target.href, {'csrfmiddlewaretoken': $.parseHTML('{% csrf_token %}')[0].value});
            $(event.target).addClass('d-none');
            $(event.target).closest('div.container').addClass('inactive');
            $('#notification_popover_content').html($(".popover-body").html());
        });
    });
}

function set_popover_listeners_on_closed() {
    $('[data-toggle=popover]').on('hidden.bs.popover', function () {
        // Recreate popover with new HTML
        $('[data-toggle=popover]').popover('dispose').popover(get_popover_settings());

        // Remove body listener
        $(document).off('click', popover_on_click_trigger);

        // Re-add listeners
        set_popover_listeners_on_shown();
        set_popover_listeners_on_closed();
    });
}

// Create popover
$('[data-toggle=popover]').popover(get_popover_settings());

// Add listeners for popover opening
set_popover_listeners_on_shown();

// Add listeners for popover closing
set_popover_listeners_on_closed();