"use strict";
$(document).ready(function () {
    $('#external-events .fc-event')
        .each(function () {
            $(this).data('event',
                {
                    title: $.trim($(this).text()),
                    stick: true
                });
            $(this).draggable({
                zIndex: 999,
                revert: true,
                revertDuration: 0
            });
        });
        $('#calendar').fullCalendar({
            header: {
                left: 'prev,next today',
                center: 'title',
                right: 'month,agendaWeek,agendaDay,listMonth'
            },
            defaultDate: '2024-01-04',
            navLinks: true,
            businessHours: true,
            editable: true,
            droppable: true,
        
            drop: function () {
                if ($('#checkbox2').is(':checked')) {
                    $(this).remove();
                }
            },
            events: {
                url: '/emp_get_events',
                method: 'GET',
                failure: function () {
                    alert('There was an error while fetching events!');
                },
            },
        });
});
$(document).ready(function() {
    // Event click handler
    $('.fc-h-event').on('click', function() {
        var title = $(this).find('.fc-title').text();
        // Show event title or perform other actions
        alert('Clicked event: ' + title);
    });

    // Event hover handler
    $('.fc-h-event').hover(
        function() {
            var title = $(this).find('.fc-title').text();
            // Show event details on hover
            console.log('Hovered event: ' + title);
        },
        function() {
            // Remove event details on hover out
            console.log('Hovered out');
        }
    );
});
