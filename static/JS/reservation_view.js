$('#save-changes').click(() => {
    let selectedSpaces = [];
    $('#modal-spaces input[type=checkbox]:checked').each( (_, space_id) => {
        selectedSpaces.push(space_id.id);
    });

    addSpaces(timeToSeconds(day, hour), selectedSpaces);

});
function addSpaces(key, value) {
    if (value.length > 0) {
        selected[key] = value;
    } else {
        if (selected.hasOwnProperty(key)) {
            delete selected[key];
        }
    }
    console.log(selected)
}

function timeToSeconds(day, hour) {
    let date = new Date(day+"T"+hour);
    return (date.getTime()/1000).toString();
}

$('#get-previous-week').click(() => {
    console.log(firstDaySchedule);
    changeWeek(new Date(firstDaySchedule).addDays(new Date().daysDifference(firstDaySchedule)));
});

$('#get-next-week').click(() => {
    changeWeek(new Date(firstDaySchedule).addDays(firstDaySchedule.MAX_DAYS));
});

function changeSchedule(schedule) {
    let scheduleContent = "";
    for (let [day, daily] of Object.entries(schedule)) {
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
    firstDaySchedule = new Date(Object.keys(schedule)[0]);
    canGoPreviousWeek();
    $('#schedule').html(scheduleContent);
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
