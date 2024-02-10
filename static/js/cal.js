const locSelect = document.querySelector('#hub-select')
const viewSelect = document.querySelector('#view-select')
const calGoBtn = document.querySelector('#cal-go-btn')

document.addEventListener('DOMContentLoaded', function () {


    const calendarDiv = document.getElementById('calendar');

    let calendar = new HubCalendar(calendarDiv, {
        //Calls the HubCalendar model to create a new calendar and sets the initial parameters for the calendar display
        themeSystem: 'bootstrap5',
        initialView: 'dayGridMonth',
        dayCellDidMount: function (info) {
            let formattedDate = info.date.toISOString().split('T')[0];
            info.el.setAttribute('id', formattedDate)
        },
        initialDate: new Date(),

        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },

    });

    calendar.render();
    calendar.loadLocations()

    calGoBtn.addEventListener("click", function (e) {
        // Event listener for the "Go" button to get the value of Location and View type,
        // Clears the calendar if any existing data shows then calls the calendar instance methods that call the API and loads the data to the DOM. 
        let locId = locSelect.options[locSelect.selectedIndex].value
        let dataType = viewSelect.value

        calendar.getEventSources().forEach(source => source.remove)

        if (dataType === 'Available') {
            calendar.showCurrentAvailableAppointments(locId)
        } else if (dataType === 'Booked') {
            calendar.showCurrentBookedAppointments(locId)
        }

    })


});



