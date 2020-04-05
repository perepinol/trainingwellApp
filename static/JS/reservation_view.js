$('#save-changes').click(() => {
    let selectedSpaces = [];
    $('#modal-spaces input[type=checkbox]:checked').each( (_, space_id) => {
        selectedSpaces.push(space_id.id);
    });
    addSpaces(day, hour, selectedSpaces);
});

function addSpaces(day, hour, value) {
    let key = timeToSeconds(day, hour);
    if (value.length > 0) {
        selected[key] = value;
    } else {
        if (selected.hasOwnProperty(key)) {
            delete selected[key];
        }
    }
}

function timeToSeconds(day, hour) {
    let date = new Date(day+"T"+hour);
    return (date.getTime()/1000).toString();
}

$('#get-previous-week').click(() => {
    changeWeek(new Date(firstDaySchedule).addDays(new Date().daysDifference(firstDaySchedule)));
});

$('#get-next-week').click(() => {
    changeWeek(new Date(firstDaySchedule).addDays(firstDaySchedule.MAX_DAYS));
});

function changeSchedule() {
    let scheduleContent = "";
    for (let [day, daily] of Object.entries(json_string)) {
        scheduleContent += createDiv(['col-xl-2', 'col-lg-4', 'col-md-6', 'col-sm-12']);
            scheduleContent += createDiv(['col-12'], ['text-align: center', 'display: block', 'margin-left: 2%', 'margin-right: 2%', 'margin-top: 2%']);
                scheduleContent += "<h6>"+day+"</h6>";
            scheduleContent += "</div>\n";
            for (let [hour, spaces] of Object.entries(daily)) {
                scheduleContent += createDiv(['col-12'], ['margin: 2%']);
                if (spaces === undefined || Object.keys(spaces).length === 0) {
                    scheduleContent += createDiv(['w-100', 'rounded', 'bg-danger', 'text-white', 'cannot-reserve'], ['text-align: center', 'display: block','padding: 2px']);
                        scheduleContent+=createSpan(hour);
                    scheduleContent += "</div>\n";
                } else {
                    scheduleContent += createSuccessButton(day+" "+hour, hour);
                }
                scheduleContent += "</div>\n";
            }
        scheduleContent += "</div>\n";
    }
    let newDate = new Date(Object.keys(json_string)[0]);
    let positionAnimate = newDate > firstDaySchedule ? 200 : -200;
    let elem = $('#schedule');
    firstDaySchedule = newDate;
    elem.animate({
        left: '-='+positionAnimate,
        opacity: '0'
    }, function () {
        elem.css('left', '+='+2*positionAnimate);
        elem.html(scheduleContent);
        elem.animate({
            left: '-='+positionAnimate,
            opacity: 1,
        });
    });
    canGoPreviousWeek();
    restartListeners();
}

function createDiv(classList, styleList) {
    let classes = classList !== undefined && classList.length > 0? 'class="'+classList.join(" ")+'" ' : "";
    let styles  = styleList !== undefined && styleList.length > 0? 'style="'+styleList.join(";")+'" ' : "";
    return "<div " + classes + styles + ">\n";
}

function createSuccessButton(id, content) {
    return "<button id='"+id+"' class=\"w-100 rounded bg-success text-white can-reserve\" data-toggle=\"modal\" data-target=\"#exampleModal\" style=\"text-align: center; display: block\">\n"+createSpan(content)+"</button>\n";
}

function createSpan(content) {
    return "<span>"+content+"</span>";
}
