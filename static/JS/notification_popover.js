function is_or_has(object, part) {
    return object.is(part) || object.has(part).length > 0
}

function popover_on_click_trigger(event) {
    const popover_button = $('[data-toggle=popover]')
    if (
        !is_or_has($(".popover-body"), event.target) && // Not clicked inside popover
        !is_or_has(popover_button, event.target) // Not clicked on popover button
    ) {
        popover_button.popover('hide');
    }
}

function get_popover_settings() {
    return {
        html: true,
        container: 'body',
        content: $('#notification-popover__content').html(),
        template: '<div class="popover w-100" role="tooltip"><div class="arrow"></div><div class="popover-body p-0"></div></div>',
        trigger: 'click'
    }
}

function set_popover_listeners_on_shown(token) {
    $('[data-toggle=popover]').on('shown.bs.popover', function () {
        const popbody =  $('.popover-body')
        const mark_read_buttons = popbody.find('.js-notification-read');
        const all_read_button = popbody.find('a.js-all-read');

        // So that popover closes when clicking on rest of page
        $(document).click(popover_on_click_trigger);

        // Handles notification's "mark as read" (click on tick)
        mark_read_buttons.click(function (event) {
            event.preventDefault();
            const element = $(event.target).closest('a')[0];
            $.post(element.href, {'csrfmiddlewaretoken': token})
                .done(() => {
                    // Mark cell in grey
                    $(element).addClass('d-none');
                    $(element).closest('div.container').addClass('inactive');

                    // Diminish number of notification count
                    const noti = $('#noti-count');
                    noti.text(noti.text() - 1 > 0 ? noti.text() - 1 : '');

                    // Disable read all button if there are no unread notifications
                    if (noti.text() === '') all_read_button.addClass('anchor--disabled');

                    // Save HTML to outside of popover
                    $('#notification-popover__content').html($(".popover-body").html());
                });
        });

        // Listener for 'mark all as read'
        all_read_button.click(function (event) {
            event.preventDefault();
            mark_read_buttons.each((_, element) => {
                $(element).click();
            });
        });
    });
}

function set_popover_listeners_on_closed(token) {
    $('[data-toggle=popover]').on('hidden.bs.popover', function () {
        // Delete popover
        $('[data-toggle=popover]').popover('dispose');

        // Remove body listener
        $(document).off('click', popover_on_click_trigger);

        // Re-create popover with new HTML
        create_popover(token);
    });
}

function create_popover(token) {
    // Create popover
    $('[data-toggle=popover]').popover(get_popover_settings());

    // Add listeners for popover opening
    set_popover_listeners_on_shown(token);

    // Add listeners for popover closing
    set_popover_listeners_on_closed(token);


}