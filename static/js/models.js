class HubCalendar extends FullCalendar.Calendar {
    //Object model for displaying the calendar
    constructor(calendarE1, options) {
        const eventsData = options.events || []

        super(calendarE1, options);
        this.eventsData = eventsData;

    }

    async getLocations() {
        //REST API call the get locations from db. 
        const loc = await axios.get('/get_locations');
        return (loc.data.loc_data);
    };

    async loadLocations() {
        //Calls getLocations to get location list then builds html options for the locations select field. Populates locations select field.
        let loc_data = await this.getLocations()

        let html = ''
        for (let k in loc_data) {
            if (loc_data.hasOwnProperty(k)) {
                html += `<option value="${k}"> ${loc_data[k]} </option>`
            }

        }

        if (locSelect) {
            locSelect.innerHTML = html;
        }

    };

    async showCurrentAvailableAppointments(locId) {
        // REST API call to get current available appointments, sets the calendar data source to the response object returned. 
        const response = await axios.get(`/get_current_available/${locId}`);
        const appointmentData = response.data;
        this.getEventSources().forEach(source => source.remove());
        this.addEventSource(appointmentData)

    };

    async showCurrentBookedAppointments(locId) {
        //REST API call to get current booked appointments, sets the calendar data source to the response object returned. 
        const response = await axios.get(`/get_current_booked/${locId}`);
        const bookedData = response.data;
        this.getEventSources().forEach(source => source.remove());
        this.addEventSource(bookedData);
    }


    //For future implementation:
    //showCurrentAppointments(locId)

    //showCurrentBookings(locId)

    //showAllAppointments(locId)

    //showAllBookings(locId)

    //
}